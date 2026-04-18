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

st.set_page_config(page_title="Smart Timetable", layout="wide")

# கச்சிதமான தோற்றத்திற்கான CSS (Excel Style)
st.markdown("""
    <style>
    .stButton > button { width: 100%; height: 35px; padding: 0px; font-size: 9px; border-radius: 2px; line-height: 1; border: 1px solid #ccc; }
    .small-card { padding: 2px; font-size: 10px; border-radius: 3px; margin-bottom: 2px; text-align: center; border: 1px solid #aaa; }
    div[data-testid="stColumn"] { padding: 0px 1px !important; }
    </style>
    """, unsafe_allow_html=True)

# பாடங்களின் பெயர்களைச் சுருக்கும் செயல்பாடு
def get_short_sub(sub_name):
    sub_map = {
        "Computer Science": "CS",
        "Computer Applications": "CA",
        "Commerce": "COM",
        "Accountancy": "ACC",
        "Economics": "ECO",
        "Mathematics": "MATH",
        "Social Science": "S.Sci",
        "Physics": "PHY",
        "Chemistry": "CHE",
        "Biology": "BIO",
        "Business Maths": "B.M"
    }
    # மேப்பில் இருந்தால் அதைத் தரும், இல்லையெனில் முதல் 3 எழுத்துக்களைத் தரும்
    return sub_map.get(sub_name, sub_name[:3].upper())

def get_color(text):
    if not text: return "#ffffff"
    hash_obj = hashlib.md5(text.encode()).hexdigest()
    return f'#{(int(hash_obj[:2],16)%40)+210:02x}{(int(hash_obj[2:4],16)%40)+210:02x}{(int(hash_obj[4:6],16)%40)+210:02x}'

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
main_col, side_col = st.columns([1.4, 0.6])

with side_col:
    st.markdown("##### 👨‍🏫 ஆசிரியர் & சில்லுகள்")
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
            
            # மிகச்சிறிய சில்லு
            st.markdown(f"""<div style="background:{bg}; border:1px solid #999; padding:2px; border-radius:3px; text-align:center; font-size:10px; color:black;">
                <b>{a['class_name']}</b> - {get_short_sub(a['subject_name'])} (மீதம்: {rem})
                </div>""", unsafe_allow_html=True)
            
            if rem > 0:
                if st.button(f"பிடி: {a['class_name']}-{get_short_sub(a['subject_name'])}", key=f"src_{a['id']}"):
                    st.session_state['active_allot'] = a
                    st.toast(f"{a['class_name']} பாடம் பிடிக்கப்பட்டது!")

with main_col:
    st.markdown("##### 📅 கால அட்டவணை")
    sel_class = st.selectbox("வகுப்பு:", ["-- Select --"] + class_list, label_visibility="collapsed")
    
    if sel_class != "-- Select --":
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
        periods = [1, 2, 3, 4, 5, 6, 7, 8]
        
        # Grid Header (Day + P1-P8)
        h_cols = st.columns([0.8] + [1]*8)
        h_cols[0].write("**Day**")
        for i, p in enumerate(periods): h_cols[i+1].write(f"**P{p}**")

        for day in days:
            r_cols = st.columns([0.8] + [1]*8)
            r_cols[0].write(f"**{day[:3]}**") # கிழமையைச் சுருக்கி (Mon, Tue)
            
            for p in periods:
                entry = df_time[(df_time['class_name'] == sel_class) & 
                                (df_time['day_of_week'] == day) & 
                                (df_time['period_number'] == p)] if not df_time.empty else pd.DataFrame()
                
                with r_cols[p]:
                    if not entry.empty:
                        # ஏற்கனவே உள்ள பதிவு - சுருக்கப் பெயர்கள்
                        s_code = get_short_sub(entry.iloc[0]['subject_name'])
                        t_code = emis_to_short.get(entry.iloc[0]['teacher_id'], "??")
                        bg = get_color(entry.iloc[0]['subject_name'])
                        
                        st.markdown(f"""<div style="position:absolute; width:100%; height:33px; background:{bg}; z-index:-1; border-radius:2px; border:1px solid #aaa;"></div>""", unsafe_allow_html=True)
                        if st.button(f"{s_code}\n{t_code}", key=f"p_{day}_{p}"):
                            # டெலீட் செய்வதற்கு முன் ஒரு உறுதிப்படுத்தல் தேவைப்பட்டால் popover பயன்படுத்தலாம்
                            supabase.table("weekly_timetable").delete().eq("id", entry.iloc[0]['id']).execute()
                            st.cache_data.clear()
                            st.rerun()
                    else:
                        # காலியாக இருந்தால்
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
