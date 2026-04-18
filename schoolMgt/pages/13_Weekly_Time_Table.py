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

st.set_page_config(page_title="Master Timetable Grid", layout="wide")

# Excel போன்ற கிரிட் மற்றும் கார்டுகளுக்கான CSS
st.markdown("""
    <style>
    /* Excel Table Grid Styling */
    .stButton > button {
        width: 100%; height: 35px; padding: 0px; font-size: 11px;
        border-radius: 0px; border: 1px solid #000 !important;
        line-height: 1.1; font-weight: bold; background-color: white;
    }
    /* Day & Period Labels */
    .grid-label {
        font-size: 11px; font-weight: bold; background: #E0E0E0;
        height: 35px; display: flex; align-items: center;
        justify-content: center; border: 1px solid #000;
    }
    /* Selection Card Decoration */
    .card-container {
        border-radius: 8px; padding: 10px; text-align: center;
        box-shadow: 2px 2px 8px rgba(0,0,0,0.1); margin-bottom: 10px;
    }
    div[data-testid="stColumn"] { padding: 1px !important; margin: 0px !important; }
    </style>
    """, unsafe_allow_html=True)

def get_short_sub(sub_name):
    sub_map = {"Computer Science": "CS", "Computer Applications": "CA", "Commerce": "COM",
               "Accountancy": "ACC", "Economics": "ECO", "Mathematics": "MAT",
               "Social Science": "S.Sci", "Physics": "PHY", "Chemistry": "CHE",
               "Biology": "BIO", "Tamil": "TAM", "English": "ENG"}
    return sub_map.get(sub_name, sub_name[:3].upper())

def get_color(text):
    if not text: return "#ffffff"
    hash_obj = hashlib.md5(text.encode()).hexdigest()
    r = (int(hash_obj[:2],16)%40)+210
    g = (int(hash_obj[2:4],16)%40)+210
    b = (int(hash_obj[4:6],16)%40)+210
    return f'#{r:02x}{g:02x}{b:02x}'

# --- ⚡ FETCH DATA ---
@st.cache_data(ttl=2)
def get_data():
    allot = supabase.table("staff_allotment").select("*").execute()
    time_t = supabase.table("weekly_timetable").select("*").execute()
    teachers = supabase.table("teachers").select("emis_id, short_name, full_name").execute()
    return allot.data, time_t.data, teachers.data

allot_data, time_data, teach_data = get_data()
df_time = pd.DataFrame(time_data) if time_data else pd.DataFrame()
emis_to_short = {t['emis_id']: t['short_name'] for t in teach_data}

# --- 🏗️ LAYOUT ---
st.title("📅 வாராந்திர கால அட்டவணை மேலாண்மை")

# 1. ஆசிரியர் தேர்வு (மேலே)
t_opts = {f"{t['full_name']} ({t['short_name']})": t for t in teach_data}
sel_teacher_name = st.selectbox("ஆசிரியரைத் தேர்வு செய்க:", ["-- Select Teacher --"] + list(t_opts.keys()))

