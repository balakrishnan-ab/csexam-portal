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

st.set_page_config(page_title="Grid Timetable", layout="wide")

# CSS: அட்டவணை மற்றும் சில்லுகளுக்கான வடிவம்
st.markdown("""
    <style>
    /* Excel Grid Styling */
    .stButton > button {
        width: 100%; height: 35px; padding: 0px; font-size: 11px;
        border-radius: 0px; border: 1px solid #000 !important;
        font-weight: bold; background-color: white;
    }
    /* Day & Period Labels */
    .grid-label {
        font-size: 11px; font-weight: bold; background: #E0E0E0;
        height: 35px; display: flex; align-items: center;
        justify-content: center; border: 1px solid #000;
    }
    /* Right Side Chips */
    .chip-container {
        border: 1px solid #999; border-radius: 5px; padding: 8px;
        margin-bottom: 5px; text-align: center; cursor: pointer;
    }
    div[data-testid="stColumn"] { padding: 1px !important; margin: 0px !important; }
    </style>
    """, unsafe_allow_html=True)

# தற்காலிக நினைவகம் (Draft Mode)
if 'draft_table' not in st.session_state:
    st.session_state['draft_table'] = {}

def get_short_sub(sub_name):
    sub_map = {"Computer Science": "CS", "Computer Applications": "CA", "Commerce": "COM", "Accountancy": "ACC", "Economics": "ECO", "Mathematics": "MAT", "Tamil": "TAM", "English": "ENG"}
    return sub_map.get(sub_name, sub_name[:3].upper())

def get_color(text):
    if not text: return "#ffffff"
    hash_obj = hashlib.md5(text.encode()).hexdigest()
    return f'#{(int(hash_obj[:2],16)%40)+210:02x}{(int(hash_obj[2:4],16)%40)+210:02x}{(int(hash_obj[4:6],16)%40)+210:02x}'

# --- ⚡ FETCH DATA ---
@st.cache_data(ttl=60)
def get_init_data():
    allot = supabase.table("staff_allotment").select("*").execute()
    time_db = supabase.table("weekly_timetable").select("*").execute()
    teach = supabase.table("teachers").select("emis_id, short_name, full_name").execute()
    classes = supabase.table("classes").select("class_name").order("class_name").execute()
    return allot.data, time_db.data, teach.data, [c['class_name'] for c in classes.data]

allot_data, db_list, teach_data, class_list = get_init_data()

# தரவுதள தகவல்களை Draft-க்கு மாற்றுதல்
if not st.session_state['draft_table'] and db_list:
    for e in db_list:
        st.session_state['draft_table'][(e['class_name'], e['day_of_week'], e['period_number'])] = e

# --- 🏗️ LAYOUT (இடது: அட்டவணை | வலது: சில்லுகள்) ---
left_col, right_col = st.columns([1.4, 0.6])

with right_col:
    st.markdown("##### 👨‍🏫 ஆசிரியர் & சில்லுகள்")
    t_opts = {f"{t['full_name']} ({t['short_name']})": t for t in teach_data}
    sel_t = st.selectbox("ஆசிரியர்:", ["-- Select --"] + list(t_opts.keys()), label_visibility="collapsed")
    
    if sel_t != "-- Select --":
        t_id = t_opts[sel_t]['emis_id']
        t_allots = [a for a in allot_data if a['teacher_id'] == t_id]
        
        # சில்லுகள் (Cards)
        for a in t_allots:
            used = sum(1 for k, v in st.session_state['draft_table'].items() if v['teacher_id'] == a['teacher_id'] and v['class_name'] == a['class_name'] and v['subject_name'] == a['subject_name'])
            rem = a['periods_per_week'] - used
            bg = get_color(a['subject_name'])
            active = st.session_state.get('active_id') == a['id']
            
            st.markdown(f"""
                <div style="background:{bg if rem > 0 else '#eee'}; border:{'4px solid red' if active else '1px solid #000'}; 
                            padding:8px; border-radius:5px; text-align:center; margin-bottom:5px;">
                    <b>{a['class_name']}</b> | {get_short_sub(a['subject_name'])} | <b>Rem: {rem}</b>
                </div>
            """, unsafe_allow_html=True)
            
            if rem > 0:
                if st.button(f"பிடி {a['class_name']}", key=f"pick_{a['id']}"):
                    st.session_state['active_allot'] = a
                    st.session_state['active_id'] = a['id']
                    st.session_state['sel_class'] = a['class_name']
                    st.rerun()

with left_col:
    sel_class = st.selectbox("வகுப்பு:", ["-- Select Class --"] + class_list, index=class_list.index(st.session_state.get('sel_class'))+1 if st.session_state.get('sel_class') in class_list else 0)
    
    if sel_class != "-- Select Class --":
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
        periods = [1, 2, 3, 4, 5, 6, 7, 8]
        
        # Header
        h_cols = st.columns([0.8] + [1]*8)
        h_cols[0].markdown("<div class='grid-label'>Day</div>", unsafe_allow_html=True)
        for p in periods: h_cols[p].markdown(f"<div class='grid-label'>P{p}</div>", unsafe_allow_html=True)

        # Grid
        for day in days:
            r_cols = st.columns([0.8] + [1]*8)
            r_cols[0].markdown(f"<div class='grid-label' style='background:#f9f9f9;'>{day[:3]}</div>", unsafe_allow_html=True)
            for p in periods:
                key = (sel_class, day, p)
                entry = st.session_state['draft_table'].get(key)
                with r_cols[p]:
                    if entry:
                        bg_c = get_color(entry['subject_name'])
                        st.markdown(f'<div style="position:absolute; width:100%; height:35px; background:{bg_c}; z-index:-1; border:1px solid #000;"></div>', unsafe_allow_html=True)
                        if st.button(f"{get_short_sub(entry['subject_name'])}\n{entry['teacher_name'].split('(')[-1].replace(')','')}", key=f"c_{day}_{p}"):
                            del st.session_state['draft_table'][key]
                            st.rerun()
                    else:
                        if st.button(" ", key=f"c_{day}_{p}"):
                            if 'active_allot' in st.session_state:
                                a = st.session_state['active_allot']
                                st.session_state['draft_table'][key] = {"class_name": sel_class, "day_of_week": day, "period_number": p, "teacher_id": a['teacher_id'], "teacher_name": a['teacher_name'], "subject_name": a['subject_name']}
                                st.rerun()

        if st.button("💾 SAVE ALL CHANGES", type="primary", use_container_width=True):
            with st.spinner("Saving..."):
                supabase.table("weekly_timetable").delete().eq("class_name", sel_class).execute()
                batch = [v for k, v in st.session_state['draft_table'].items() if k[0] == sel_class]
                if batch: supabase.table("weekly_timetable").insert(batch).execute()
                st.success("Saved Successfully!")
                st.cache_data.clear()
