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

st.set_page_config(page_title="Fast Timetable Editor", layout="wide")

# --- ⚡ FETCH DATA ---
@st.cache_data(ttl=60)
def get_data():
    allot = supabase.table("staff_allotment").select("*").execute()
    time_db = supabase.table("weekly_timetable").select("*").execute()
    teachers = supabase.table("teachers").select("emis_id, short_name, full_name").order("full_name").execute()
    return allot.data, time_db.data, teachers.data

allot_data, db_list, teach_data = get_data()

# --- 🏗️ LAYOUT & STATE ---
st.title("👨‍🏫 ஆசிரியர் கால அட்டவணை மேலாண்மை")

# Session State for Draft
if 'draft_tt' not in st.session_state:
    st.session_state.draft_tt = {}

main_col, side_col = st.columns([1.6, 0.4])

with main_col:
    t_opts = {f"{t['full_name']} ({t['short_name']})": t for t in teach_data}
    sel_t_label = st.selectbox("ஆசிரியரைத் தேர்வு செய்க:", ["-- Select Teacher --"] + list(t_opts.keys()))

if sel_t_label != "-- Select Teacher --":
    sel_t = t_opts[sel_t_label]
    t_id = sel_t['emis_id']
    t_allots = [a for a in allot_data if a['teacher_id'] == t_id]
    
    # தரவை Session State-க்கு மாற்றல் (ஒருமுறை மட்டும்)
    if st.session_state.get('active_t_id') != t_id:
        st.session_state.draft_tt = {}
        st.session_state.active_t_id = t_id
        for e in db_list:
            if e['teacher_id'] == t_id:
                st.session_state.draft_tt[(e['day_of_week'], e['period_number'])] = e['class_name']

    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
    periods = [str(i) for i in range(1, 9)]

    # 1. வலதுபுறம் (ஒதுக்கீடு நிலை)
    with side_col:
        st.markdown("##### 🏷️ ஒதுக்கீடு விவரம்")
        current_tt = st.session_state.draft_tt
        for a in t_allots:
            used = list(current_tt.values()).count(a['class_name'])
            rem = a['periods_per_week'] - used
            # FN (1-4), AN (5-8) கணக்கீடு
            fn = sum(1 for (d, p), cls in current_tt.items() if cls == a['class_name'] and int(p) <= 4)
            an = sum(1 for (d, p), cls in current_tt.items() if cls == a['class_name'] and int(p) > 4)
            st.markdown(f"**{a['class_name']}** | {a['subject_name']} <br>மீதம்: {rem} | FN:{fn} AN:{an}", unsafe_allow_html=True)

    # 2. அட்டவணை கிரிட்
    with main_col:
        df_grid = pd.DataFrame(index=[d[:3] for d in days], columns=periods).fillna("")
        for (d, p), cls in current_tt.items():
            df_grid.at[d[:3], str(p)] = cls

        # ஒதுக்கீடு மீதமுள்ள வகுப்புகளை மட்டும் பட்டியலிடுதல்
        available = [""] + [a['class_name'] for a in t_allots if list(current_tt.values()).count(a['class_name']) < a['periods_per_week']]

        edited_df = st.data_editor(
            df_grid,
            column_config={p: st.column_config.SelectboxColumn(p, options=available + list(set(current_tt.values())), width="small") for p in periods},
            use_container_width=True, num_rows="fixed"
        )
        
        # மாற்றங்களை Session State-ல் சேமித்தல்
        for d_short, row in edited_df.iterrows():
            day = next(d for d in days if d.startswith(d_short))
            for p in periods:
                st.session_state.draft_tt[(day, int(p))] = row[p]

        # 3. 🚀 மொத்தமாகச் சேமிக்க
        if st.button("🚀 அட்டவணையைச் சேமி (Submit to DB)", type="primary", use_container_width=True):
            with st.spinner("சேமிக்கப்படுகிறது..."):
                supabase.table("weekly_timetable").delete().eq("teacher_id", t_id).execute()
                new_entries = []
                for (day, p_num), cls_name in st.session_state.draft_tt.items():
                    if cls_name and cls_name != "":
                        staff = next((a for a in t_allots if a['class_name'] == cls_name), None)
                        if staff:
                            new_entries.append({"class_name": cls_name, "day_of_week": day, "period_number": p_num,
                                              "teacher_id": t_id, "teacher_name": sel_t['full_name'], "subject_name": staff['subject_name']})
                if new_entries: supabase.table("weekly_timetable").insert(new_entries).execute()
                st.success("வெற்றிகரமாகச் சேமிக்கப்பட்டது!")
                st.cache_data.clear()
