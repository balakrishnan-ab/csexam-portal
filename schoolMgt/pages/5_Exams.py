import streamlit as st
import requests
import pandas as pd

st.set_page_config(page_title="Exams Management", layout="wide")

# 1. URL மற்றும் தரவுகள்
try:
    BASE_URL = st.secrets["BASE_URL"]
except:
    st.error("BASE_URL secrets-ல் இல்லை!")
    st.stop()

@st.cache_data(ttl=60)
def fetch_all():
    try:
        return requests.get(BASE_URL).json()
    except:
        return None

all_data = fetch_all()
classes_list = all_data.get('classes', []) if all_data else []
exams_list = all_data.get('exams', []) if all_data else []

st.title("📝 தேர்வு மற்றும் தேர்வு எண் மேலாண்மை")

# 2. புதிய தேர்வு & தானியங்கி Roll No உருவாக்கம்
with st.form("add_exam_form"):
    st.subheader("🆕 புதிய தேர்வு உருவாக்கம்")
    col1, col2 = st.columns(2)
    ename = col1.text_input("தேர்வின் பெயர் (எ.கா: ANNUAL EXAM)").upper().strip()
    ayear = col2.text_input("கல்வியாண்டு", value="2025-26")

    st.divider()
    st.write("📊 **தேர்வு எண் தொடக்க விபரம் (Roll No Settings)**")
    st.info("பெண்கள் பெயர்கள் முதலிலும், ஆண்கள் பெயர்கள் இரண்டாவதாகவும் வரிசைப்படுத்தப்படும்.")
    
    # எந்த வகுப்புகளுக்கு Roll No உருவாக்க வேண்டும்?
    sel_classes = st.multiselect("வகுப்புகளைத் தேர்ந்தெடுக்கவும்:", [c['class_name'] for c in classes_list])
    
    roll_settings = {}
    if sel_classes:
        for cls in sel_classes:
            st.write(f"📍 **{cls} வகுப்பு:**")
            c3, c4 = st.columns(2)
            # உங்கள் விருப்பப்படி பெண்கள் முதலில், பிறகு ஆண்கள்
            start_female = c3.number_input(f"{cls} - மாணவியர் தொடக்க எண்", min_value=1, value=1, key=f"f_{cls}")
            start_male = c4.number_input(f"{cls} - மாணவர் தொடக்க எண்", min_value=1, value=51, key=f"m_{cls}")
            roll_settings[cls] = {"female": start_female, "male": start_male}

    if st.form_submit_button("💾 தேர்வை உருவாக்கி Roll No ஒதுக்கு"):
        if ename and sel_classes:
            # கூகுள் ஸ்கிரிப்டிற்கு அனுப்பும் தகவல்
            payload = {
                "action": "generate_roll_nos",
                "exam_name": ename,
                "academic_year": ayear,
                "roll_settings": roll_settings
            }
            with st.spinner("தேர்வு எண்கள் உருவாக்கப்படுகிறது..."):
                res = requests.post(BASE_URL, json=payload)
                if res.status_code == 200:
                    st.success(f"தேர்வு '{ename}' உருவாக்கப்பட்டு Roll No வழங்கப்பட்டது!")
                    st.cache_data.clear()
                    st.rerun()
        else:
            st.warning("தேர்வு பெயர் மற்றும் வகுப்புகளைத் தேர்ந்தெடுக்கவும்.")

st.divider()

# 3. தற்போதுள்ள தேர்வுகள் பட்டியல்
if exams_list:
    st.subheader("📋 தேர்வுகள் பட்டியல்")
    df_exams = pd.DataFrame(exams_list)[['exam_name', 'academic_year']]
    df_exams.index = range(1, len(df_exams) + 1)
    st.table(df_exams)
