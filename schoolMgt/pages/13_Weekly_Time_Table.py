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

# CSS for Grid
st.markdown("""
    <style>
    .stButton > button { width: 100%; height: 35px; padding: 0px; font-size: 11px; border-radius: 0px; border: 1px solid #000 !important; font-weight: bold; background-color: white; }
    .grid-label { font-size: 11px; font-weight: bold; background: #E0E0E0; height: 35px; display: flex; align-items: center; justify-content: center; border: 1px solid #000; }
    div[data-testid="stColumn"] { padding: 1px !important; margin: 0px !important; }
    </style>
    """, unsafe_allow_html=True)

# State Management for Draft (மாற்றங்களைத் தற்காலிகமாகச் சேமிக்க)
if 'draft_timetable' not in st.session_state:
    st.session_state['draft_timetable'] = {} # Key: (class, day, period), Value: staff_info

def get_short_sub(sub_name):
    sub_map = {"Computer Science": "CS", "Computer Applications": "CA", "Commerce": "COM", "Accountancy": "ACC", "Economics": "ECO", "Mathematics": "MAT", "Tamil": "TAM", "English": "ENG"}
    return sub_map.get(sub_name, sub_name[:3].upper())

def get_color(text):
    if not text: return "#ffffff"
    hash_obj = hashlib.md5(text.encode()).hexdigest()
    return f'#{(int(hash_obj[:2],16)%40)+210:02x}{(int(hash_obj[2:4],16)%40)+210:02x}{(int(hash_obj[4:6],16)%40)+210:02x}'

# --- ⚡ FETCH DATA (Initial only) ---
@st.cache_data(ttl=60)
def get_initial_data():
    allot = supabase.table("staff_allotment").select("*").execute()
    time_t = supabase.table("weekly_timetable").select("*").execute()
    teachers = supabase.table("teachers").select("emis_id, short_name, full_name").execute()
    return allot.data, time_t.data, teachers.data

allot_data, db_time_list, teach_data = get_initial_data()

# தரவுதளத்தில் உள்ளதை Session State-க்கு மாற்றுதல் (முதல் முறை மட்டும்)
if not st.session_state['draft_timetable'] and db_time_list:
    for entry in db_time_list:
        key = (entry['class_name'], entry['day_of_week'], entry['period_number'])
        st.session_state['draft_timetable'][key] = entry

# --- 🏗️ LAYOUT ---
st.title("📅 வாராந்திர கால அட்டவணை (Fast Edit Mode)")

t_opts = {f"{t['full_name']} ({t['short_name']})": t for t in teach_data}
sel_teacher_name = st.selectbox("ஆசிரியரைத் தேர்வு செய்க:", ["-- Select Teacher --"] + list(t_opts.keys()))

if sel_teacher_name != "-- Select Teacher --":
    t_info = t_opts[sel_teacher_name]
    t_id = t_info['emis_id']
    
    # 📌 1. Card View
    st.markdown("##### 📌 ஒதுக்கப்பட்ட வகுப்புகள்")
    t_allots = [a for a in allot_data if a['teacher_id'] == t_id]
    card_cols = st.columns(len(t_allots) if t_allots else 1)
    
    for idx, a in enumerate(t_allots):
        # Draft-ல் இருந்து பயன்பாட்டை எண்ணுதல்
        used = sum(1 for k, v in st.session_state['draft_timetable'].items() if v['teacher_id'] == a['teacher_id'] and v['class_name'] == a['class_name'] and v['subject_name'] == a['subject_name'])
        rem = a['periods_per_week'] - used
        bg = get_color(a['subject_name'])
        is_active = st.session_state.get('active_allot_id') == a['id']
        
        with card_cols[idx]:
            st.markdown(f'<div style="background:{bg if rem > 0 else "#eee"}; border:{"4px solid red" if is_active else "1px solid #000"}; padding:5px; border-radius:5px; text-align:center;"><b>{a['class_name']}</b><br><small>{get_short_sub(a['subject_name'])}</small><br><b>Rem: {rem}</b></div>', unsafe_allow_html=True)
            if rem > 0 and st.button(f"Pick {idx+1}", key=f"sel_{a['id']}"):
                st.session_state['active_allot'] = a
                st.session_state['active_allot_id'] = a['id']
                st.session_state['current_class'] = a['class_name']
                st.rerun()

    active_class = st.session_state.get('current_class')
    if active_class:
        st.markdown(f"##### 📅 {active_class} - Draft Editor")
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
        periods = [1, 2, 3, 4, 5, 6, 7, 8]
        
        # Grid Display
        h_cols = st.columns([0.8] + [1]*8)
        h_cols[0].markdown("<div class='grid-label'>Day</div>", unsafe_allow_html=True)
        for p in periods: h_cols[p].markdown(f"<div class='grid-label'>P{p}</div>", unsafe_allow_html=True)

        for day in days:
            r_cols = st.columns([0.8] + [1]*8)
            r_cols[0].markdown(f"<div class='grid-label' style='background:#f9f9f9;'>{day[:3]}</div>", unsafe_allow_html=True)
            for p in periods:
                cell_key = (active_class, day, p)
                entry = st.session_state['draft_timetable'].get(cell_key)
                with r_cols[p]:
                    if entry:
                        bg_c = get_color(entry['subject_name'])
                        st.markdown(f'<div style="position:absolute; width:100%; height:35px; background:{bg_c}; z-index:-1; border:1px solid #000;"></div>', unsafe_allow_html=True)
                        if st.button(f"{get_short_sub(entry['subject_name'])}\n{entry['teacher_name'].split('(')[-1].replace(')','')}", key=f"c_{day}_{p}"):
                            del st.session_state['draft_timetable'][cell_key]
                            st.rerun()
                    else:
                        if st.button(" ", key=f"c_{day}_{p}"):
                            if 'active_allot' in st.session_state:
                                a = st.session_state['active_allot']
                                # Draft Conflict Check (வேகமான சரிபார்ப்பு)
                                t_conflict = [k for k, v in st.session_state['draft_timetable'].items() if v['teacher_id'] == a['teacher_id'] and k[1] == day and k[2] == p]
                                if t_conflict: st.error("Teacher Conflict!")
                                else:
                                    st.session_state['draft_timetable'][cell_key] = {"class_name": active_class, "day_of_week": day, "period_number": p, "teacher_id": a['teacher_id'], "teacher_name": a['teacher_name'], "subject_name": a['subject_name']}
                                    st.rerun()

        st.divider()
        # 💾 FINAL SUBMIT BUTTON
        if st.button("💾 SAVE TO DATABASE (மொத்தமாகச் சேமி)", type="primary", use_container_width=True):
            with st.spinner("சேமிக்கப்படுகிறது..."):
                # 1. பழைய தரவுகளை நீக்குதல் (தேர்வு செய்யப்பட்ட வகுப்புக்கு மட்டும்)
                supabase.table("weekly_timetable").delete().eq("class_name", active_class).execute()
                # 2. புதிய தரவுகளை மொத்தமாக ஏற்றுதல் (Bulk Insert)
                bulk_data = [v for k, v in st.session_state['draft_timetable'].items() if k[0] == active_class]
                if bulk_data:
                    supabase.table("weekly_timetable").insert(bulk_data).execute()
                st.success("வெற்றிகரமாகச் சேமிக்கப்பட்டது!")
                st.cache_data.clear()
