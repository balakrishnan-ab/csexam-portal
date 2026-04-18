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

st.set_page_config(page_title="Grid Master Timetable", layout="wide")

# Mark Entry போன்ற Grid CSS
st.markdown("""
    <style>
    /* Table Shell */
    .grid-container { border: 1px solid #ddd; border-radius: 4px; overflow: hidden; }
    /* Cells */
    .stButton > button {
        width: 100%; height: 35px; padding: 0px; font-size: 11px;
        border-radius: 0px; border: 0.5px solid #ccc !important;
        background-color: white; color: black; font-weight: normal;
    }
    .stButton > button:hover { background-color: #f1f1f1; border-color: #999 !important; }
    /* Headers */
    .grid-header {
        font-size: 12px; font-weight: bold; background: #f8f9fa;
        height: 35px; display: flex; align-items: center;
        justify-content: center; border: 0.5px solid #ccc;
    }
    div[data-testid="stColumn"] { padding: 0px !important; margin: 0px !important; }
    </style>
    """, unsafe_allow_html=True)

# தற்காலிக சேமிப்பு (Draft Memory)
if 'temp_table' not in st.session_state:
    st.session_state['temp_table'] = {}

def get_short_sub(sub_name):
    sub_map = {"Computer Science": "CS", "Computer Applications": "CA", "Commerce": "COM", "Accountancy": "ACC", "Economics": "ECO", "Mathematics": "MAT", "Tamil": "TAM", "English": "ENG"}
    return sub_map.get(sub_name, sub_name[:3].upper())

def get_color(text):
    if not text: return "#ffffff"
    hash_obj = hashlib.md5(text.encode()).hexdigest()
    return f'#{(int(hash_obj[:2],16)%30)+220:02x}{(int(hash_obj[2:4],16)%30)+220:02x}{(int(hash_obj[4:6],16)%30)+220:02x}'

# --- ⚡ FETCH DATA ---
@st.cache_data(ttl=60)
def get_data():
    allot = supabase.table("staff_allotment").select("*").execute()
    time_db = supabase.table("weekly_timetable").select("*").execute()
    teach = supabase.table("teachers").select("emis_id, short_name, full_name").execute()
    classes = supabase.table("classes").select("class_name").order("class_name").execute()
    return allot.data, time_db.data, teach.data, [c['class_name'] for c in classes.data]

allot_data, db_list, teach_data, class_list = get_data()

# தரவுதள தகவலை தற்காலிக நினைவகத்திற்கு ஏற்றுதல்
if not st.session_state['temp_table'] and db_list:
    for e in db_list:
        st.session_state['temp_table'][(e['class_name'], e['day_of_week'], e['period_number'])] = e

# --- 🏗️ LAYOUT (இடது: Grid | வலது: Cards) ---
main_grid, side_panel = st.columns([1.5, 0.5])

with side_panel:
    st.markdown("##### 👨‍🏫 ஆசிரியர் & கார்டுகள்")
    t_opts = {f"{t['full_name']} ({t['short_name']})": t for t in teach_data}
    sel_t = st.selectbox("ஆசிரியர்:", ["-- Select --"] + list(t_opts.keys()), label_visibility="collapsed")
    
    if sel_t != "-- Select --":
        t_id = t_opts[sel_t]['emis_id']
        t_allots = [a for a in allot_data if a['teacher_id'] == t_id]
        
        for a in t_allots:
            used = sum(1 for k, v in st.session_state['temp_table'].items() if v['teacher_id'] == a['teacher_id'] and v['class_name'] == a['class_name'] and v['subject_name'] == a['subject_name'])
            rem = a['periods_per_week'] - used
            bg = get_color(a['subject_name'])
            active = st.session_state.get('active_id') == a['id']
            
            st.markdown(f"""
                <div style="background:{bg if rem > 0 else '#eee'}; border:{'3px solid red' if active else '1px solid #ccc'}; 
                            padding:8px; border-radius:4px; text-align:center; margin-bottom:5px; font-size:12px;">
                    <b>{a['class_name']}</b> | {get_short_sub(a['subject_name'])} | <b>Rem: {rem}</b>
                </div>
            """, unsafe_allow_html=True)
            
            if rem > 0:
                if st.button(f"பிடி {a['class_name']}", key=f"p_{a['id']}"):
                    st.session_state['active_allot'] = a
                    st.session_state['active_id'] = a['id']
                    st.session_state['view_class'] = a['class_name']
                    st.rerun()

with main_grid:
    sel_class = st.selectbox("வகுப்பு:", ["-- Select Class --"] + class_list, 
                             index=class_list.index(st.session_state.get('view_class'))+1 if st.session_state.get('view_class') in class_list else 0)
    
    if sel_class != "-- Select Class --":
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
        periods = [1, 2, 3, 4, 5, 6, 7, 8]
        
        # Header Row
        h_cols = st.columns([0.8] + [1]*8)
        h_cols[0].markdown("<div class='grid-header'>Day</div>", unsafe_allow_html=True)
        for p in periods: h_cols[p].markdown(f"<div class='grid-header'>P{p}</div>", unsafe_allow_html=True)

        # Main Grid Row
        for day in days:
            r_cols = st.columns([0.8] + [1]*8)
            r_cols[0].markdown(f"<div class='grid-header' style='background:#fff;'>{day[:3]}</div>", unsafe_allow_html=True)
            for p in periods:
                key = (sel_class, day, p)
                entry = st.session_state['temp_table'].get(key)
                with r_cols[p]:
                    if entry:
                        bg_c = get_color(entry['subject_name'])
                        st.markdown(f'<div style="position:absolute; width:100%; height:35px; background:{bg_c}; z-index:-1; border:0.5px solid #ccc;"></div>', unsafe_allow_html=True)
                        if st.button(f"{get_short_sub(entry['subject_name'])}\n{entry['teacher_name'].split('(')[-1].replace(')','')}", key=f"c_{day}_{p}"):
                            del st.session_state['temp_table'][key]
                            st.rerun()
                    else:
                        if st.button(" ", key=f"c_{day}_{p}"):
                            if 'active_allot' in st.session_state:
                                a = st.session_state['active_allot']
                                st.session_state['temp_table'][key] = {"class_name": sel_class, "day_of_week": day, "period_number": p, "teacher_id": a['teacher_id'], "teacher_name": a['teacher_name'], "subject_name": a['subject_name']}
                                st.rerun()

        # Mark Entry பக்கத்தில் உள்ளது போன்ற Submit பட்டன்
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🚀 சரிபார்த்துச் சேமி (Submit to DB)", type="primary", use_container_width=True):
            with st.spinner("தரவுதளத்தில் சேமிக்கப்படுகிறது..."):
                supabase.table("weekly_timetable").delete().eq("class_name", sel_class).execute()
                batch = [v for k, v in st.session_state['temp_table'].items() if k[0] == sel_class]
                if batch: supabase.table("weekly_timetable").insert(batch).execute()
                st.success(f"{sel_class} அட்டவணை வெற்றிகரமாகச் சேமிக்கப்பட்டது!")
                st.cache_data.clear()
