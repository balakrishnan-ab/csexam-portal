import streamlit as st
import pandas as pd
import hashlib
from supabase import create_client, Client

# --- 1. SUPABASE CONNECTION ---
try:
    url: str = st.secrets["SUPABASE_URL"]
    key: str = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(url, key)
except Exception as e:
    st.error("Connection Error!")
    st.stop()

st.set_page_config(page_title="Master Timetable", layout="wide")

# --- 🎨 COLOR GENERATOR ---
def get_color(text):
    if not text or text == "-": return "#f0f2f6"
    hash_object = hashlib.md5(text.encode()).hexdigest()
    r = (int(hash_object[:2], 16) % 100) + 180
    g = (int(hash_object[2:4], 16) % 100) + 180
    b = (int(hash_object[4:6], 16) % 100) + 180
    return f'#{r:02x}{g:02x}{b:02x}'

# --- ⚡ FETCH DATA ---
@st.cache_data(ttl=5)
def get_data():
    allot = supabase.table("staff_allotment").select("*").execute()
    time_t = supabase.table("weekly_timetable").select("*").execute()
    teachers = supabase.table("teachers").select("emis_id, full_name, short_name").order("full_name").execute()
    classes = supabase.table("classes").select("class_name").order("class_name").execute()
    return allot.data, time_t.data, teachers.data, [c['class_name'] for c in classes.data]

allot_data, time_data, teach_data, class_list = get_data()
df_time = pd.DataFrame(time_data) if time_data else pd.DataFrame()

# --- 🛠️ SIDEBAR: ஆசிரியர் தேர்வு & சில்லுகள் ---
st.sidebar.title("👨‍🏫 ஆசிரியர் தேர்வகம்")
t_options = {f"{t['full_name']} ({t['short_name']})": t for t in teach_data}
sel_teacher_label = st.sidebar.selectbox("ஆசிரியரைத் தேர்வு செய்க:", ["-- Select --"] + list(t_options.keys()))

selected_allotment = None

if sel_teacher_label != "-- Select --":
    t_info = t_options[sel_teacher_label]
    st.sidebar.markdown(f"### 🎯 {t_info['short_name']}-ன் பாடங்கள்")
    
    # இந்த ஆசிரியருக்கு ஒதுக்கப்பட்ட பாடங்களைச் சில்லுகளாகக் காட்டுதல்
    t_allots = [a for a in allot_data if a['teacher_id'] == t_info['emis_id']]
    
    for a in t_allots:
        # சில்லு (Card) வடிவமைப்பு
        card_bg = get_color(a['class_name'])
        with st.sidebar.container():
            st.markdown(f"""
                <div style="background:{card_bg}; padding:10px; border-radius:10px; border:2px solid #555; margin-bottom:10px; cursor:pointer;">
                    <div style="font-weight:bold; color:black;">{a['class_name']}</div>
                    <div style="font-size:12px; color:#333;">{a['subject_name']}</div>
                    <div style="font-size:11px; color:blue;">மொத்த பீரியட்கள்: {a['periods_per_week']}</div>
                </div>
            """, unsafe_allow_html=True)
            if st.sidebar.button(f"தேர்வு செய்க: {a['class_name']}-{a['subject_name']}", key=f"btn_{a['id']}"):
                st.session_state['active_allot'] = a
                st.sidebar.success(f"{a['class_name']} தேர்வு செய்யப்பட்டது!")

# --- 📅 MAIN VIEW: கால அட்டவணை ---
view_mode = st.radio("பார்வை முறை:", ["வகுப்பு வாரியாக", "ஆசிரியர் வாரியாக"], horizontal=True)

days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
periods = [1, 2, 3, 4, 5, 6, 7, 8]

if view_mode == "வகுப்பு வாரியாக":
    sel_class = st.selectbox("வகுப்பைத் தேர்வு செய்க:", class_list)
    st.subheader(f"🏫 {sel_class} - கால அட்டவணை")
    
    # Table Header
    cols = st.columns([1] + [1]*8)
    cols[0].write("**Day**")
    for p in periods: cols[p].write(f"**P{p}**")

    for day in days:
        row_cols = st.columns([1] + [1]*8)
        row_cols[0].write(f"**{day}**")
        
        for p in periods:
            # ஏற்கனவே உள்ள பதிவு
            entry = df_time[(df_time['class_name'] == sel_class) & 
                            (df_time['day_of_week'] == day) & 
                            (df_time['period_number'] == p)] if not df_time.empty else pd.DataFrame()
            
            with row_cols[p]:
                if not entry.empty:
                    label = entry.iloc[0]['teacher_name'].split('(')[-1].replace(')', '')
                    bg = get_color(entry.iloc[0]['subject_name'])
                    if st.button(label, key=f"p_{day}_{p}", help=entry.iloc[0]['subject_name']):
                        # நீக்கும் வசதி
                        supabase.table("weekly_timetable").delete().eq("id", entry.iloc[0]['id']).execute()
                        st.cache_data.clear()
                        st.rerun()
                else:
                    if st.button("➕", key=f"p_{day}_{p}"):
                        if 'active_allot' in st.session_state:
                            a = st.session_state['active_allot']
                            # 🚦 Conflict Check
                            conflict = df_time[(df_time['teacher_id'] == a['teacher_id']) & 
                                               (df_time['day_of_week'] == day) & 
                                               (df_time['period_number'] == p)] if not df_time.empty else pd.DataFrame()
                            
                            if not conflict.empty:
                                st.error(f"முரண்பாடு! இவர் ஏற்கனவே {conflict.iloc[0]['class_name']} வகுப்பில் உள்ளார்.")
                            else:
                                supabase.table("weekly_timetable").insert({
                                    "class_name": sel_class, "day_of_week": day, "period_number": p,
                                    "teacher_id": a['teacher_id'], "teacher_name": a['teacher_name'],
                                    "subject_name": a['subject_name']
                                }).execute()
                                st.cache_data.clear()
                                st.rerun()
                        else:
                            st.warning("முதலில் இடதுபுறம் ஒரு பாடத்தைத் தேர்வு செய்யவும்!")

elif view_mode == "ஆசிரியர் வாரியாக":
    # படம் 2 போன்ற முழுமையான ஆசிரியர் அட்டவணை (Read Only View)
    if sel_teacher_label != "-- Select --":
        t_id = t_options[sel_teacher_label]['emis_id']
        st.subheader(f"👨‍🏫 {sel_teacher_label} - தனிப்பட்ட கால அட்டவணை")
        
        t_matrix = pd.DataFrame("-", index=days, columns=periods)
        if not df_time.empty:
            t_entries = df_time[df_time['teacher_id'] == str(t_id)]
            for _, r in t_entries.iterrows():
                t_matrix.at[r['day_of_week'], r['period_number']] = r['class_name']
        
        st.table(t_matrix)
