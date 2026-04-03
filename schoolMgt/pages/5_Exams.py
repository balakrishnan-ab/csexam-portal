import streamlit as st
import requests
import pandas as pd

st.set_page_config(page_title="Sequential Roll No Generator", layout="wide")

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

st.title("📝 தானியங்கி தொடர் தேர்வு எண் மேலாண்மை")

# 1. அடிப்படை விபரங்கள்
st.subheader("🆕 புதிய தேர்வு உருவாக்கம்")
c1, c2 = st.columns(2)
ename = c1.text_input("தேர்வின் பெயர்").upper().strip()
ayear = c2.text_input("கல்வியாண்டு", value="2025-26")

st.divider()
# வரிசைப்படி தேர்ந்தெடுக்கவும்
sel_classes = st.multiselect("வகுப்புகளை வரிசைப்படி தேர்ந்தெடுக்கவும் (எ.கா: 10-A, பிறகு 10-B):", 
                             [c['class_name'] for c in classes_list])

roll_settings = {}

if sel_classes and students_list:
    df_stu = pd.DataFrame(students_list)
    
    st.markdown("### 🔢 ஆரம்ப எண் தேர்வு")
    # ஆரம்ப எண் 1-ல் இருந்து தொடங்குகிறது
    start_num = st.number_input("முதல் வகுப்பின் முதல் மாணவிக்கான ஆரம்ப எண்:", min_value=1, value=1)
    
    current_num = start_num
    st.write("---")
    
    # ⚡ மிக முக்கியமான லாஜிக்: ஒரு பிரிவின் ஆண்கள் முடிந்ததும் அடுத்த பிரிவின் பெண்கள் தொடங்குதல்
    for cls in sel_classes:
        st.markdown(f"#### 📍 {cls} வகுப்பு")
        
        # அந்த வகுப்பில் உள்ள பெண்கள் மற்றும் ஆண்கள்
        f_count = len(df_stu[(df_stu['class_name'] == cls) & (df_stu['Gender'] == 'Female')])
        m_count = len(df_stu[(df_stu['class_name'] == cls) & (df_stu['Gender'] == 'Male')])
        
        c_f, c_m = st.columns(2)
        
        # 1. பெண்களுக்கான எண்கள் (முதலில்)
        with c_f:
            f_start = current_num
            f_end = f_start + f_count - 1 if f_count > 0 else f_start - 1
            st.success(f"👩‍🎓 மாணவிகள் ({f_count}): **{f_start} - {max(0, f_end)}**")
            # அடுத்த எண் ஆண்களுக்குச் செல்லும்
            if f_count > 0: current_num = f_end + 1
            
        # 2. ஆண்களுக்கான எண்கள் (பெண்களுக்கு அடுத்து)
        with c_m:
            m_start = current_num
            m_end = m_start + m_count - 1 if m_count > 0 else m_start - 1
            st.info(f"👨‍🎓 மாணவர்கள் ({m_count}): **{m_start} - {max(0, m_end)}**")
            # அடுத்த எண் அடுத்த பிரிவின் பெண்களுக்குச் செல்லும்
            if m_count > 0: current_num = m_end + 1
        
        # இறுதித் தகவலை சேமித்தல்
        roll_settings[cls] = {"female": f_start, "male": m_start}
        st.write("---")

# 2. சேமிக்கும் பட்டன்
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
