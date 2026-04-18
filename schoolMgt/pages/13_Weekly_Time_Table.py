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

# Excel போன்ற நேர்த்தியான பார்டர் மற்றும் கிரிட் ஸ்டைலிங்
st.markdown("""
    <style>
    /* Excel Table Grid */
    .stButton > button {
        width: 100%; height: 35px; padding: 0px; font-size: 11px;
        border-radius: 0px; border: 1px solid #000 !important; /* தடிமனான கருப்பு கோடு */
        line-height: 1.1; font-weight: 500;
    }
    /* Day & Header Labels */
    .header-label {
        font-size: 12px; font-weight: bold; background: #d3d3d3;
        height: 35px; display: flex; align-items: center;
        justify-content: center; border: 1px solid #000;
    }
    /* Teacher Allotment Cards */
    .allot-card {
        border-radius: 4px; margin-bottom: 5px; text-align: center;
        transition: transform 0.2s;
    }
    .active-selection {
        border: 4px solid #ff4b4b !important; /* தேர்வு செய்யப்பட்ட சில்லு சிவப்பு பார்டர் */
    }
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
    # தெளிவான வண்ணங்கள்
    r = (int(hash_obj[:2],16)%50)+200
    g = (int(hash_obj[2:4],16)%50)+200
    b = (int(hash_obj[4:6],16)%50)+200
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
main_col, side_col = st.columns([1.5, 0.5])

with side_col:
    st.write("##### 👨‍🏫 ஆசிரியர் தேர்வு")
    t_opts = {f"{t['full_name']} ({t['short_name']})": t for t in teach_data}
    sel_teacher = st.selectbox("Teacher Selection", list(t_opts.keys()), label_visibility="collapsed")
    
    if sel_teacher:
        t_id = t_opts[sel_teacher]['emis_id']
        t_allots = [a for a in allot_data if a['teacher_id'] == t_id]
        
        for a in t_allots:
            used = len(df_time[(df_time['teacher_id'] == a['teacher_id']) & (df_time['class_name'] == a['class_name']) & (df_time['subject_name'] == a['subject_name'])]) if not df_time.empty else 0
            rem = a['periods_per_week'] - used
            bg = get_color(a['subject_name'])
            
            # சில்லு வடிவமைப்பு - பிரிக்காமல் ஒரே பெட்டியாக
            is_active = st.session_state.get('active_allot_id') == a['id']
            border_css = "active-selection" if is_active else ""
            
            # முழு சில்லும் ஒரே பட்டனாக
            if rem > 0:
                if st.button(f"{a['class_name']} - {get_short_sub(a['subject_name'])}\n(மீதம்: {rem})", key=f"allot_{a['id']}", 
                             help="இதை கிளிக் செய்து பின் அட்டவணையில் ஒட்டவும்"):
                    st.session_state['active_allot'] = a
                    st.session_state['active_allot_id'] = a['id']
                    st.rerun()
            else:
                st.markdown(f"<div style='background:#eee; color:#aaa; border:1px solid #ccc; padding:5px; font-size:10px; text-align:center;'>{a['class_name']} (0)</div>", unsafe_allow_html=True)

with main_col:
    sel_class = st.selectbox("Select Class:", ["-- Select Class --"] + class_list, label_visibility="collapsed")
    
    if sel_class != "-- Select Class --":
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
        periods = [1, 2, 3, 4, 5, 6, 7, 8]
        
        # Grid Header
        h_cols = st.columns([0.8] + [1]*8)
        h_cols[0].markdown("<div class='header-label'>Day</div>", unsafe_allow_html=True)
        for p in periods:
            h_cols[p].markdown(f"<div class='header-label'>P{p}</div>", unsafe_allow_html=True)

        for day in days:
            r_cols = st.columns([0.8] + [1]*8)
            r_cols[0].markdown(f"<div class='header-label' style='background:#f9f9f9;'>{day[:3]}</div>", unsafe_allow_html=True)
            
            for p in periods:
                entry = df_time[(df_time['class_name'] == sel_class) & (df_time['day_of_week'] == day) & (df_time['period_number'] == p)] if not df_time.empty else pd.DataFrame()
                
                with r_cols[p]:
                    if not entry.empty:
                        sub_code = get_short_sub(entry.iloc[0]['subject_name'])
                        t_code = emis_to_short.get(entry.iloc[0]['teacher_id'], "??")
                        bg_color = get_color(sub_code)
                        # Excel போன்ற வண்ணக் கோடுகள்
                        st.markdown(f'<div style="position:absolute; width:100%; height:35px; background:{bg_color}; z-index:-1;"></div>', unsafe_allow_html=True)
                        if st.button(f"{sub_code}\n{t_code}", key=f"cell_{day}_{p}"):
                            supabase.table("weekly_timetable").delete().eq("id", entry.iloc[0]['id']).execute()
                            st.cache_data.clear()
                            st.rerun()
                    else:
                        # காலியான Excel செல்
                        if st.button(" ", key=f"cell_{day}_{p}"):
                            if 'active_allot' in st.session_state:
                                a = st.session_state['active_allot']
                                supabase.table("weekly_timetable").insert({
                                    "class_name": sel_class, "day_of_week": day, "period_number": p,
                                    "teacher_id": a['teacher_id'], "teacher_name": a['teacher_name'],
                                    "subject_name": a['subject_name']
                                }).execute()
                                st.cache_data.clear()
                                st.rerun()
