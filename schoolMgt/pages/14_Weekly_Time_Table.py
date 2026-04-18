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

# CSS: நேர்த்தியான தோற்றம்
st.markdown("""
    <style>
    .info-line { font-size: 13px; padding: 5px; border-bottom: 1px solid #eee; }
    div[data-testid="stColumn"] { padding: 0px !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. FETCH DATA ---
@st.cache_data(ttl=60)
def get_data():
    allot = supabase.table("staff_allotment").select("*").execute()
    time_db = supabase.table("weekly_timetable").select("*").execute()
    teachers = supabase.table("teachers").select("emis_id, short_name, full_name").order("full_name").execute()
    return allot.data, time_db.data, teachers.data

allot_data, db_list, teach_data = get_data()

# --- 3. UI SETUP ---
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
    
    # Session State-க்கு தரவை மாற்றல்
    if st.session_state.get('active_t_id') != t_id:
        st.session_state.draft_tt = {}
        st.session_state.active_t_id = t_id
        for e in db_list:
            if e['teacher_id'] == t_id:
                st.session_state.draft_tt[(e['day_of_week'], e['period_number'])] = e['class_name']

    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
    periods = [str(i) for i in range(1, 9)]

    # --- 4. DATA EDITOR ---
    with main_col:
        df_grid = pd.DataFrame(index=[d[:3] for d in days], columns=periods).fillna("")
        for (d, p), cls in st.session_state.draft_tt.items():
            df_grid.at[d[:3], str(p)] = cls

        # ஒதுக்கீடு விவரங்கள் & பட்டியல் உருவாக்கம்
        flat_tt = list(st.session_state.draft_tt.values())
        
        available_list = []
        for a in t_allots:
            if a['periods_per_week'] - flat_tt.count(a['class_name']) > 0:
                available_list.append(a['class_name'])
        
        existing_classes = [str(x) for x in flat_tt if x and str(x).strip() != ""]
        final_options = sorted(list(set([""] + available_list + existing_classes)))

        edited_df = st.data_editor(
            df_grid,
            column_config={p: st.column_config.SelectboxColumn(p, options=final_options, width="small") for p in periods},
            use_container_width=True, num_rows="fixed"
        )
        
        # மாற்றங்களை Session State-க்கு மாற்றுதல்
        for d_short, row in edited_df.iterrows():
            day = next(d for d in days if d.startswith(d_short))
            for p in periods:
                st.session_state.draft_tt[(day, int(p))] = row[p]

    # --- 5. ஒதுக்கீடு விவரம் (வலதுபுறம்) ---
    with side_col:
        st.markdown("##### 🏷️ ஒதுக்கீடு விவரம்")
        for a in t_allots:
            used = flat_tt.count(a['class_name'])
            rem = a['periods_per_week'] - used
            fn = sum(1 for (d, p), cls in st.session_state.draft_tt.items() if cls == a['class_name'] and int(p) <= 4)
            an = sum(1 for (d, p), cls in st.session_state.draft_tt.items() if cls == a['class_name'] and int(p) > 4)
            
            color = "red" if rem < 0 else ("gray" if rem == 0 else "blue")
            st.markdown(f"**{a['class_name']}** | <span style='color:{color};'>மீதம்: {rem}</span> <br>FN:{fn} AN:{an}", unsafe_allow_html=True)

    # --- 6. SAVE (பிழையற்ற சுத்தமான சேமிப்பு) ---
    if st.button("🚀 அட்டவணையைச் சேமி (Submit to DB)", type="primary", use_container_width=True):
        if any(list(st.session_state.draft_tt.values()).count(a['class_name']) > a['periods_per_week'] for a in t_allots):
            st.error("பிழை: ஒதுக்கீடு மீறப்பட்டுள்ளது! -ve ஒதுக்கீடுகளை நீக்கவும்.")
        else:
            supabase.table("weekly_timetable").delete().eq("teacher_id", t_id).execute()
            
            new_entries = []
            for (d, p), cls in st.session_state.draft_tt.items():
                if cls and str(cls).strip() != "" and not pd.isna(cls):
                    staff = next((a for a in t_allots if a['class_name'] == cls), None)
                    if staff:
                        new_entries.append({
                            "class_name": str(cls),
                            "day_of_week": str(d),
                            "period_number": int(p),
                            "teacher_id": int(t_id),
                            "teacher_name": str(sel_t['full_name']),
                            "subject_name": str(staff['subject_name'])
                        })
            
            if new_entries:
                try:
                    supabase.table("weekly_timetable").insert(new_entries).execute()
                    st.success("வெற்றிகரமாகச் சேமிக்கப்பட்டது!")
                    st.cache_data.clear()
                except Exception as e:
                    st.error(f"சேமிப்பில் பிழை: {e}")
            else:
                st.warning("சேமிக்க தரவுகள் இல்லை.")
