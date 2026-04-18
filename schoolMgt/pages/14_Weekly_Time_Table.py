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

@st.cache_data(ttl=10)
def get_data():
    allot = supabase.table("staff_allotment").select("*").execute()
    time_db = supabase.table("weekly_timetable").select("*").execute()
    teachers = supabase.table("teachers").select("emis_id, short_name, full_name").order("full_name").execute()
    return allot.data, time_db.data, teachers.data

allot_data, db_list, teach_data = get_data()

st.title("👨‍🏫 ஆசிரியர் கால அட்டவணை மேலாண்மை")
if 'draft_tt' not in st.session_state: st.session_state.draft_tt = {}

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

    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
    periods = [str(i) for i in range(1, 9)]

    # Layout: இடது பக்கம் Editor, வலது பக்கம் ஒதுக்கீடு விவரம்
    main_col, side_col = st.columns([0.7, 0.3])

    with main_col:
        df_grid = pd.DataFrame(index=[d[:3] for d in days], columns=periods).fillna("")
        for (d, p), cls in st.session_state.draft_tt.items():
            df_grid.at[d[:3], str(p)] = cls

        edited_df = st.data_editor(df_grid, column_config={p: st.column_config.SelectboxColumn(p, options=sorted(list(set([""] + [a['class_name'] for a in t_allots] + [str(x) for x in st.session_state.draft_tt.values() if x]))), width="small") for p in periods}, use_container_width=True, num_rows="fixed")
        
        for d_short, row in edited_df.iterrows():
            day = next(d for d in days if d.startswith(d_short))
            for p in periods: st.session_state.draft_tt[(day, int(p))] = row[p]

        if st.button("🚀 அட்டவணையைச் சேமி"):
            supabase.table("weekly_timetable").delete().eq("teacher_id", t_id).execute()
            new_entries = [{"class_name": cls, "day_of_week": d, "period_number": p, "teacher_id": t_id, 
                           "teacher_name": sel_t['full_name'], "subject_name": next((a['subject_name'] for a in t_allots if a['class_name'] == cls), "")}
                          for (d, p), cls in st.session_state.draft_tt.items() if cls and cls != ""]
            if new_entries: supabase.table("weekly_timetable").insert(new_entries).execute()
            st.success("சேமிக்கப்பட்டது!")
            st.rerun()

    # ஒதுக்கீடு விவரம் (வலதுபுறம் மீண்டும் இணைக்கப்பட்டது)
    with side_col:
        st.markdown("##### 🏷️ ஒதுக்கீடு விவரம் (FN/AN)")
        for a in t_allots:
            cls = a['class_name']
            flat_vals = list(st.session_state.draft_tt.values())
            rem = a['periods_per_week'] - flat_vals.count(cls)
            fn = sum(1 for (d, p), c in st.session_state.draft_tt.items() if c == cls and int(p) <= 4)
            an = sum(1 for (d, p), c in st.session_state.draft_tt.items() if c == cls and int(p) > 4)
            st.markdown(f"**{cls}** | மீதம்: {rem}<br><small>FN:{fn} | AN:{an}</small>", unsafe_allow_html=True)

    # வகுப்பு வாரியான அட்டவணை (கீழே)
    st.divider()
    st.markdown("### 🏫 வகுப்பு வாரியான கால அட்டவணை")
    unique_classes = sorted(list(set([a['class_name'] for a in allot_data])))
    db_list_new = supabase.table("weekly_timetable").select("*").execute().data

    for i in range(0, len(unique_classes), 3):
        cols = st.columns(3)
        for j, cls in enumerate(unique_classes[i:i+3]):
            with cols[j]:
                st.markdown(f"**வகுப்பு: {cls}**")
                df_cls = pd.DataFrame(index=[d[:3] for d in days], columns=periods).fillna("-")
                for entry in db_list_new:
                    classes = [c.strip() for c in str(entry['class_name']).split("&")]
                    if cls in classes:
                        df_cls.at[entry['day_of_week'][:3], str(entry['period_number'])] = f"{entry['subject_name'][:3]}-{entry['teacher_name'].split('(')[-1].replace(')', '')[:2]}"
                st.table(df_cls)
