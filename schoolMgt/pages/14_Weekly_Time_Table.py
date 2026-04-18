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

# --- FETCH DATA ---
@st.cache_data(ttl=60)
def get_data():
    allot = supabase.table("staff_allotment").select("*").execute()
    time_db = supabase.table("weekly_timetable").select("*").execute()
    teachers = supabase.table("teachers").select("emis_id, short_name, full_name").order("full_name").execute()
    return allot.data, time_db.data, teachers.data

allot_data, db_list, teach_data = get_data()

# --- UI ---
st.title("👨‍🏫 ஆசிரியர் கால அட்டவணை மேலாண்மை")
if 'draft_tt' not in st.session_state: st.session_state.draft_tt = {}

main_col, side_col = st.columns([1.6, 0.4])

with main_col:
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

    # 1. இடதுபுறம் அட்டவணை
    with main_col:
        df_grid = pd.DataFrame(index=[d[:3] for d in days], columns=periods).fillna("")
        for (d, p), cls in st.session_state.draft_tt.items():
            df_grid.at[d[:3], str(p)] = cls

        # ஒதுக்கீடு மீதமுள்ள வகுப்புகள் + ஏற்கனவே அட்டவணையில் உள்ளவை
        flat_tt = list(st.session_state.draft_tt.values())
        
        # முக்கிய மாற்றம்: மீதம் > 0 உள்ளவை மட்டுமே புதிய தேர்வுக்கு வரும்
        available_list = []
        for a in t_allots:
            if a['periods_per_week'] - flat_tt.count(a['class_name']) > 0:
                available_list.append(a['class_name'])
        
        # Existing values (மறையாமல் இருக்க)
        existing_classes = list(set([c for c in flat_tt if c and c != ""]))
        final_options = sorted(list(set([""] + available_list + existing_classes)))

        edited_df = st.data_editor(
            df_grid,
            column_config={p: st.column_config.SelectboxColumn(p, options=final_options, width="small") for p in periods},
            use_container_width=True, num_rows="fixed"
        )
        
        for d_short, row in edited_df.iterrows():
            day = next(d for d in days if d.startswith(d_short))
            for p in periods:
                st.session_state.draft_tt[(day, int(p))] = row[p]

    # 2. வலதுபுறம் (ஒதுக்கீடு நிலை)
    with side_col:
        st.markdown("##### 🏷️ ஒதுக்கீடு விவரம்")
        for a in t_allots:
            used = flat_tt.count(a['class_name'])
            rem = a['periods_per_week'] - used
            # FN/AN கணக்கீடு
            fn = sum(1 for (d, p), cls in st.session_state.draft_tt.items() if cls == a['class_name'] and int(p) <= 4)
            an = sum(1 for (d, p), cls in st.session_state.draft_tt.items() if cls == a['class_name'] and int(p) > 4)
            
            # வண்ணம்: -ve சென்றால் சிவப்பு, 0 என்றால் கருப்பு/சாம்பல்
            color = "red" if rem < 0 else ("gray" if rem == 0 else "blue")
            st.markdown(f"**{a['class_name']}** | <span style='color:{color};'>மீதம்: {rem}</span> <br>FN:{fn} AN:{an}", unsafe_allow_html=True)

    # 3. சேமிப்பு
    if st.button("🚀 அட்டவணையைச் சேமி", type="primary", use_container_width=True):
        # சேமிக்கும் முன் -ve சரிபார்ப்பு
        if any(list(st.session_state.draft_tt.values()).count(a['class_name']) > a['periods_per_week'] for a in t_allots):
            st.error("பிழை: ஒதுக்கீடு மீறப்பட்டுள்ளது! -ve ஒதுக்கீடுகளை நீக்கவும்.")
        else:
            supabase.table("weekly_timetable").delete().eq("teacher_id", t_id).execute()
            new_entries = [{"class_name": cls, "day_of_week": d, "period_number": p, "teacher_id": t_id, 
                           "teacher_name": sel_t['full_name'], "subject_name": next((a['subject_name'] for a in t_allots if a['class_name'] == cls), "")}
                          for (d, p), cls in st.session_state.draft_tt.items() if cls and cls != ""]
            if new_entries: supabase.table("weekly_timetable").insert(new_entries).execute()
            st.success("வெற்றிகரமாகச் சேமிக்கப்பட்டது!")
