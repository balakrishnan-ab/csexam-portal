import streamlit as st
import requests
import pandas as pd

# 1. பக்க அமைப்பு
st.set_page_config(page_title="Exams & Roll No Management", layout="wide")

# 2. URL மற்றும் தரவுகள் பெறுதல்
try:
    BASE_URL = st.secrets["BASE_URL"]
except:
    st.error("BASE_URL secrets-ல் கண்டறியப்படவில்லை!")
    st.stop()

@st.cache_data(ttl=60)
def fetch_everything():
    try:
        res = requests.get(BASE_URL).json()
        return res
    except Exception as e:
        return None

all_data = fetch_everything()

if not all_data:
    st.warning("கூகுள் சீட்டில் இருந்து தகவல்கள் வரவில்லை. URL-ஐச் சரிபார்க்கவும்.")
    st.stop()

# தரவுகளைப் பிரித்தல்
exams_list = all_data.get('exams', [])
classes_list = all_data.get('classes', [])
students_list = all_data.get('students', [])

st.title("📝 தேர்வு மற்றும் தேர்வு எண் மேலாண்மை")

# 3. புதிய தேர்வு உருவாக்கம் & தானியங்கி Roll No
with st.form("add_exam_form"):
    st.subheader("🆕 புதிய தேர்வு உருவாக்கம்")
    col1, col2 = st.columns(2)
    ename = col1.text_input("தேர்வின் பெயர் (எ.கா: ANNUAL EXAM)").upper().strip()
    ayear = col2.text_input("கல்வியாண்டு", value="2025-26")

    st.divider()
    st.markdown("### 📊 **தேர்வு எண் தொடக்க விபரம் (Roll No Settings)**")
    
    # எந்தெந்த வகுப்புகளுக்கு தேர்வு எண் உருவாக்க வேண்டும்?
    sel_classes = st.multiselect("வகுப்புகளைத் தேர்ந்தெடுக்கவும்:", [c['class_name'] for c in classes_list])
    
    roll_settings = {}
    if sel_classes and students_list:
        df_stu = pd.DataFrame(students_list)
        
        for cls in sel_classes:
            st.write(f"📍 **{cls} வகுப்பு விபரம்:**")
            
            # அந்த வகுப்பில் உள்ள ஆண்/பெண் எண்ணிக்கை
            m_students = df_stu[(df_stu['class_name'] == cls) & (df_stu['Gender'] == 'Male')]
            f_students = df_stu[(df_stu['class_name'] == cls) & (df_stu['Gender'] == 'Female')]
            
            m_count = len(m_students)
            f_count = len(f_students)
            
            c3, c4 = st.columns(2)
            
            # மாணவிகள் (Female) - இறுதி எண் கணக்கீடு
            with c3:
                f_start = st.number_input(f"{cls} - மாணவியர் தொடக்க எண்", min_value=1, value=1, key=f"f_s_{cls}")
                f_end = f_start + f_count - 1 if f_count > 0 else 0
                st.write(f"👩‍🎓 மாணவிகள்: **{f_count}** | இறுதி எண்: :blue[**{f_end if f_count > 0 else '-'}**]")
            
            # மாணவர்கள் (Male) - இறுதி எண் கணக்கீடு
            with c4:
                m_start = st.number_input(f"{cls} - மாணவர் தொடக்க எண்", min_value=1, value=51, key=f"m_s_{cls}")
                m_end = m_start + m_count - 1 if m_count > 0 else 0
                st.write(f"👨‍🎓 மாணவர்கள்: **{m_count}** | இறுதி எண்: :blue[**{m_end if m_count > 0 else '-'}**]")
            
            roll_settings[cls] = {"female": f_start, "male": m_start}
            st.write("---")

    # 4. சேமிக்கும் பட்டன்
    submit = st.form_submit_button("🚀 தேர்வை உருவாக்கி Roll No ஒதுக்கு", use_container_width=True)
    
    if submit:
        if ename and sel_classes:
            payload = {
                "action": "generate_roll_nos",
                "exam_name": ename,
                "academic_year": ayear,
                "roll_settings": roll_settings
            }
            try:
                res = requests.post(BASE_URL, json=payload)
                if res.status_code == 200:
                    st.success(f"தேர்வு '{ename}' உருவாக்கப்பட்டது!")
                    st.cache_data.clear()
                    st.rerun()
                else:
                    st.error("சேமிப்பதில் பிழை ஏற்பட்டது.")
            except Exception as e:
                st.error(f"Error: {e}")
        else:
            st.warning("தேர்வு பெயர் மற்றும் வகுப்புகளைத் தேர்ந்தெடுக்கவும்.")

st.divider()

# 5. தேர்வுகள் பட்டியல்
if exams_list:
    st.subheader("📋 தேர்வுகள் பட்டியல்")
    df_exams = pd.DataFrame(exams_list)[['exam_name', 'academic_year']]
    df_exams.index = range(1, len(df_exams) + 1)
    st.table(df_exams)
