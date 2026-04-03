import streamlit as st
import requests
import pandas as pd

st.set_page_config(page_title="Smart Roll No Management", layout="wide")

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
if not all_data: st.stop()

classes_list = all_data.get('classes', [])
students_list = all_data.get('students', [])
exams_list = all_data.get('exams', [])

st.title("📝 தானியங்கி தேர்வு எண் மேலாண்மை")

# 1. அடிப்படை விபரங்கள்
st.subheader("🆕 புதிய தேர்வு")
c1, c2 = st.columns(2)
ename = c1.text_input("தேர்வின் பெயர்").upper().strip()
ayear = c2.text_input("கல்வியாண்டு", value="2025-26")

st.divider()
sel_classes = st.multiselect("வகுப்புகளைத் தேர்ந்தெடுக்கவும் (வரிசைப்படி):", [c['class_name'] for c in classes_list])

roll_settings = {}
if sel_classes and students_list:
    df_stu = pd.DataFrame(students_list)
    
    # ஆரம்ப எண்களைச் சேமிக்க தற்காலிக மாறிகள்
    next_f_start = 1
    next_m_start = 51

    for i, cls in enumerate(sel_classes):
        st.markdown(f"#### 📍 {cls} வகுப்பு")
        
        f_count = len(df_stu[(df_stu['class_name'] == cls) & (df_stu['Gender'] == 'Female')])
        m_count = len(df_stu[(df_stu['class_name'] == cls) & (df_stu['Gender'] == 'Male')])
        
        col_f, col_m = st.columns(2)
        
        with col_f:
            # முதல் வகுப்பிற்கு மட்டும் மாற்ற அனுமதிக்கிறோம், மற்றவை தானாக மாறும்
            f_start = st.number_input(f"{cls} - பெண் தொடக்கம்", min_value=1, value=next_f_start, key=f"f_s_{cls}")
            f_end = f_start + f_count - 1 if f_count > 0 else f_start - 1
            st.success(f"பெண்கள்: {f_count} | இறுதி: **{max(0, f_end)}**")
            # அடுத்த வகுப்பிற்கு முந்தைய பிரிவின் இறுதி எண்ணிற்கு அடுத்த எண்ணை வழங்குகிறோம்
            next_f_start = f_end + 1
            
        with col_m:
            m_start = st.number_input(f"{cls} - ஆண் தொடக்கம்", min_value=1, value=next_m_start, key=f"m_s_{cls}")
            m_end = m_start + m_count - 1 if m_count > 0 else m_start - 1
            st.info(f"ஆண்கள்: {m_count} | இறுதி: **{max(0, m_end)}**")
            next_m_start = m_end + 1
            
        roll_settings[cls] = {"female": f_start, "male": m_start}
        st.write("---")

# 2. சேமிக்கும் பட்டன்
if st.button("🚀 தேர்வை உருவாக்கி எண்களைப் பதிவிடு", use_container_width=True, type="primary"):
    if ename and sel_classes:
        payload = {"action": "generate_roll_nos", "exam_name": ename, "academic_year": ayear, "roll_settings": roll_settings}
        res = requests.post(BASE_URL, json=payload)
        if res.status_code == 200:
            st.success("வெற்றிகரமாக உருவாக்கப்பட்டது!")
            st.cache_data.clear()
            st.rerun()
    else:
        st.warning("தேர்வு பெயர் மற்றும் வகுப்புகளைச் சரிபார்க்கவும்.")
