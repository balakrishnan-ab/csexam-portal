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

# CSS: நேர்த்தியான எக்செல் கட்டம்
st.markdown("""
    <style>
    .grid-label { font-size: 13px; font-weight: bold; background: #E0E0E0; height: 40px; display: flex; align-items: center; justify-content: center; border: 1px solid #000; }
    /* Selectbox-ஐ எக்செல் கட்டம் போல மாற்ற */
    div[data-testid="stSelectbox"] > div { border: none !important; border-radius: 0px !important; }
    div[data-testid="stSelectbox"] { border: 1px solid #000; margin: 0px !important; }
    /* வலதுபுற விவரம் */
    .info-box { border-left: 5px solid #007bff; background: #f9f9f9; padding: 10px; margin-bottom: 5px; border-top: 1px solid #ddd; border-right: 1px solid #ddd; border-bottom: 1px solid #ddd; }
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

if 'teacher_tt' not in st.session_state:
    st.session_state.teacher_tt = {}

# --- 🏗️ LAYOUT ---
st.title("👨‍🏫 ஆசிரியர் கால அட்டவணை மேலாண்மை")

main_col, side_col = st.columns([1.5, 0.5])

with main_col:
    t_opts = {f"{t['full_name']} ({t['short_name']})": t for t in teach_list}
    sel_teacher_label = st.selectbox("ஆசிரியரைத் தேர்வு செய்க:", ["-- Select Teacher --"] + list(t_opts.keys()))

if sel_teacher_label != "-- Select Teacher --":
    sel_t = t_opts[sel_teacher_label]
    t_id = sel_t['emis_id']
    t_allots = [a for a in allot_data if a['teacher_id'] == t_id]
    
    # கார்டுகளில் விவரம் (வலதுபுறம்)
    with side_col:
        st.markdown("##### 📝 ஒதுக்கீடு விவரம்")
        for a in t_allots:
            st.markdown(f"""<div class='info-box'><b>{a['class_name']}</b><br><small>{a['subject_name']}</small><br><span style='color:blue;'>வாராந்திர பீரியட்கள்: {a['periods_per_week']}</span></div>""", unsafe_allow_html=True)

    # 1. கம்பைன் வகுப்புகளுக்கான ஆப்ஷன்களை உருவாக்குதல்
    cls_list = sorted([a['class_name'] for a in t_allots])
    # தனி வகுப்புகள் + கம்பைன் ஆப்ஷன் (உதாரணம்: "11-A & 11-B")
    dropdown_options = [" "] + cls_list
    if len(cls_list) > 1:
        dropdown_options.append(" & ".join(cls_list)) # கம்பைன் வகுப்பு ஆப்ஷன்

    # 2. தரவுகளை ஏற்றுதல்
    if st.session_state.get('last_t_id') != t_id:
        st.session_state.teacher_tt = {}
        st.session_state.last_t_id = t_id
        for e in db_list:
            if e['teacher_id'] == t_id:
                st.session_state.teacher_tt[(e['day_of_week'], e['period_number'])] = e['class_name']

    # 3. கால அட்டவணை கிரிட்
    with main_col:
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
        periods = range(1, 9)

        # Headers
        h_cols = st.columns([0.8] + [1]*8)
        h_cols[0].markdown("<div class='grid-label'>Day</div>", unsafe_allow_html=True)
        for p in periods: h_cols[p].markdown(f"<div class='grid-label'>{p}</div>", unsafe_allow_html=True)

        for day in days:
            r_cols = st.columns([0.8] + [1]*8)
            r_cols[0].markdown(f"<div class='grid-label' style='background:#f9f9f9;'>{day[:3]}</div>", unsafe_allow_html=True)
            
            for p in periods:
                key = (day, p)
                current_val = st.session_state.teacher_tt.get(key, " ")
                
                # கம்பைன் வகுப்புகள் டேட்டாபேஸில் தனித்தனியாக இருக்கும், ஆனால் திரையில் "A & B" எனத் தெரிய வேண்டும்
                with r_cols[p]:
                    sel = st.selectbox(f"sel_{day}_{p}", dropdown_options, 
                                       index=dropdown_options.index(current_val) if current_val in dropdown_options else 0,
                                       key=f"sb_{day}_{p}", label_visibility="collapsed")
                    
                    if sel != current_val:
                        st.session_state.teacher_tt[key] = sel
                        st.rerun()

        st.divider()
        if st.button(f"🚀 {sel_t['short_name']} அட்டவணையைச் சேமி", type="primary", use_container_width=True):
            with st.spinner("சேமிக்கப்படுகிறது..."):
                supabase.table("weekly_timetable").delete().eq("teacher_id", t_id).execute()
                new_entries = []
                for (d, pn), cls_val in st.session_state.teacher_tt.items():
                    if cls_val != " ":
                        # "11-A & 11-B" என்பதைத் தனித்தனியாகப் பிரித்தல்
                        selected_classes = cls_val.split(" & ")
                        for cls in selected_classes:
                            staff_info = next((a for a in t_allots if a['class_name'] == cls), None)
                            if staff_info:
                                new_entries.append({
                                    "class_name": cls, "day_of_week": d, "period_number": pn,
                                    "teacher_id": t_id, "teacher_name": f"{sel_t['full_name']} ({sel_t['short_name']})",
                                    "subject_name": staff_info['subject_name']
                                })
                if new_entries:
                    supabase.table("weekly_timetable").insert(new_entries).execute()
                st.success("வெற்றிகரமாகச் சேமிக்கப்பட்டது!")
                st.cache_data.clear()