if sel_teacher_name != "-- Select Teacher --":
    t_info = t_opts[sel_teacher_name]
    t_id = t_info['emis_id']
    
    # 2. ஒதுக்கப்பட்ட வகுப்புகள் (Cards - நடுவில்)
    st.markdown("---")
    st.markdown(f"##### 📌 {t_info['short_name']} -க்கு ஒதுக்கப்பட்ட வகுப்புகள்")
    t_allots = [a for a in allot_data if a['teacher_id'] == t_id]
    
    if t_allots:
        # கார்டுகளை வரிசையாகக் காட்ட 4 காலம்கள்
        card_cols = st.columns(4)
        for idx, a in enumerate(t_allots):
            used = len(df_time[(df_time['teacher_id'] == a['teacher_id']) & 
                               (df_time['class_name'] == a['class_name']) & 
                               (df_time['subject_name'] == a['subject_name'])]) if not df_time.empty else 0
            rem = a['periods_per_week'] - used
            bg = get_color(a['subject_name'])
            is_active = st.session_state.get('active_allot_id') == a['id']
            
            with card_cols[idx % 4]:
                # கார்டு தோற்றம்
                st.markdown(f"""
                    <div style="background:{bg}; border:{'4px solid red' if is_active else '1px solid #000'}; 
                                padding:8px; border-radius:8px; text-align:center;">
                        <b style="font-size:14px;">{a['class_name']}</b><br>
                        <span style="font-size:12px;">{get_short_sub(a['subject_name'])}</span><br>
                        <b style="color:{'red' if rem==0 else 'blue'};">மீதம்: {rem}</b>
                    </div>
                """, unsafe_allow_html=True)
                
                if rem > 0:
                    if st.button(f"தேர்வு: {a['class_name']}", key=f"btn_{a['id']}"):
                        st.session_state['active_allot'] = a
                        st.session_state['active_allot_id'] = a['id']
                        st.session_state['current_class'] = a['class_name']
                        st.rerun()
                else:
                    st.write("🚫 முடிந்தது")

    # 3. அட்டவணை கிரிட் (கீழே)
    active_class = st.session_state.get('current_class')
    
    if active_class:
        st.markdown("---")
        st.markdown(f"##### 📅 {active_class} - கால அட்டவணை (Excel Grid)")
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
        periods = [1, 2, 3, 4, 5, 6, 7, 8]
        
        # Grid Header
        h_cols = st.columns([0.8] + [1]*8)
        h_cols[0].markdown("<div class='grid-label'>Day</div>", unsafe_allow_html=True)
        for p in periods: h_cols[p].markdown(f"<div class='grid-label'>P{p}</div>", unsafe_allow_html=True)

        for day in days:
            r_cols = st.columns([0.8] + [1]*8)
            r_cols[0].markdown(f"<div class='grid-label' style='background:#f9f9f9;'>{day[:3]}</div>", unsafe_allow_html=True)
            
            for p in periods:
                entry = df_time[(df_time['class_name'] == active_class) & 
                                (df_time['day_of_week'] == day) & 
                                (df_time['period_number'] == p)] if not df_time.empty else pd.DataFrame()
                
                with r_cols[p]:
                    if not entry.empty:
                        # ஏற்கனவே பாடம் உள்ளது
                        sub_code = get_short_sub(entry.iloc[0]['subject_name'])
                        t_short = emis_to_short.get(entry.iloc[0]['teacher_id'], "??")
                        bg_color = get_color(sub_code)
                        st.markdown(f'<div style="position:absolute; width:100%; height:35px; background:{bg_color}; z-index:-1; border:1px solid #000;"></div>', unsafe_allow_html=True)
                        if st.button(f"{sub_code}\n{t_short}", key=f"cell_{day}_{p}"):
                            supabase.table("weekly_timetable").delete().eq("id", entry.iloc[0]['id']).execute()
                            st.cache_data.clear()
                            st.rerun()
                    else:
                        # காலியான கட்டம்
                        if st.button(" ", key=f"cell_{day}_{p}"):
                            if 'active_allot' in st.session_state:
                                a = st.session_state['active_allot']
                                # Conflict Check
                                conflict = df_time[(df_time['teacher_id'] == a['teacher_id']) & (df_time['day_of_week'] == day) & (df_time['period_number'] == p)] if not df_time.empty else pd.DataFrame()
                                if not conflict.empty:
                                    st.error(f"முரண்பாடு: {conflict.iloc[0]['class_name']}")
                                else:
                                    supabase.table("weekly_timetable").insert({
                                        "class_name": active_class, "day_of_week": day, "period_number": p,
                                        "teacher_id": a['teacher_id'], "teacher_name": a['teacher_name'],
                                        "subject_name": a['subject_name']
                                    }).execute()
                                    st.cache_data.clear()
                                    st.rerun()
else:
    st.info("தொடங்குவதற்கு மேல் உள்ள பட்டியலில் ஆசிரியரைத் தேர்வு செய்யவும்.")
