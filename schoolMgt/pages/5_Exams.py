import streamlit as st
import requests
import pandas as pd

st.set_page_config(page_title="Exams & Roll No Management", layout="wide")

try:
    BASE_URL = st.secrets["BASE_URL"]
except:
    st.error("BASE_URL missing!")
    st.stop()

@st.cache_data(ttl=60)
def fetch_everything():
    try:
        return requests.get(BASE_URL).json()
    except: return None

all_data = fetch_everything()
if not all_data:
    st.stop()

exams_list = all_data.get('exams', [])
classes_list = all_data.get('classes', [])
students_list = all_data.get('students', [])

st.title("📝 தேர்வு மற்றும் தேர்வு எண் மேலாண்மை")

# 1. அடிப்படை விபரங்கள்
st.subheader("🆕 புதிய தேர்வு உருவாக்கம்")
c1, c2 = st.columns(2)
ename = c1.text_input("தேர்வின் பெயர் (எ.கா: ANNUAL EXAM)").upper().strip()
ayear = c2.text_input("கல்வியாண்டு", value="2025-26")

st.divider()
st.markdown("### 📊 **தேர்வு எண் தொடக்க விபரம் (Roll No Settings)**")
st.info("குறிப்பு: நீங்கள் தொடக்க எண்ணை மாற்றியவுடன் இறுதி எண் உடனடியாகக் கணக்கிடப்படும்.")

# 2. வகுப்புத் தேர்வு (இது Form-க்கு வெளியே இருப்பதால் Live-ஆக வேலை செய்யும்)
sel_classes = st.multiselect("வகுப்புகளைத் தேர்ந்தெடுக்கவும்:", [c['class_name'] for c in classes_list])

roll_settings = {}
if sel_classes and students_list:
    df_stu = pd.DataFrame(students_list)
    
    for cls in sel_classes:
        st.markdown(f"#### 📍 {cls} வகுப்பு")
        m_count = len(df_stu[(df_stu['class_name'] == cls) & (df_stu['Gender'] == 'Male')])
        f_count = len(df_stu[(df_stu['class_name'] == cls) & (df_stu['Gender'] == 'Female')])
        
        c3, c4 = st.columns(2)
        with c3:
            # ⚡ Form-க்கு வெளியே இருப்பதால் இது உடனடியாக மாறும்
            f_start = st.number_input(f"{cls} - மாணவியர் தொடக்க எண்", min_value=1, value=1, key=f"f_s_{cls}")
            f_end = f_start + f_count - 1 if f_count > 0 else 0
            st.success(f"👩‍🎓 மாணவிகள்: **{f_count}** | இறுதி எண்: **{f_end if f_count > 0 else '-'}**")
        
        with c4:
            m_start = st.number_input(f"{cls} - மாணவர் தொடக்க எண்", min_value=1, value=51, key=f"m_s_{cls}")
            m_end = m_start + m_count - 1 if m_count > 0 else 0
            st.info(f"👨‍🎓 மாணவர்கள்: **{m_count}** | இறுதி எண்: **{m_end if m_count > 0 else '-'}**")
        
        roll_settings[cls] = {"female": f_start, "male": m_start}
        st.write("---")

# 3. சேமிக்கும் பட்டன் (இதை மட்டும் தனியாக வைக்கிறோம்)
if st.button("🚀 தேர்வை உருவாக்கி Roll No ஒதுக்கு", use_container_width=True, type="primary"):
    if ename and sel_classes:
        payload = {
            "action": "generate_roll_nos",
            "exam_name": ename,
            "academic_year": ayear,
            "roll_settings": roll_settings
        }
        with st.spinner("சேமிக்கப்படுகிறது..."):
            res = requests.post(BASE_URL, json=payload)
            if res.status_code == 200:
                st.success("வெற்றிகரமாக உருவாக்கப்பட்டது!")
                st.cache_data.clear()
                st.rerun()
    else:
        st.warning("தேர்வு பெயர் மற்றும் வகுப்புகளைச் சரிபார்க்கவும்.")

if exams_list:
    st.divider()
    st.subheader("📋 தேர்வுகள் பட்டியல்")
    st.table(pd.DataFrame(exams_list)[['exam_name', 'academic_year']])
