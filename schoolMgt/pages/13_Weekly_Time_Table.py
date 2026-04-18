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

# CSS for compact grid and small cards
st.markdown("""
    <style>
    .stButton > button { width: 100%; height: 45px; padding: 0px; font-size: 10px; border-radius: 2px; }
    .allot-card { padding: 5px; border-radius: 4px; border: 1px solid #ccc; margin-bottom: 5px; text-align: center; cursor: pointer; }
    </style>
    """, unsafe_allow_html=True)

def get_color(text):
    if not text: return "#ffffff"
    hash_obj = hashlib.md5(text.encode()).hexdigest()
    return f'#{(int(hash_obj[:2],16)%50)+200:02x}{(int(hash_obj[2:4],16)%50)+200:02x}{(int(hash_obj[4:6],16)%50)+200:02x}'

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

# --- 🏗️ LAYOUT (3 பிரிவுகள்) ---
# 1. வகுப்புத் தேர்வு | 2. அட்டவணை Grid | 3. ஆசிரியர் & ஒதுக்கீட்டுச் சில்லுகள்
main_col, side_col = st.columns([1.2, 0.8])

with side_col:
    st.subheader("👨‍🏫 ஆசிரியர் & ஒதுக்கீடு")
    t_opts = {f"{t['full_name']} ({t['short_name']})": t for t in teach_data}
    sel_teacher = st.selectbox("ஆசிரியர்:", ["-- Select --"] + list(t_opts.keys()))
    
    if sel_teacher != "-- Select --":
        t_info = t_opts[sel_teacher]
        t_allots = [a for a in allot_data if a['teacher_id'] == t_info['emis_id']]
        
        for a in t_allots:
            # 🔍 ஏற்கனவே எத்தனை முறை பயன்படுத்தப்பட்டுள்ளது என எண்ணுதல்
            used_count = len(df_time[(df_time['teacher_id'] == a['teacher_id']) & 
                                     (df_time['class_name'] == a['class_name']) & 
                                     (df_time['subject_name'] == a['subject_name'])]) if not df_time.empty else 0
            
            remaining = a['periods_per_week'] - used_count
            bg = get_color(a['subject_name'])
            
            # சிறிய சில்லு (Card)
            st.markdown(f"""
                <div style="background:{bg}; border:1px solid #999; padding:5px; border-radius:5px; text-align:center;">
                    <div style="font-size:11px; font-weight:bold;">{a['class_name']}</div>
                    <div style="font-size:9px;">{a['subject_name']}</div>
                    <div style="font-size:10px; color:{'red' if remaining <= 0 else 'blue'};">மீதம்: {remaining}</div>
                </div>
            """, unsafe_allow_html=True)
            
            if remaining > 0:
                if st.button(f"பயன்படுத்து: {a['class_name']}", key=f"src_{a['id']}"):
                    st.session_state['active_allot'] = a
            else:
                st.write("🚫 முடிந்தது")

with main_col:
    st.subheader("📅 கால அட்டவணை")
    sel_class = st.selectbox("வகுப்பு தேர்வு:", ["-- Select --"] + class_list, label_visibility="collapsed")
    
    if sel_class != "-- Select --":
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
        periods = [1, 2, 3, 4, 5, 6, 7, 8]
        
        # Grid Header
        h_cols = st.columns([1] + [1]*8)
        for i, h in enumerate(["Day"] + [f"P{p}" for p in periods]): h_cols[i].markdown(f"**{h}**")

        for day in days:
            r_cols = st.columns([1] + [1]*8)
            r_cols[0].markdown(f"**{day}**")
            
            for p in periods:
                entry = df_time[(df_time['class_name'] == sel_class) & 
                                (df_time['day_of_week'] == day) & 
                                (df_time['period_number'] == p)] if not df_time.empty else pd.DataFrame()
                
                with r_cols[p]:
                    if not entry.empty:
                        # ஏற்கனவே பாடம் உள்ளது - நீக்கலாம்
                        sub = entry.iloc[0]['subject_name']
                        t_short = entry.iloc[0]['teacher_name'].split('(')[-1].replace(')', '')
                        if st.button(f"{sub}\n{t_short}", key=f"p_{day}_{p}", help="நீக்க கிளிக் செய்க"):
                            supabase.table("weekly_timetable").delete().eq("id", entry.iloc[0]['id']).execute()
                            st.cache_data.clear()
                            st.rerun()
                    else:
                        # காலியாக உள்ளது - சேர்க்கலாம்
                        if st.button("➕", key=f"p_{day}_{p}"):
                            if 'active_allot' in st.session_state:
                                a = st.session_state['active_allot']
                                
                                # 🚦 Conflict Check (ஆசிரியர் வேறு வகுப்பில் இருக்கிறாரா?)
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
                            else:
                                st.warning("முதலில் வலதுபுறம் பாடம் தேர்வு செய்க!")
