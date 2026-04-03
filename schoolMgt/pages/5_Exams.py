import streamlit as st
import requests
import pandas as pd

# 1. பக்க அமைப்பு
st.set_page_config(page_title="Smart Roll No Generator", layout="wide")

# 2. URL மற்றும் தரவுகள்
try:
    BASE_URL = st.secrets["BASE_URL"]
except:
    st.error("BASE_URL secrets-ல் இல்லை!")
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

# 3. அடிப்படை விபரங்கள்
st.subheader("🆕 புதிய தேர்வு உருவாக்கம்")
c1, c2 = st.columns(2)
ename = c1.text_input("தேர்வின் பெயர்").upper().strip()
ayear = c2.text_input("கல்வியாண்டு", value="2025-26")

st.divider()
sel_classes = st.multiselect("வகுப்புகளை வரிசைப்படி தேர்ந்தெடுக்கவும்:", [c['class_name'] for c in classes_list])

roll_settings = {}

if sel_classes and students_list:
    df_stu = pd.DataFrame(students_list)
    
    # ⚡ மிக முக்கியமான பகுதி: தொடக்க எண்களைத் தீர்மானித்தல்
    # முதல் வகுப்பிற்கான தொடக்க எண்களை மட்டும் ஆசிரியரிடம் கேட்கிறோம்
    st.markdown("### 🔢 எண்களை வரிசைப்படுத்துதல்")
    col_init_f, col_init_m = st.columns(2)
    
    # Session State-ல் ஆரம்ப மதிப்புகளைச் சேமித்தல்
    if 'init_f' not in st.session_state: st.session_state.init_f = 1
    if 'init_m' not in st.session_state: st.session_state.init_m = 51

    start_f = col_init_f.number_input("அனைத்து பிரிவுகளுக்கும் பெண்களுக்கான ஆரம்ப எண்:", min_value=1, value=st.session_state.init_f)
    start_m = col_init_m.number_input("அனைத்து பிரிவுகளுக்கும் ஆண்களுக்கான ஆரம்ப எண்:", min_value=1, value=st.session_state.init_m)

    current_f = start_f
    current_m = start_m

    st.write("---")
    
    # ⚡ தானாகவே அனைத்து பிரிவுகளுக்கும் எண்களைக் கணக்கிடுதல்
    for cls in sel_classes:
        st.markdown(f"#### 📍 {cls} வகுப்பு")
        
        f_count = len(df_stu[(df_stu['class_name'] == cls) & (df_stu['Gender'] == 'Female')])
        m_count = len(df_stu[(df_stu['class_name'] == cls) & (df_stu['Gender'] == 'Male')])
        
        c_f, c_m = st.columns(2)
        
        # பெண்களுக்கான கணக்கீடு
        with c_f:
            f_end = current_f + f_count - 1 if f_count > 0 else current_f - 1
            st.success(f"பெண்: {current_f} முதல் {max(0, f_end)} வரை (மொத்தம்: {f_count})")
            roll_settings[cls] = {"female": current_f}
            if f_count > 0: current_f = f_end + 1 # அடுத்த பிரிவிற்கு அடுத்த எண்
            
        # ஆண்களுக்கான கணக்கீடு
        with c_m:
            m_end = current_m + m_count - 1 if m_count > 0 else current_m - 1
            st.info(f"ஆண்: {current_m} முதல் {max(0, m_end)} வரை (மொத்தம்: {m_count})")
            roll_settings[cls]["male"] = current_m
            if m_count > 0: current_m = m_end + 1 # அடுத்த பிரிவிற்கு அடுத்த எண்
        
        st.write("---")

# 4. சேமிக்கும் பட்டன்
if st.button("🚀 தேர்வை உருவாக்கி எண்களைப் பதிவிடு", use_container_width=True, type="primary"):
    if ename and sel_classes:
        payload = {
            "action": "generate_roll_nos", 
            "exam_name": ename, 
            "academic_year": ayear, 
            "roll_settings": roll_settings
        }
        res = requests.post(BASE_URL, json=payload)
        if res.status_code == 200:
            st.success("வெற்றிகரமாக உருவாக்கப்பட்டது!")
            st.cache_data.clear()
            st.rerun()
    else:
        st.warning("விபரங்களைச் சரிபார்க்கவும்.")
