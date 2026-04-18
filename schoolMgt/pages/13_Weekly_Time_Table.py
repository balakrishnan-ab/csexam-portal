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

st.set_page_config(page_title="Compact Master Timetable", layout="wide")

# 🎨 Excel பாணியில் கச்சிதமான தோற்றத்திற்கான CSS
st.markdown("""
    <style>
    /* கிரிட் கட்டங்களை மிகச் சிறியதாக்க */
    .stButton > button {
        width: 100%;
        height: 30px; /* மிகக் குறைந்த உயரம் */
        padding: 0px;
        font-size: 9px; /* சிறிய எழுத்துக்கள் */
        border-radius: 2px;
        border: 1px solid #ddd;
        line-height: 1;
        transition: all 0.2s;
    }
    .stButton > button:hover {
        border: 1px solid #999;
        box-shadow: 1px 1px 3px rgba(0,0,0,0.1);
    }
    /* ஆசிரியர் சில்லுகளுக்கான ஸ்டைல் */
    .allot-btn > div > button {
        height: 35px !important;
        font-weight: bold !important;
        border-bottom: 2px solid rgba(0,0,0,0.2) !important;
    }
    /* Column-களுக்கு இடையே உள்ள இடைவெளியைக் குறைக்க */
    div[data-testid="stColumn"] {
        padding: 0.5px !important;
        margin: 0px !important;
    }
    /* Day Column-க்கான ஸ்டைல் */
    .day-col {
        font-size: 10px;
        font-weight: bold;
        color: #333;
        text-align: center;
        background: #f8f9fa;
        padding: 5px;
        border-radius: 3px;
    }
    </style>
    """, unsafe_allow_html=True)

# பாடங்களின் பெயர்களைச் சுருக்கும் செயல்பாடு
def get_short_sub(sub_name):
    sub_map = {
        "Computer Science": "CS", "Computer Applications": "CA", "Commerce": "COM",
        "Accountancy": "ACC", "Economics": "ECO", "Mathematics": "MAT",
        "Social Science": "S.Sci", "Physics": "PHY", "Chemistry": "CHE",
        "Biology": "BIO", "Tamil": "TAM", "English": "ENG"
    }
    # மேப்பில் இருந்தால் அதைத் தரும், இல்லையெனில் முதல் 3 எழுத்துக்களைத் தரும்
    return sub_map.get(sub_name, sub_name[:3].upper())

# வண்ணங்களை உருவாக்கும் செயல்பாடு (மென்மையான Pastel நிறங்கள் - Excel போல)
def get_color(text):
    if not text: return "#ffffff"
    hash_obj = hashlib.md5(text.encode()).hexdigest()
    # வெளிர் நிறங்கள் (Pastel colors)
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
    classes = supabase.table("classes").select("class_name").order("class_name").execute()
    return allot.data, time_t.data, teachers.data, [c['class_name'] for c in classes.data]

allot_data, time_data, teach_data, class_list = get_data()
df_time = pd.DataFrame(time_data) if time_data else pd.DataFrame()
emis_to_short = {t['emis_id']: t['short_name'] for t in teach_data}

st.title("🏫 பள்ளி முதன்மை கால அட்டவணை (Compact View)")

# --- 🏗️ LAYOUT ---
# 1. கால அட்டவணை | 2. ஆசிரியர் சில்லுகள் (வலதுபுறம் கச்சிதமாக)
main_col, side_col = st.columns([1.5, 0.5])

with side_col:
    st.markdown("##### 👨‍🏫 ஆசிரியர் & சில்லுகள்")
    t_opts = {f"{t['full_name']} ({t['short_name']})": t for t in teach_data}
    sel_teacher = st.selectbox("ஆசிரியர்:", ["-- Select --"] + list(t_opts.keys()), label_visibility="collapsed")
    
    if sel_teacher != "-- Select --":
        t_id = t_opts[sel_teacher]['emis_id']
        t_allots = [a for a in allot_data if a['teacher_id'] == t_id]
        
        # ஒரு வரிசையில் 4 சில்லுகள் (Compact Grid of 4)
        for i in range(0, len(t_allots), 4):
            cols = st.columns(4)
            for j, a in enumerate(t_allots[i:i+4]):
                used = len(df_time[(df_time['teacher_id'] == a['teacher_id']) & 
                                   (df_time['class_name'] == a['class_name']) & 
                                   (df_time['subject_name'] == a['subject_name'])]) if not df_time.empty else 0
                rem = a['periods_per_week'] - used
                
                if rem > 0:
                    with cols[j]:
                        st.markdown('<div class="allot-btn">', unsafe_allow_html=True)
                        btn_label = f"{a['class_name']}\n{get_short_sub(a['subject_name'])}\n({rem})"
                        if st.button(btn_label, key=f"allot_{a['id']}"):
                            st.session_state['active_allot'] = a
                        st.markdown('</div>', unsafe_allow_html=True)
                else:
                    cols[j].markdown(f"<div style='font-size:8px; color:red; text-align:center;'>{a['class_name']}<br>Fin</div>", unsafe_allow_html=True)

