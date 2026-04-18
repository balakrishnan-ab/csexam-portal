import streamlit as st
import pandas as pd
import hashlib
from supabase import create_client, Client

# --- 1. SUPABASE CONNECTION ---
try:
    url: str = st.secrets["SUPABASE_URL"]
    key: str = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(url, key)
except:
    st.error("Connection Error!")
    st.stop()

st.set_page_config(page_title="3D Master Timetable", layout="wide")

# 🎨 3D மற்றும் கச்சிதமான தோற்றத்திற்கான CSS
st.markdown("""
    <style>
    /* 3D Glass Effect for Allotment Cards */
    .stButton > button {
        width: 100%;
        height: 38px;
        padding: 0px;
        font-size: 10px;
        font-weight: bold;
        border-radius: 6px;
        background: white;
        border: 1px solid #ddd;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.1); /* 3D Shadow */
        transition: all 0.3s;
    }
    .stButton > button:hover {
        transform: translateY(-2px); /* Lift effect */
        box-shadow: 4px 4px 10px rgba(0,0,0,0.15);
    }
    /* Small Pick Button Style */
    .pick-btn > div > button {
        height: 28px !important;
        background: #f8f9fa !important;
        font-size: 9px !important;
        border-left: 4px solid #4CAF50 !important; /* Green indicator */
    }
    /* Compact Table spacing */
    div[data-testid="stColumn"] { padding: 1px !important; }
    </style>
    """, unsafe_allow_html=True)

# பாடங்களின் பெயர்களைச் சுருக்கும் செயல்பாடு
def get_short_sub(sub_name):
    sub_map = {
        "Computer Science": "CS", "Computer Applications": "CA", "Commerce": "COM",
        "Accountancy": "ACC", "Economics": "ECO", "Mathematics": "MAT",
        "Social Science": "S.Sci", "Physics": "PHY", "Chemistry": "CHE",
        "Biology": "BIO", "Business Maths": "B.M", "Tamil": "TAM", "English": "ENG"
    }
    return sub_map.get(sub_name, sub_name[:3].upper())

def get_color(text):
    if not text: return "#ffffff"
    hash_obj = hashlib.md5(text.encode()).hexdigest()
    # 3D தோற்றத்திற்கு மென்மையான வெளிர் நிறங்கள்
    r = (int(hash_obj[:2],16)%30)+225
    g = (int(hash_obj[2:4],16)%30)+225
    b = (int(hash_obj[4:6],16)%30)+225
    return f'#{r:02x}{g:02x}{b:02x}'

# --- ⚡ FETCH DATA ---
@st.cache_data(ttl=2)
def get_data():
    allot = supabase.table("staff_allotment").select("*").execute()
    time_t = supabase.table("weekly_timetable").select("*").execute()
    teachers = supabase.table("teachers").select("emis_id, full_name, short_name").order("full_name").execute()
    classes = supabase.table("classes").select("class_name").order("class_name").execute()
    return allot.data, time_t.data, teachers.data, [c['class_name'] for c in classes.data]

allot_data, time_data, teach_data, class_list = get_data()
df_time = pd.DataFrame(time_data) if time_data else pd.DataFrame()
emis_to_short = {t['emis_id']: t['short_name'] for t in teach_data}

# --- 🏗️ LAYOUT ---
main_col, side_col = st.columns([1.5, 0.5])

