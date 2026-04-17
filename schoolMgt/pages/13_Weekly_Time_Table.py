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
    st.error("Secrets missing!")
    st.stop()

st.set_page_config(page_title="Master Timetable", layout="wide")

def get_color(text):
    if not text or text == "-": return "#ffffff"
    hash_object = hashlib.md5(text.encode()).hexdigest()
    return f'#{(int(hash_object[:2], 16) % 100) + 155:02x}{(int(hash_object[2:4], 16) % 100) + 155:02x}{(int(hash_object[4:6], 16) % 100) + 155:02x}'

# --- ⚡ FETCH DATA ---
@st.cache_data(ttl=5)
def get_master_data():
    allotments = supabase.table("staff_allotment").select("*").execute()
    timetable = supabase.table("weekly_timetable").select("*").execute()
    teachers = supabase.table("teachers").select("emis_id, full_name, short_name").execute()
    return allotments.data, timetable.data, teachers.data

allot_data, time_data, teach_data = get_master_data()
df_time = pd.DataFrame(time_data) if time_data else pd.DataFrame()

st.title("🏫 பள்ளி முதன்மை கால அட்டவணை (Master View)")

# --- 🛠️ UI OPTIONS ---
view_mode = st.radio("பார்வை முறை:", ["வகுப்பு வாரியாக", "ஆசிரியர் வாரியாக (படம் 2 போல்)"], horizontal=True)

days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
periods = [1, 2, 3, 4, 5, 6, 7, 8]

if view_mode == "ஆசிரியர் வாரியாக (படம் 2 போல்)":
    # ஆசிரியர்களைத் தேர்வு செய்தல் (ஒரே நேரத்தில் 3 ஆசிரியர்கள் வரை பார்க்கலாம்)
    t_options = {f"{t['full_name']} ({t['short_name']})": t['emis_id'] for t in teach_data}
    selected_teachers = st.multiselect("ஆசிரியர்களைத் தேர்வு செய்க:", list(t_options.keys()), default=list(t_options.keys())[:3])
    
    if selected_teachers:
        t_cols = st.columns(len(selected_teachers))
        
        for idx, t_label in enumerate(selected_teachers):
            t_id = t_options[t_label]
            with t_cols[idx]:
                st.markdown(f"### 👨‍🏫 {t_label}")
                
                # இந்த ஆசிரியருக்கான தனி அட்டவணை உருவாக்குதல்
                t_matrix = pd.DataFrame("-", index=days, columns=periods)
                
                if not df_time.empty:
                    t_entries = df_time[df_time['teacher_id'] == str(t_id)]
                    for _, row in t_entries.iterrows():
                        if row['day_of_week'] in days and row['period_number'] in periods:
                            t_matrix.at[row['day_of_week'], row['period_number']] = row['class_name']
                
                # வண்ணம் சேர்த்துக் காட்டுதல்
                st.table(t_matrix)
                
                # அந்த ஆசிரியருக்கு ஒதுக்கப்பட்ட மொத்த பீரியட்கள்
                total_p = t_entries.shape[0] if not df_time.empty else 0
                st.metric("மொத்த பாடவேளைகள்", total_p)

else:
    # பழைய வகுப்பு வாரியான முறை
    classes = sorted(list(set([a['class_name'] for a in allot_data])))
    sel_class = st.selectbox("வகுப்பைத் தேர்வு செய்க:", classes)
    
    if sel_class:
        st.subheader(f"🏫 {sel_class} - கால அட்டவணை")
        
        # Grid View for Input
        for day in days:
            st.write(f"**{day}**")
            cols = st.columns(8)
            for p in periods:
                with cols[p-1]:
                    # தற்போதுள்ள பதிவு
                    match = df_time[(df_time['class_name'] == sel_class) & 
                                    (df_time['day_of_week'] == day) & 
                                    (df_time['period_number'] == p)] if not df_time.empty else pd.DataFrame()
                    
                    label = "Empty" if match.empty else match.iloc[0]['teacher_name'].split('(')[-1].replace(')', '')
                    
                    with st.popover(f"P{p}\n{label}", use_container_width=True):
                        st.write(f"{day} - P{p}")
                        # இங்கு தேர்வு செய்யும் வசதி (முந்தைய குறியீட்டில் இருந்தது போல்)
                        st.info("இங்கு ஆசிரியரைத் தேர்வு செய்யலாம்.")
