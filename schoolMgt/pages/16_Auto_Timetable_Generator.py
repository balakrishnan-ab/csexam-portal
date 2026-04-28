import streamlit as st
import pandas as pd
from supabase import create_client, Client

st.title("⚙️ ஆட்டோ-ஜெனரேட் டைம்டேபிள் - எடிட்டர்")

# 1. தரவுத்தள இணைப்பு (Supabase)
try:
    url, key = st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(url, key)
except:
    st.error("Connection Error!")
    st.stop()

# 2. தரவைப் பெறும் பங்க்ஷன்
@st.cache_data(ttl=5)
def get_allotment_data():
    allot = supabase.table("staff_allotment").select("*").execute()
    return allot.data

# பட்டனுக்கு முன்பே தரவை பெற்று விடுங்கள்
allot_data = get_allotment_data() 

# 3. 'அனைவருக்கும் ஒதுக்கீடு' பட்டன்
if st.button("🤖 அனைவருக்கும் தானாக நிரப்பு (Auto-Assign All)"):
    new_df = pd.DataFrame(index=["Mon", "Tue", "Wed", "Thu", "Fri", "Sat"], 
                          columns=[str(i) for i in range(1, 9)]).fillna("-")
    
    all_tasks = []
    for a in allot_data:
        all_tasks.extend([a['class_name']] * int(a['periods_per_week']))
    
    idx = 0
    days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
    periods = [str(i) for i in range(1, 9)]
    
    for d in days:
        for p in periods:
            if idx < len(all_tasks):
                new_df.at[d, p] = all_tasks[idx]
                idx += 1
    
    st.session_state.temp_tt = new_df
    st.rerun()

# 4. Tabs மற்றும் Editor... (இதற்குப் பிறகு உங்கள் பழைய குறியீட்டைச் சேர்க்கவும்)
if 'temp_tt' not in st.session_state:
    st.session_state.temp_tt = pd.DataFrame(index=["Mon", "Tue", "Wed", "Thu", "Fri", "Sat"], 
                                            columns=[str(i) for i in range(1, 9)]).fillna("-")

tab1, tab2 = st.tabs(["👨‍🏫 ஆசிரியர் வாரியாக", "🏫 வகுப்பு வாரியாக"])
# ... மீதமுள்ள tab குறியீடுகள் ...
# தற்காலிக தரவு (Example Data)
if 'temp_tt' not in st.session_state:
    st.session_state.temp_tt = pd.DataFrame(index=["Mon", "Tue", "Wed", "Thu", "Fri"], columns=[str(i) for i in range(1, 9)]).fillna("-")

with tab1:
  st.title("👨‍🏫 அனைத்து ஆசிரியர்கள் கால அட்டவணை")

# 1. மாஸ்டர் டேபிளை உருவாக்குதல் (ஆசிரியர்கள் x வேளைகள்)
# teachers_list என்பது உங்கள் தரவுத்தளத்தில் உள்ள ஆசிரியர்களின் பட்டியல்
if 'master_tt' not in st.session_state:
    st.session_state.master_tt = pd.DataFrame(
        index=teachers_list, 
        columns=["Mon_1", "Mon_2", "Tue_1", "Tue_2"] # இதை விரிவுபடுத்தலாம்
    ).fillna("-")

# 2. ஒரே எடிட்டரில் அனைத்தையும் காட்ட
edited_master_tt = st.data_editor(
    st.session_state.master_tt,
    use_container_width=True,
    key="master_editor"
)

# 3. சேமிக்கும்போது வகுப்பு வாரியாகப் பிரித்தல்
if st.button("💾 அனைத்தையும் சேமி"):
    # இங்கே இந்த மாஸ்டர் டேபிளை வகுப்பு வாரியாகப் பிரிக்கும் தர்க்கம் (Logic)
    # பின்னர் Supabase-க்கு அனுப்பவும்
    st.success("அனைத்து ஆசிரியர்களின் அட்டவணையும் சேமிக்கப்பட்டது!")

with tab2:
    st.subheader("வகுப்பு வாரியான தற்காலிக அட்டவணை")
    # key="class_editor" என்று கொடுக்கவும்
    edited_class_tt = st.data_editor(
        st.session_state.temp_tt, 
        use_container_width=True, 
        key="class_editor"
    )
# சேமிப்பு மற்றும் கைவிடும் பட்டன்கள்
col1, col2 = st.columns([1, 1])
with col1:
    if st.button("💾 சரி (Save)"):
        # இங்கே தரவுத்தளத்தில் (Supabase) சேமிக்கும் தர்க்கத்தை எழுதவும்
        st.session_state.temp_tt = edited_teacher_tt # தற்காலிக தரவை அப்டேட் செய்யவும்
        st.success("அட்டவணை வெற்றிகரமாகச் சேமிக்கப்பட்டது!")
with col2:
    if st.button("❌ கைவிடு (Discard)"):
        # தற்காலிக தரவை நீக்கிவிடலாம்
        st.warning("மாற்றங்கள் கைவிடப்பட்டன!")
        st.rerun()

st.info("குறிப்பு: 'சரி' கொடுத்தால் மட்டுமே மாற்றங்கள் தரவுத்தளத்தில் பதிவாகும்.")
