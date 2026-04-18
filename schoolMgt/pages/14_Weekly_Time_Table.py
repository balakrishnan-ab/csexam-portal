import streamlit as st
import pandas as pd
from supabase import create_client, Client

# --- 1. SUPABASE CONNECTION ---
try:
    url, key = st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(url, key)
except:
    st.error("Connection Error!")
    st.stop()

st.set_page_config(page_title="Teacher Timetable Editor", layout="wide")

# --- 2. FETCH DATA ---
@st.cache_data(ttl=60)
def get_data():
    allot = supabase.table("staff_allotment").select("*").execute()
    time_db = supabase.table("weekly_timetable").select("*").execute()
    teachers = supabase.table("teachers").select("emis_id, short_name, full_name").order("full_name").execute()
    return allot.data, time_db.data, teachers.data

allot_data, db_list, teach_data = get_data()

st.title("👨‍🏫 ஆசிரியர் கால அட்டவணை மேலாண்மை")
if 'draft_tt' not in st.session_state: st.session_state.draft_tt = {}

# --- 3. TEACHER SELECTION ---
t_opts = {f"{t['full_name']} ({t['short_name']})": t for t in teach_data}
sel_t_label = st.selectbox("ஆசிரியரைத் தேர்வு செய்க:", ["-- Select Teacher --"] + list(t_opts.keys()))

if sel_t_label != "-- Select Teacher --":
    sel_t = t_opts[sel_t_label]
    t_id = sel_t['emis_id']
    t_allots = [a for a in allot_data if a['teacher_id'] == t_id]
    
    # Session State Setup
    if st.session_state.get('active_t_id') != t_id:
        st.session_state.draft_tt = {}
        st.session_state.active_t_id = t_id
        for e in db_list:
            if e['teacher_id'] == t_id:
                st.session_state.draft_tt[(e['day_of_week'], e['period_number'])] = e['class_name']

    # Layout: இடது பக்கம் Editor, வலது பக்கம் ஒதுக்கீடு விவரம்
    main_col, side_col = st.columns([0.7, 0.3])

    with main_col:
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
        periods = [str(i) for i in range(1, 9)]
        df_grid = pd.DataFrame(index=[d[:3] for d in days], columns=periods).fillna("")
        for (d, p), cls in st.session_state.draft_tt.items():
            df_grid.at[d[:3], str(p)] = cls

        flat_tt = list(st.session_state.draft_tt.values())
        available_list = [a['class_name'] for a in t_allots if a['periods_per_week'] - flat_tt.count(a['class_name']) > 0]
        final_options = sorted(list(set([""] + available_list + [str(x) for x in flat_tt if x])))

        edited_df = st.data_editor(df_grid, column_config={p: st.column_config.SelectboxColumn(p, options=final_options, width="small") for p in periods}, use_container_width=True, num_rows="fixed")
        
        for d_short, row in edited_df.iterrows():
            day = next(d for d in days if d.startswith(d_short))
            for p in periods: st.session_state.draft_tt[(day, int(p))] = row[p]

        # SAVE BUTTON
        if st.button("🚀 அட்டவணையைச் சேமி", type="primary", use_container_width=True):
            supabase.table("weekly_timetable").delete().eq("teacher_id", t_id).execute()
            # ... (Save Logic - முந்தையது போலவே) ...
            st.success("வெற்றிகரமாகச் சேமிக்கப்பட்டது!")

    with side_col:
        st.markdown("##### 🏷️ ஒதுக்கீடு விவரம்")
        for a in t_allots:
            used = flat_tt.count(a['class_name'])
            rem = a['periods_per_week'] - used
            st.markdown(f"**{a['class_name']}** | மீதம்: <span style='color:red;'>{rem}</span>", unsafe_allow_html=True)

    # --- 4. வகுப்பு கால அட்டவணைகள் (3 per Row) ---
    st.divider()
    st.markdown("### 🏫 வகுப்பு வாரியான கால அட்டவணை")
    
    unique_classes = sorted(list(set([a['class_name'] for a in t_allots])))
    rows = [unique_classes[i:i+3] for i in range(0, len(unique_classes), 3)]
    
    for row in rows:
        cols = st.columns(3)
        for i, cls in enumerate(row):
            with cols[i]:
                st.subheader(f"வகுப்பு: {cls}")
                # அந்த வகுப்புக்கு மட்டும் தரவை எடுத்தல்
                class_data = [(d, p, c) for (d, p), c in st.session_state.draft_tt.items() if c == cls]
                # எளிய அட்டவணை வடிவம்
                st.write(f"ஒதுக்கப்பட்ட பாடவேளைகள்: {len(class_data)}")