with side_col:
    st.markdown("##### 💎 ஆசிரியர் & சில்லுகள்")
    t_opts = {f"{t['full_name']} ({t['short_name']})": t for t in teach_data}
    sel_teacher = st.selectbox("ஆசிரியர்:", ["-- Select --"] + list(t_opts.keys()), label_visibility="collapsed")
    
    if sel_teacher != "-- Select --":
        t_info = t_opts[sel_teacher]
        t_allots = [a for a in allot_data if a['teacher_id'] == t_info['emis_id']]
        
        for a in t_allots:
            used = len(df_time[(df_time['teacher_id'] == a['teacher_id']) & 
                               (df_time['class_name'] == a['class_name']) & 
                               (df_time['subject_name'] == a['subject_name'])]) if not df_time.empty else 0
            rem = a['periods_per_week'] - used
            bg = get_color(a['subject_name'])
            
            # 3D சில்லு வடிவமைப்பு
            st.markdown(f"""
                <div style="background:{bg}; border:1px solid #ccc; padding:4px 8px; border-radius:6px; 
                            box-shadow: 2px 2px 4px rgba(0,0,0,0.1); margin-bottom:4px;">
                    <span style="font-weight:bold; font-size:11px; color:#333;">{a['class_name']}</span>
                    <span style="float:right; font-size:10px; color:{'red' if rem==0 else 'blue'};"><b>{rem}</b></span>
                    <div style="font-size:9px; color:#666;">{get_short_sub(a['subject_name'])}</div>
                </div>
            """, unsafe_allow_html=True)
            
            if rem > 0:
                st.markdown('<div class="pick-btn">', unsafe_allow_html=True)
                if st.button(f"பிடி: {get_short_sub(a['subject_name'])} ({a['class_name']})", key=f"src_{a['id']}"):
                    st.session_state['active_allot'] = a
                st.markdown('</div>', unsafe_allow_html=True)

with main_col:
    st.markdown("##### 📅 கால அட்டவணை")
    sel_class = st.selectbox("வகுப்பு:", ["-- Select --"] + class_list, label_visibility="collapsed")
    
    if sel_class != "-- Select --":
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
        periods = [1, 2, 3, 4, 5, 6, 7, 8]
        
        h_cols = st.columns([0.8] + [1]*8)
        h_cols[0].write("**Day**")
        for i, p in enumerate(periods): h_cols[i+1].write(f"**P{p}**")

        for day in days:
            r_cols = st.columns([0.8] + [1]*8)
            r_cols[0].write(f"**{day[:3]}**")
            
            for p in periods:
                entry = df_time[(df_time['class_name'] == sel_class) & 
                                (df_time['day_of_week'] == day) & 
                                (df_time['period_number'] == p)] if not df_time.empty else pd.DataFrame()
                
                with r_cols[p]:
                    if not entry.empty:
                        s_code = get_short_sub(entry.iloc[0]['subject_name'])
                        t_code = emis_to_short.get(entry.iloc[0]['teacher_id'], "??")
                        bg = get_color(entry.iloc[0]['subject_name'])
                        
                        # அட்டவணை கட்டத்திற்குள் 3D வண்ணம்
                        st.markdown(f"""<div style="position:absolute; width:100%; height:36px; background:{bg}; 
                                    border-radius:4px; border-bottom:3px solid rgba(0,0,0,0.1); 
                                    border-right:2px solid rgba(0,0,0,0.05); z-index:-1;"></div>""", unsafe_allow_html=True)
                        if st.button(f"{s_code}\n{t_code}", key=f"p_{day}_{p}"):
                            supabase.table("weekly_timetable").delete().eq("id", entry.iloc[0]['id']).execute()
                            st.cache_data.clear()
                            st.rerun()
                    else:
                        if st.button("➕", key=f"p_{day}_{p}"):
                            if 'active_allot' in st.session_state:
                                a = st.session_state['active_allot']
                                conflict = df_time[(df_time['teacher_id'] == a['teacher_id']) & 
                                                   (df_time['day_of_week'] == day) & 
                                                   (df_time['period_number'] == p)] if not df_time.empty else pd.DataFrame()
                                if not conflict.empty:
                                    st.error(f"முரண்பாடு: {conflict.iloc[0]['class_name']}")
                                else:
                                    supabase.table("weekly_timetable").insert({
                                        "class_name": sel_class, "day_of_week": day, "period_number": p,
                                        "teacher_id": a['teacher_id'], "teacher_name": a['teacher_name'],
                                        "subject_name": a['subject_name']
                                    }).execute()
                                    st.cache_data.clear()
                                    st.rerun()
