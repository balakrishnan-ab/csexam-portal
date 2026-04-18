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

# CSS: கச்சிதமான அட்டவணை
st.markdown("""
    <style>
    .grid-label { font-size: 13px; font-weight: bold; background: #eee; height: 45px; display: flex; align-items: center; justify-content: center; border: 1px solid #000; }
    .stButton > button { width: 100%; height: 45px; border-radius: 0px; border: 1px solid #000; background: white; font-size: 11px; }
    div[data-testid="stColumn"] { padding: 0px !important; margin: 0px !important; }
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

# Session State for Local Edits
if 'teacher_tt' not in st.session_state:
    st.session_state.teacher_tt = {}

# --- 🏗️ LAYOUT ---
st.title("👨‍🏫 ஆசிரியர் வாரியாக அட்டவணை நிரப்புதல்")

# 1. ஆசிரியர் தேர்வு
t_opts = {f"{t['full_name']} ({t['short_name']})": t for t in teach_list}
sel_teacher_label = st.selectbox("ஆசிரியரைத் தேர்வு செய்க:", ["-- Select Teacher --"] + list(t_opts.keys()))

if sel_teacher_label != "-- Select Teacher --":
    sel_t = t_opts[sel_teacher_label]
    t_id = sel_t['emis_id']
    
    # ஆசிரியருக்கு ஒதுக்கப்பட்ட வகுப்புகள்
    t_allots = [a for a in allot_data if a['teacher_id'] == t_id]
    all_classes = sorted(list(set([a['class_name'] for a in t_allots])))

    # தரவுகளை ஏற்றியவுடன் ஸ்டேட்டில் சேமிக்க (அந்த ஆசிரியருக்கு மட்டும்)
    if st.session_state.get('last_t_id') != t_id:
        st.session_state.teacher_tt = {}
        st.session_state.last_t_id = t_id
        for e in db_list:
            if e['teacher_id'] == t_id:
                key = (e['day_of_week'], e['period_number'])
                if key not in st.session_state.teacher_tt:
                    st.session_state.teacher_tt[key] = []
                st.session_state.teacher_tt[key].append(e['class_name'])

    # 2. அட்டவணை கிரிட்
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
    periods = range(1, 9)

    st.info(f"குறிப்பு: {sel_t['short_name']} அவர்களுக்குரிய பாடவேளைகளைக் கிளிக் செய்து, வகுப்புகளைத் தேர்வு செய்யவும் (Combine வகுப்புகளுக்கு ஒன்றுக்கும் மேற்பட்ட வகுப்புகளைத் தேர்வு செய்யலாம்).")

    # Header
    h_cols = st.columns([0.8] + [1]*8)
    h_cols[0].markdown("<div class='grid-label'>Day</div>", unsafe_allow_html=True)
    for p in periods: h_cols[p].markdown(f"<div class='grid-label'>{p}</div>", unsafe_allow_html=True)

    for day in days:
        r_cols = st.columns([0.8] + [1]*8)
        r_cols[0].markdown(f"<div class='grid-label' style='background:#f9f9f9;'>{day[:3]}</div>", unsafe_allow_html=True)
        
        for p in periods:
            key = (day, p)
            current_classes = st.session_state.teacher_tt.get(key, [])
            btn_text = ", ".join(current_classes) if current_classes else "---"
            
            with r_cols[p]:
                # பாப்-அப் போன்று செயல்பட செலக்ட் பாக்ஸ்
                sel = st.multiselect(f"{day}_{p}", all_classes, default=current_classes, key=f"ms_{day}_{p}", label_visibility="collapsed")
                
                # மாற்றம் நடந்தால் ஸ்டேட்டில் அப்டேட்
                if set(sel) != set(current_classes):
                    st.session_state.teacher_tt[key] = sel
                    st.rerun()

    # 3. 🚀 SAVE BUTTON
    st.divider()
    if st.button(f"🚀 {sel_t['short_name']} அட்டவணையைச் சேமி", type="primary", use_container_width=True):
        with st.spinner("சேமிக்கப்படுகிறது..."):
            # இந்த ஆசிரியரின் பழைய பதிவுகளை மட்டும் நீக்குதல்
            supabase.table("weekly_timetable").delete().eq("teacher_id", t_id).execute()
            
            new_entries = []
            for (day, p_num), classes in st.session_state.teacher_tt.items():
                for cls in classes:
                    # அந்த வகுப்பிற்கான பாடத்தைக் கண்டறிதல்
                    staff_info = next((a for a in t_allots if a['class_name'] == cls), None)
                    if staff_info:
                        new_entries.append({
                            "class_name": cls,
                            "day_of_week": day,
                            "period_number": p_num,
                            "teacher_id": t_id,
                            "teacher_name": sel_t['full_name'] + f" ({sel_t['short_name']})",
                            "subject_name": staff_info['subject_name']
                        })
            
            if new_entries:
                supabase.table("weekly_timetable").insert(new_entries).execute()
            
            st.success("வெற்றிகரமாகச் சேமிக்கப்பட்டது!")
            st.cache_data.clear()

else:
    st.warning("தொடங்குவதற்கு ஆசிரியரைத் தேர்வு செய்யவும்.")
