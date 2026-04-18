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
    
    if st.session_state.get('active_t_id') != t_id:
        st.session_state.draft_tt = {}
        st.session_state.active_t_id = t_id
        for e in db_list:
            if e['teacher_id'] == t_id:
                st.session_state.draft_tt[(e['day_of_week'], e['period_number'])] = e['class_name']

    main_col, side_col = st.columns([0.7, 0.3])

    with main_col:
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
        periods = [str(i) for i in range(1, 9)]
        df_grid = pd.DataFrame(index=[d[:3] for d in days], columns=periods).fillna("")
        for (d, p), cls in st.session_state.draft_tt.items():
            df_grid.at[d[:3], str(p)] = cls

        flat_tt = list(st.session_state.draft_tt.values())
        available_list = [a['class_name'] for a in t_allots if a['periods_per_week'] - flat_tt.count(a['class_name']) > 0]
        final_options = sorted(list(set([""] + available_list + [str(x) for x in flat_tt if x and x != ""])))

        edited_df = st.data_editor(df_grid, column_config={p: st.column_config.SelectboxColumn(p, options=final_options, width="small") for p in periods}, use_container_width=True, num_rows="fixed")
        
        for d_short, row in edited_df.iterrows():
            day = next(d for d in days if d.startswith(d_short))
            for p in periods: st.session_state.draft_tt[(day, int(p))] = row[p]

        if st.button("🚀 அட்டவணையைச் சேமி", type="primary", use_container_width=True):
            supabase.table("weekly_timetable").delete().eq("teacher_id", t_id).execute()
            # [Save Logic - முந்தையது போலவே]
            st.success("சேமிக்கப்பட்டது!")

    # --- 4. ஒதுக்கீடு விவரம் (FN/AN) ---
    with side_col:
        st.markdown("##### 🏷️ ஒதுக்கீடு விவரம் (FN/AN)")
        for a in t_allots:
            cls = a['class_name']
            rem = a['periods_per_week'] - flat_tt.count(cls)
            fn = sum(1 for (d, p), c in st.session_state.draft_tt.items() if c == cls and int(p) <= 4)
            an = sum(1 for (d, p), c in st.session_state.draft_tt.items() if c == cls and int(p) > 4)
            color = "red" if rem < 0 else ("blue" if rem > 0 else "gray")
            st.markdown(f"**{cls}** | மீதம்: <span style='color:{color};'>{rem}</span><br><small>FN:{fn} | AN:{an}</small>", unsafe_allow_html=True)

 # --- 5. வகுப்பு வாரியான கால அட்டவணை (Horizontal Tables) ---
    st.divider()
    st.markdown("### 🏫 வகுப்பு வாரியான கால அட்டவணை")
    
    # தேவையான மாறிகளை மீண்டும் வரையறுத்தல் (எரர் வராமல் இருக்க)
    days_short = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
    periods = [str(i) for i in range(1, 9)]
    
    unique_classes = sorted(list(set([a['class_name'] for a in t_allots])))
    
    # 3 வகுப்பு அட்டவணைகளை ஒரு வரிசையில் காட்ட
    for i in range(0, len(unique_classes), 3):
        row_classes = unique_classes[i:i+3]
        cols = st.columns(3)
        
        for j, cls in enumerate(row_classes):
            with cols[j]:
                st.markdown(f"**வகுப்பு: {cls}**")
                
                # இந்த வகுப்பிற்குரிய தரவை மட்டும் எடுத்தல்
                df_cls = pd.DataFrame(index=days_short, columns=periods).fillna("-")
                for (d, p), c in st.session_state.draft_tt.items():
                    if c == cls:
                        df_cls.at[d[:3], str(p)] = "X" # அல்லது பாடத்தின் பெயர்
                
                if df_cls.values.tolist():
                    st.table(df_cls)
                else:
                    st.info("இன்னும் பாடவேளைகள் ஒதுக்கப்படவில்லை.")
