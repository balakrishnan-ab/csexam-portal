import streamlit as st
import pandas as pd
from supabase import create_client, Client

# --- SUPABASE CONNECTION ---
try:
    url, key = st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(url, key)
except:
    st.error("Connection Error!")
    st.stop()

st.set_page_config(page_title="Teacher Timetable Editor", layout="wide")

# --- FETCH DATA ---
@st.cache_data(ttl=60)
def get_data():
    allot = supabase.table("staff_allotment").select("*").execute()
    time_db = supabase.table("weekly_timetable").select("*").execute()
    teachers = supabase.table("teachers").select("emis_id, short_name, full_name").order("full_name").execute()
    return allot.data, time_db.data, teachers.data

allot_data, db_list, teach_data = get_data()

st.title("👨‍🏫 ஆசிரியர் கால அட்டவணை மேலாண்மை")

main_col, side_col = st.columns([1.6, 0.4])

with main_col:
    t_opts = {f"{t['full_name']} ({t['short_name']})": t for t in teach_data}
    sel_t_label = st.selectbox("ஆசிரியரைத் தேர்வு செய்க:", ["-- Select Teacher --"] + list(t_opts.keys()))

if sel_t_label != "-- Select Teacher --":
    sel_t = t_opts[sel_t_label]
    t_id = sel_t['emis_id']
    t_allots = [a for a in allot_data if a['teacher_id'] == t_id]
    
    # Session State
    if st.session_state.get('active_t_id') != t_id:
        st.session_state.draft_tt = {}
        st.session_state.active_t_id = t_id
        for e in db_list:
            if e['teacher_id'] == t_id:
                st.session_state.draft_tt[(e['day_of_week'], e['period_number'])] = e['class_name']

    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
    periods = [str(i) for i in range(1, 9)]

    # --- 1. DATA EDITOR (மேல் பகுதி) ---
    df_grid = pd.DataFrame(index=[d[:3] for d in days], columns=periods).fillna("")
    for (d, p), cls in st.session_state.draft_tt.items():
        df_grid.at[d[:3], str(p)] = cls

    flat_tt = list(st.session_state.draft_tt.values())
    available_list = [a['class_name'] for a in t_allots if a['periods_per_week'] - flat_tt.count(a['class_name']) > 0]
    final_options = sorted(list(set([""] + available_list + [str(x) for x in flat_tt if x and x != ""])))

    edited_df = st.data_editor(
        df_grid,
        column_config={p: st.column_config.SelectboxColumn(p, options=final_options, width="small") for p in periods},
        use_container_width=True, num_rows="fixed"
    )
    
    for d_short, row in edited_df.iterrows():
        day = next(d for d in days if d.startswith(d_short))
        for p in periods:
            st.session_state.draft_tt[(day, int(p))] = row[p]

    # --- 2. கீழ் பகுதியில் வகுப்பு வாரியான அட்டவணை (படம் போன்ற அமைப்பு) ---
    st.markdown("---")
    st.markdown("##### 📅 ஆசிரியர் செல்லும் வகுப்புகளின் அட்டவணை")
    
    # ஆசிரியர் எடுக்கும் ஒவ்வொரு வகுப்புக்கும் ஒரு அட்டவணை
    for cls_name in sorted(list(set([a['class_name'] for a in t_allots]))):
        st.subheader(f"வகுப்பு: {cls_name}")
        cls_tt = pd.DataFrame(index=[d[:3] for d in days], columns=periods).fillna("-")
        
        # அந்த வகுப்பின் மொத்த நேர அட்டவணையில் இருந்து அந்த ஆசிரியரின் பாடம் மட்டும்
        for e in db_list:
            if e['class_name'] == cls_name and e['teacher_id'] == t_id:
                cls_tt.at[e['day_of_week'][:3], str(e['period_number'])] = e['subject_name']
        
        st.table(cls_tt)

    # --- 3. SAVE ---
    if st.button("🚀 அட்டவணையைச் சேமி"):
        # (சேமிக்கும் பழைய லாஜிக்...)
        supabase.table("weekly_timetable").delete().eq("teacher_id", t_id).execute()
        new_entries = [{"class_name": cls, "day_of_week": d, "period_number": p, "teacher_id": t_id, 
                       "teacher_name": sel_t['full_name'], "subject_name": next((a['subject_name'] for a in t_allots if a['class_name'] == cls), "")}
                      for (d, p), cls in st.session_state.draft_tt.items() if cls and cls != ""]
        if new_entries: supabase.table("weekly_timetable").insert(new_entries).execute()
        st.success("வெற்றிகரமாகச் சேமிக்கப்பட்டது!")
        st.rerun()
