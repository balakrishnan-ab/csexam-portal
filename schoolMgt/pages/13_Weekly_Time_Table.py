import streamlit as st
import pandas as pd
import hashlib
from supabase import create_client, Client

# --- 1. SUPABASE CONNECTION ---
try:
    url, key = st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(url, key)
except:
    st.error("Connection Error!")
    st.stop()

st.set_page_config(page_title="Fast Master Timetable", layout="wide")

# CSS: கச்சிதமான மற்றும் வேகமான கிரிட்
st.markdown("""
    <style>
    .stButton > button {
        width: 100%; height: 42px; padding: 2px; font-size: 11px;
        border: 1px solid #000; border-radius: 0px; background: white;
    }
    .grid-header {
        font-size: 13px; font-weight: bold; background: #E0E0E0;
        height: 40px; display: flex; align-items: center;
        justify-content: center; border: 1px solid #000;
    }
    .active-card {
        border: 3px solid #ff4b4b !important;
        background-color: #fff0f0 !important;
        box-shadow: 0px 0px 10px rgba(255, 75, 75, 0.3);
    }
    div[data-testid="stColumn"] { padding: 0.5px !important; margin: 0px !important; }
    </style>
    """, unsafe_allow_html=True)

# --- ⚡ FETCH DATA ---
@st.cache_data(ttl=2)
def get_init_data():
    allot = supabase.table("staff_allotment").select("*").execute()
    time_db = supabase.table("weekly_timetable").select("*").execute()
    teachers = supabase.table("teachers").select("emis_id, full_name, short_name").order("full_name").execute()
    return allot.data, time_db.data, teachers.data

allot_data, db_list, teach_list = get_init_data()

# Session State மேலாண்மை (வேகத்திற்காக)
if 'temp_tt' not in st.session_state: st.session_state.temp_tt = {}
if 'active_cls' not in st.session_state: st.session_state.active_cls = []

# --- 🏗️ LAYOUT ---
st.title("👨‍🏫 அதிவேக கால அட்டவணை மேலாண்மை")

main_col, side_col = st.columns([1.5, 0.5])

with main_col:
    t_opts = {f"{t['full_name']} ({t['short_name']})": t for t in teach_list}
    sel_teacher_label = st.selectbox("ஆசிரியரைத் தேர்வு செய்க:", ["-- Select --"] + list(t_opts.keys()))

if sel_teacher_label != "-- Select --":
    sel_t = t_opts[sel_teacher_label]
    t_id = sel_t['emis_id']
    t_allots = [a for a in allot_data if a['teacher_id'] == t_id]

    # 1. தரவுகளை Session State-க்கு ஏற்றுதல்
    if st.session_state.get('current_tid') != t_id:
        st.session_state.temp_tt = {}
        st.session_state.current_tid = t_id
        for e in db_list:
            if e['teacher_id'] == t_id:
                key = (e['day_of_week'], e['period_number'])
                if key not in st.session_state.temp_tt: st.session_state.temp_tt[key] = []
                st.session_state.temp_tt[key].append(e['class_name'])

    # 2. வலதுபுறம் ஒதுக்கீடு மற்றும் மீதமுள்ள எண்ணிக்கை (Live Counting)
    with side_col:
        st.markdown("##### 📝 ஒதுக்கீடு & மீதி")
        selected_for_grid = [] # தற்போது கிரிட்டில் தேர்வு செய்யப்பட்டுள்ள வகுப்பு
        
        for a in t_allots:
            # திரையில் (Session State) எத்தனை முறை உள்ளது என எண்ணுதல்
            used = sum(1 for classes in st.session_state.temp_tt.values() if a['class_name'] in classes)
            rem = a['periods_per_week'] - used
            
            is_active = a['class_name'] in st.session_state.active_cls
            border_css = "active-card" if is_active else ""
            
            # வகுப்பு கார்டு
            st.markdown(f"""
                <div class='{border_css}' style='border:1px solid #ccc; padding:10px; border-radius:8px; margin-bottom:5px; background:white;'>
                    <b style='font-size:15px;'>{a['class_name']}</b><br>
                    <small>{a['subject_name']}</small><br>
                    <span style='color:{"blue" if rem > 0 else "gray"}; font-weight:bold;'>மீதம்: {rem}</span>
                </div>
            """, unsafe_allow_html=True)
            
            if rem > 0 or is_active:
                if st.button(f"தேர்வு {a['class_name']}", key=f"sel_cls_{a['id']}"):
                    if a['class_name'] in st.session_state.active_cls:
                        st.session_state.active_cls.remove(a['class_name'])
                    else:
                        st.session_state.active_cls.append(a['class_name'])
                    st.rerun()

    # 3. கால அட்டவணை கிரிட் (இடதுபுறம்)
    with main_col:
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
        periods = range(1, 9)

        # Header
        h_cols = st.columns([0.8] + [1]*8)
        h_cols[0].markdown("<div class='grid-header'>Day</div>", unsafe_allow_html=True)
        for p in periods: h_cols[p].markdown(f"<div class='grid-header'>{p}</div>", unsafe_allow_html=True)

        for day in days:
            r_cols = st.columns([0.8] + [1]*8)
            r_cols[0].markdown(f"<div class='grid-header' style='background:#f9f9f9;'>{day[:3]}</div>", unsafe_allow_html=True)
            
            for p in periods:
                key = (day, p)
                current_classes = st.session_state.temp_tt.get(key, [])
                
                with r_cols[p]:
                    # பட்டன் லேபிள்
                    btn_label = "\n".join(current_classes) if current_classes else " "
                    
                    if st.button(btn_label, key=f"grid_{day}_{p}"):
                        # 🎯 மேஜிக் கிளிக்: 
                        # 1. ஏற்கனவே அந்த வகுப்புகள் இருந்தால் நீக்கும்.
                        # 2. வலதுபுறம் தேர்வு செய்த வகுப்புகளை இங்கே ஒட்டும்.
                        if st.session_state.active_cls:
                            st.session_state.temp_tt[key] = list(st.session_state.active_cls)
                        else:
                            st.session_state.temp_tt[key] = []
                        st.rerun()

        st.divider()
        if st.button(f"🚀 {sel_t['short_name']} அட்டவணையை மொத்தமாகச் சேமி", type="primary", use_container_width=True):
            with st.spinner("சேமிக்கப்படுகிறது..."):
                supabase.table("weekly_timetable").delete().eq("teacher_id", t_id).execute()
                new_entries = []
                for (d, pn), classes in st.session_state.temp_tt.items():
                    for cls in classes:
                        staff_info = next((a for a in t_allots if a['class_name'] == cls), None)
                        if staff_info:
                            new_entries.append({
                                "class_name": cls, "day_of_week": d, "period_number": pn,
                                "teacher_id": t_id, "teacher_name": f"{sel_t['full_name']} ({sel_t['short_name']})",
                                "subject_name": staff_info['subject_name']
                            })
                if new_entries:
                    supabase.table("weekly_timetable").insert(new_entries).execute()
                st.success("வெற்றிகரமாகத் தரவுதளத்தில் சேமிக்கப்பட்டது!")
                st.cache_data.clear()
