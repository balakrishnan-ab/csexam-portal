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

st.set_page_config(page_title="Professional Timetable", layout="wide")

# CSS: எக்செல் போன்ற கட்டங்கள் மற்றும் சுத்தமான தோற்றம்
st.markdown("""
    <style>
    /* கீழிறங்கு பட்டியலின் குறிகளை மறைக்க */
    div[data-baseweb="select"] > div {
        border: none !important;
        background-color: transparent !important;
    }
    /* தேவையற்ற சின்னங்களை மறைக்க */
    div[data-testid="stSelectbox"] svg { display: none !important; }
    
    /* கட்டங்களின் வடிவம் மாறாமல் இருக்க */
    .grid-cell {
        border: 1px solid #000;
        height: 45px;
        display: flex;
        align-items: center;
        justify-content: center;
        background-color: white;
    }
    .header-label {
        font-size: 14px; font-weight: bold; background: #E0E0E0;
        height: 45px; display: flex; align-items: center;
        justify-content: center; border: 1px solid #000;
    }
    div[data-testid="stColumn"] { padding: 0px !important; margin: 0px !important; }
    </style>
    """, unsafe_allow_html=True)

# --- ⚡ FETCH DATA ---
@st.cache_data(ttl=2)
def get_init_data():
    allot = supabase.table("staff_allotment").select("*").execute()
    time_db = supabase.table("weekly_timetable").select("*").execute()
    classes = supabase.table("classes").select("class_name").order("class_name").execute()
    return allot.data, time_db.data, [c['class_name'] for c in classes.data]

allot_data, db_list, class_list = get_init_data()

if 'working_tt' not in st.session_state:
    st.session_state.working_tt = {}

# --- 🏗️ LAYOUT ---
st.title("📅 வாராந்திர கால அட்டவணை")

main_col, side_col = st.columns([1.5, 0.5])

with main_col:
    selected_class = st.selectbox("வகுப்பைத் தேர்வு செய்க:", ["-- Select Class --"] + class_list)

if selected_class != "-- Select Class --":
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
    periods = range(1, 9)

    # தரவுகளை ஏற்றியவுடன் ஒருமுறை மட்டும் ஸ்டேட்டில் சேமிக்க
    if not st.session_state.working_tt or st.session_state.get('last_class') != selected_class:
        st.session_state.working_tt = {}
        st.session_state.last_class = selected_class
        for e in db_list:
            if e['class_name'] == selected_class:
                st.session_state.working_tt[(selected_class, e['day_of_week'], e['period_number'])] = e

    # 1. ஆசிரியர் நிலை (வலதுபுறம்)
    with side_col:
        st.markdown("##### 🏷️ ஆசிரியர் நிலை")
        class_staff = [a for a in allot_data if a['class_name'] == selected_class]
        
        available_teachers = []
        for s in class_staff:
            t_short = s['teacher_name'].split('(')[-1].replace(')', '')
            label = f"{s['subject_name']} - {t_short}"
            
            # பயன்பாட்டை எண்ணுதல்
            used = sum(1 for k, v in st.session_state.working_tt.items() 
                       if k[0] == selected_class and v['subject_name'] == s['subject_name'])
            
            rem = s['periods_per_week'] - used
            if rem > 0:
                available_teachers.append(s)
                st.success(f"{label} | மீதம்: {rem}")
            else:
                st.error(f"{label} | முடிந்தது ✅")

    # 2. அட்டவணை கிரிட் (இடதுபுறம்)
    with main_col:
        # தலைப்பு வரிசை
        h_cols = st.columns([0.8] + [1]*8)
        h_cols[0].markdown("<div class='header-label'>Day</div>", unsafe_allow_html=True)
        for p in periods: h_cols[p].markdown(f"<div class='header-label'>{p}</div>", unsafe_allow_html=True)

        for day in days:
            r_cols = st.columns([0.8] + [1]*8)
            r_cols[0].markdown(f"<div class='header-label' style='background:#f9f9f9;'>{day[:3]}</div>", unsafe_allow_html=True)
            
            for p in periods:
                key = (selected_class, day, p)
                entry = st.session_state.working_tt.get(key)
                
                with r_cols[p]:
                    # தற்போதுள்ள பாடம் அல்லது காலி இடத்தை கண்டறிதல்
                    current_val = " " # ஆரம்ப மதிப்பு
                    if entry:
                        current_val = f"{entry['subject_name']} - {entry['teacher_name'].split('(')[-1].replace(')','')}"
                    
                    # கீழிறங்கு பட்டியல் (எந்த குறியும் இல்லாமல்)
                    options = [" "] + [f"{s['subject_name']} - {s['teacher_name'].split('(')[-1].replace(')','')}" for s in available_teachers]
                    
                    # ஏற்கனவே இருக்கும் பாடம் பட்டியலில் இல்லையெனில் அதைச் சேர்க்கவும்
                    if current_val != " " and current_val not in options:
                        options.append(current_val)

                    sel = st.selectbox("", options, index=options.index(current_val), key=f"sel_{day}_{p}", label_visibility="collapsed")
                    
                    # மாற்றம் நடந்தால் மட்டும் சேமிக்க
                    if sel != current_val:
                        if sel == " ":
                            if key in st.session_state.working_tt:
                                del st.session_state.working_tt[key]
                        else:
                            sub_n, t_s = sel.split(" - ")
                            staff = next((s for s in class_staff if s['subject_name'] == sub_n), None)
                            if staff:
                                st.session_state.working_tt[key] = {
                                    "class_name": selected_class, "day_of_week": day, "period_number": p,
                                    "teacher_id": staff['teacher_id'], "teacher_name": staff['teacher_name'], "subject_name": staff['subject_name']
                                }
                        st.rerun()

    # 3. இறுதி சேமிப்பு பட்டன்
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🚀 சரிபார்த்துச் சேமி (Final Save)", type="primary", use_container_width=True):
        with st.spinner("சேமிக்கப்படுகிறது..."):
            supabase.table("weekly_timetable").delete().eq("class_name", selected_class).execute()
            data_to_save = [v for k, v in st.session_state.working_tt.items() if k[0] == selected_class]
            if data_to_save:
                supabase.table("weekly_timetable").insert(data_to_save).execute()
            st.success("வெற்றிகரமாகத் தரவுதளத்தில் சேமிக்கப்பட்டது!")
            st.cache_data.clear()