with main_col:
    st.markdown("##### 📅 கால அட்டவணை")
    sel_class = st.selectbox("வகுப்பைத் தேர்வு செய்க:", ["-- Select --"] + class_list, label_visibility="collapsed")
    
    if sel_class != "-- Select --":
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
        periods = [1, 2, 3, 4, 5, 6, 7, 8]
        
        # Header Row (Day | P1-P8)
        h_cols = st.columns([0.8] + [1]*8)
        h_cols[0].write("**Day**")
        for i, p in enumerate(periods): h_cols[i+1].write(f"**P{p}**")

        for day in days:
            r_cols = st.columns([0.8] + [1]*8)
            # கிழமையைச் சுருக்கி (Mon, Tue)
            r_cols[0].markdown(f"<div class='day-col'>{day[:3]}</div>", unsafe_allow_html=True)
            
            for p in periods:
                entry = df_time[(df_time['class_name'] == sel_class) & 
                                (df_time['day_of_week'] == day) & 
                                (df_time['period_number'] == p)] if not df_time.empty else pd.DataFrame()
                
                with r_cols[p]:
                    if not entry.empty:
                        # ஏற்கனவே உள்ள பதிவு - கச்சிதமான வண்ணங்களுடன்
                        s_code = get_short_sub(entry.iloc[0]['subject_name'])
                        t_code = emis_to_short.get(entry.iloc[0]['teacher_id'], "??")
                        bg = get_color(s_code)
                        
                        st.markdown(f"""<div style="position:absolute; width:100%; height:29px; background:{bg}; z-index:-1; border-radius:2px;"></div>""", unsafe_allow_html=True)
                        # CS MR என்று ஒரே வரியில் சுருக்கமாக
                        if st.button(f"{s_code}\n{t_code}", key=f"cell_{day}_{p}"):
                            supabase.table("weekly_timetable").delete().eq("id", entry.iloc[0]['id']).execute()
                            st.cache_data.clear()
                            st.rerun()
                    else:
                        # காலியாக இருந்தால்
                        if st.button("➕", key=f"cell_{day}_{p}"):
                            if 'active_allot' in st.session_state:
                                a = st.session_state['active_allot']
                                # இறுதி சரிபார்ப்பு: மீதமுள்ள எண்ணிக்கை இருக்கிறதா?
                                current_used = len(df_time[(df_time['teacher_id'] == a['teacher_id']) & (df_time['class_name'] == a['class_name']) & (df_time['subject_name'] == a['subject_name'])]) if not df_time.empty else 0
                                if current_used < a['periods_per_week']:
                                    # Conflict Check
                                    conflict = df_time[(df_time['teacher_id'] == a['teacher_id']) & (df_time['day_of_week'] == day) & (df_time['period_number'] == p)] if not df_time.empty else pd.DataFrame()
                                    if not conflict.empty:
                                        st.error(f"Conflict: {conflict.iloc[0]['class_name']}")
                                    else:
                                        supabase.table("weekly_timetable").insert({
                                            "class_name": sel_class, "day_of_week": day, "period_number": p,
                                            "teacher_id": a['teacher_id'], "teacher_name": a['teacher_name'],
                                            "subject_name": a['subject_name']
                                        }).execute()
                                        st.cache_data.clear()
                                        st.rerun()
                                else:
                                    st.warning("Limit reached!")
                            else:
                                st.warning("முதலில் வலதுபுறம் பாடம் தேர்வு செய்க!")
