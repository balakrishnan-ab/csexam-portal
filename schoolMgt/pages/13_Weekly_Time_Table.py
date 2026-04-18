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

st.set_page_config(page_title="Excel Style Timetable", layout="wide")

# கச்சிதமான மற்றும் வண்ணமயமான தோற்றத்திற்கான CSS
st.markdown("""
    <style>
    /* கிரிட் கட்டங்கள் */
    .stButton > button {
        width: 100%; height: 32px; padding: 0px; font-size: 10px;
        border-radius: 0px; border: 0.5px solid #ccc; line-height: 1.1;
    }
    /* Day Column */
    .day-label {
        font-size: 11px; font-weight: bold; background: #eee;
        height: 32px; display: flex; align-items: center;
        justify-content: center; border: 0.5px solid #ccc;
    }
    /* Active Card Highlight */
    .active-card { border: 3px solid #000 !important; box-shadow: 0px 0px 10px rgba(0,0,0,0.5); }
    div[data-testid="stColumn"] { padding: 0px !important; margin: 0px !important; }
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
    # தெளிவான வண்ணங்கள் (Vibrant colors)
    r = (int(hash_obj[:2],16)%60)+190
    g = (int(hash_obj[2:4],16)%60)+190
    b = (int(hash_obj[4:6],16)%60)+190
    return f'#{r:02x}{g:02x}{b:02x}'

# --- ⚡ FETCH DATA ---
@st.cache_data(ttl=2)
def get_data():
    allot = supabase.table("staff_allotment").select("*").execute()
    time_t = supabase.table("weekly_timetable").select("*").execute()
    teachers = supabase.table("teachers").select("emis_id, short_name, full_name").execute()
    classes = supabase.table("classes").select("class_name").order("class_name").execute()
    return allot.data, time_t.data, teachers.data, [c['class_name'] for c in classes.data]

allot_data, time_data, teach_data, class_list = get_data()
df_time = pd.DataFrame(time_data) if time_data else pd.DataFrame()
emis_to_short = {t['emis_id']: t['short_name'] for t in teach_data}

# --- 🏗️ LAYOUT ---
main_col, side_col = st.columns([1.6, 0.4])

with side_col:
    st.write("##### 👨‍🏫 தேர்வு செய்க")
    t_opts = {f"{t['full_name']} ({t['short_name']})": t for t in teach_data}
    sel_teacher = st.selectbox("ஆசிரியர்:", ["-- Select --"] + list(t_opts.keys()), label_visibility="collapsed")
    
    if sel_teacher != "-- Select --":
        t_id = t_opts[sel_teacher]['emis_id']
        t_allots = [a for a in allot_data if a['teacher_id'] == t_id]
        
        for a in t_allots:
            used = len(df_time[(df_time['teacher_id'] == a['teacher_id']) & (df_time['class_name'] == a['class_name']) & (df_time['subject_name'] == a['subject_name'])]) if not df_time.empty else 0
            rem = a['periods_per_week'] - used
            bg = get_color(a['subject_name'])
            
            # தற்போது தேர்வு செய்யப்பட்டுள்ள சில்லு என்றால் பார்டர் தடிமனாக இருக்கும்
            is_active = st.session_state.get('active_allot_id') == a['id']
            border_style = "3px solid black" if is_active else "1px solid #999"
            
            st.markdown(f"""<div style="background:{bg}; border:{border_style}; padding:4px; border-radius:4px; text-align:center; margin-bottom:2px;">
                <span style="font-size:11px; font-weight:bold;">{a['class_name']} ({rem})</span>
                </div>""", unsafe_allow_html=True)
            
            if rem > 0:
                if st.button(f"பிடி {a['class_name']}", key=f"allot_{a['id']}"):
                    st.session_state['active_allot'] = a
                    st.session_state['active_allot_id'] = a['id']
                    st.rerun()

with main_col:
    sel_class = st.selectbox("வகுப்பு:", ["-- Select --"] + class_list)
    if sel_class != "-- Select --":
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
        periods = [1, 2, 3, 4, 5, 6, 7, 8]
        
        # Header Row
        h_cols = st.columns([0.8] + [1]*8)
        h_cols[0].write("Day")
        for i, p in enumerate(periods): h_cols[i+1].write(f"P{p}")

        for day in days:
            r_cols = st.columns([0.8] + [1]*8)
            r_cols[0].markdown(f"<div class='day-label'>{day[:3]}</div>", unsafe_allow_html=True)
            
            for p in periods:
                entry = df_time[(df_time['class_name'] == sel_class) & (df_time['day_of_week'] == day) & (df_time['period_number'] == p)] if not df_time.empty else pd.DataFrame()
                
                with r_cols[p]:
                    if not entry.empty:
                        sub_code, t_code = get_short_sub(entry.iloc[0]['subject_name']), emis_to_short.get(entry.iloc[0]['teacher_id'], "??")
                        bg_color = get_color(sub_code)
                        st.markdown(f'<div style="position:absolute; width:100%; height:32px; background:{bg_color}; border:0.5px solid #aaa; z-index:-1;"></div>', unsafe_allow_html=True)
                        if st.button(f"{sub_code}\n{t_code}", key=f"cell_{day}_{p}"):
                            supabase.table("weekly_timetable").delete().eq("id", entry.iloc[0]['id']).execute()
                            st.cache_data.clear()
                            st.rerun()
                    else:
                        # காலியான கட்டம் (பிளஸ் குறி இல்லை)
                        if st.button(" ", key=f"cell_{day}_{p}"):
                            if 'active_allot' in st.session_state:
                                a = st.session_state['active_allot']
                                used_now = len(df_time[(df_time['teacher_id'] == a['teacher_id']) & (df_time['class_name'] == a['class_name']) & (df_time['subject_name'] == a['subject_name'])]) if not df_time.empty else 0
                                if used_now < a['periods_per_week']:
                                    supabase.table("weekly_timetable").insert({"class_name": sel_class, "day_of_week": day, "period_number": p, "teacher_id": a['teacher_id'], "teacher_name": a['teacher_name'], "subject_name": a['subject_name']}).execute()
                                    st.cache_data.clear()
                                    st.rerun()
                                else: st.error("Limit reached!")
