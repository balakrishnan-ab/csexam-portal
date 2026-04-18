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

st.set_page_config(page_title="Fast Timetable", layout="wide")

# CSS: Excel போன்ற கிரிட் மற்றும் வேகம்
st.markdown("""
    <style>
    .stButton > button {
        width: 100%; height: 40px; padding: 0px; font-size: 11px;
        border: 1px solid #000; border-radius: 0px; background-color: white;
    }
    .grid-label {
        font-size: 12px; font-weight: bold; background: #E0E0E0;
        height: 40px; display: flex; align-items: center;
        justify-content: center; border: 1px solid #000;
    }
    .staff-chip {
        display: inline-block; padding: 4px 10px; margin: 4px;
        border-radius: 15px; font-size: 11px; font-weight: bold;
        border: 1px solid #999;
    }
    div[data-testid="stColumn"] { padding: 0px !important; margin: 0px !important; }
    </style>
    """, unsafe_allow_html=True)

# --- ⚡ FETCH DATA ---
@st.cache_data(ttl=60)
def get_init_data():
    allot = supabase.table("staff_allotment").select("*").execute()
    time_db = supabase.table("weekly_timetable").select("*").execute()
    classes = supabase.table("classes").select("class_name").order("class_name").execute()
    return allot.data, time_db.data, [c['class_name'] for c in classes.data]

allot_data, db_list, class_list = get_init_data()

# Session State for Speed
if 'working_tt' not in st.session_state:
    st.session_state.working_tt = {} # Key: (class, day, period)

# --- 🏗️ LAYOUT ---
st.title("📅 அதிவேக கால அட்டவணை மேலாண்மை")

main_col, side_col = st.columns([1.5, 0.5])

with main_col:
    selected_class = st.selectbox("வகுப்பைத் தேர்வு செய்க:", ["-- Select Class --"] + class_list)

if selected_class != "-- Select Class --":
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
    periods = range(1, 9)

    # 1. Load Data into State (if empty)
    if not st.session_state.working_tt:
        for e in db_list:
            st.session_state.working_tt[(e['class_name'], e['day_of_week'], e['period_number'])] = e

    # 2. Smart Teacher Filter (வலதுபுறம்)
    with side_col:
        st.markdown("##### 🏷️ ஆசிரியர் நிலை")
        class_staff = [a for a in allot_data if a['class_name'] == selected_class]
        
        # தற்போதைய எண்ணிக்கையைக் கணக்கிடுதல்
        available_teachers = []
        for s in class_staff:
            t_short = s['teacher_name'].split('(')[-1].replace(')', '')
            label = f"{s['subject_name']} - {t_short}"
            
            used = sum(1 for k, v in st.session_state.working_tt.items() 
                       if k[0] == selected_class and v['subject_name'] == s['subject_name'])
            
            rem = s['periods_per_week'] - used
            if rem > 0:
                available_teachers.append(s)
                st.markdown(f'<div class="staff-chip" style="background:#e3f2fd; border-left:5px solid blue;">{label} | மீதம்: {rem}</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="staff-chip" style="background:#eee; color:#aaa;">{label} | முடிந்தது ✅</div>', unsafe_allow_html=True)

    # 3. Fast Grid Editor (மின்னல் வேகம்)
    with main_col:
        h_cols = st.columns([0.8] + [1]*8)
        h_cols[0].markdown("<div class='grid-label'>Day</div>", unsafe_allow_html=True)
        for p in periods: h_cols[p].markdown(f"<div class='grid-label'>{p}</div>", unsafe_allow_html=True)

        for day in days:
            r_cols = st.columns([0.8] + [1]*8)
            r_cols[0].markdown(f"<div class='grid-label' style='background:#f9f9f9;'>{day[:3]}</div>", unsafe_allow_html=True)
            
            for p in periods:
                key = (selected_class, day, p)
                entry = st.session_state.working_tt.get(key)
                
                with r_cols[p]:
                    if entry:
                        # ஏற்கனவே உள்ள பாடம் - கிளிக் செய்தால் நீக்கப்படும்
                        btn_label = f"{entry['subject_name'][:3]}\n{entry['teacher_name'].split('(')[-1].replace(')','')}"
                        if st.button(btn_label, key=f"btn_{day}_{p}"):
                            del st.session_state.working_tt[key]
                            st.rerun()
                    else:
                        # காலியான இடம் - Dropdown மூலம் சேர்த்தல்
                        opts = ["+"] + [f"{s['subject_name']} - {s['teacher_name'].split('(')[-1].replace(')','')}" for s in available_teachers]
                        sel = st.selectbox("", opts, key=f"sel_{day}_{p}", label_visibility="collapsed")
                        
                        if sel != "+":
                            sub_n, t_s = sel.split(" - ")
                            staff = next(s for s in available_teachers if s['subject_name'] == sub_n)
                            st.session_state.working_tt[key] = {
                                "class_name": selected_class, "day_of_week": day, "period_number": p,
                                "teacher_id": staff['teacher_id'], "teacher_name": staff['teacher_name'], "subject_name": staff['subject_name']
                            }
                            st.rerun()

    # 4. Final Save
    if st.button("🚀 சரிபார்த்துச் சேமி (Final Save)", type="primary", use_container_width=True):
        with st.spinner("சேமிக்கப்படுகிறது..."):
            supabase.table("weekly_timetable").delete().eq("class_name", selected_class).execute()
            data_to_save = [v for k, v in st.session_state.working_tt.items() if k[0] == selected_class]
            if data_to_save:
                supabase.table("weekly_timetable").insert(data_to_save).execute()
            st.success("வெற்றிகரமாகச் சேமிக்கப்பட்டது!")
            st.cache_data.clear()

else:
    st.session_state.working_tt = {} # Reset when class changes
