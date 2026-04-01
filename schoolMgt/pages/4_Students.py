import streamlit as st
import requests
import pandas as pd

# உங்களது புதிய Google Web App URL
BASE_URL = "https://script.google.com/macros/s/AKfycbzgqCZ6f-kwO46eZPWb_Tr7gz-JdLQSSOL8kVLzRbhPIrinmdQrGiNjNHYIYANNPO8xYg/exec"

st.set_page_config(page_title="Students Management", layout="wide")

st.title("👨‍🎓 மாணவர்கள் மேலாண்மை")

# 1. புதிய மாணவர் சேர்க்கை படிவம் (மேலே)
st.subheader("🆕 புதிய மாணவர் சேர்க்கை")
with st.form("add_student_form", clear_on_submit=True):
    col1, col2 = st.columns(2)
    name = col1.text_input("பெயர்")
    emis = col2.text_input("EMIS எண்")
    
    col3, col4 = st.columns(2)
    gender = col3.selectbox("பாலினம்", ["M", "F"])
    cname = col4.text_input("வகுப்பு (எ.கா: 12-A1)")
    
    submit = st.form_submit_button("💾 மாணவரைச் சேமி")
    
    if submit:
        if name and emis and cname:
            payload = {"student_name": name, "emis_no": emis, "Gender": gender, "class_name": cname}
            try:
                requests.post(f"{BASE_URL}?sheet=Students", json={"data": [payload]}, allow_redirects=True)
                st.success(f"மாணவர் {name} வெற்றிகரமாகச் சேர்க்கப்பட்டார்!")
                st.rerun()
            except Exception as e:
                st.error(f"சேமிப்பதில் பிழை: {e}")
        else:
            st.warning("அனைத்து விவரங்களையும் பூர்த்தி செய்யவும்.")

st.divider()

# 2. மாணவர்கள் பட்டியல் மற்றும் தேடல் வசதி (கீழே)
st.subheader("📋 மாணவர்கள் பட்டியல்")

try:
    res = requests.get(f"{BASE_URL}?sheet=Students", allow_redirects=True)
    if res.status_code == 200:
        data = res.json()
        if isinstance(data, list) and data:
            df = pd.DataFrame(data)
            
            # வகுப்பு வாரியாகப் பார்க்கும் வசதி (Filter)
            all_classes = ["அனைத்தும்"] + sorted(df['class_name'].unique().tolist())
            selected_class = st.selectbox("வகுப்பைத் தேர்ந்தெடுக்கவும்:", all_classes)
            
            if selected_class != "அனைத்தும்":
                df_display = df[df['class_name'] == selected_class]
            else:
                df_display = df

            # மாணவர் விவரங்களை அட்டவணையாகக் காட்டுதல்
            st.dataframe(df_display, use_container_width=True)
            
            # நீக்கல் வசதி (Delete Option)
            st.write("---")
            st.subheader("🗑️ மாணவரை நீக்க")
            student_to_delete = st.selectbox("நீக்க வேண்டிய மாணவரைத் தேர்ந்தெடுக்கவும்:", df_display['student_name'].tolist())
            
            if st.button("❌ மாணவரை நீக்கு"):
                target_emis = df[df['student_name'] == student_to_delete]['emis_no'].values[0]
                # குறிப்பு: கூகுள் ஸ்கிரிப்ட்டில் 'delete' வசதி இருந்தால் மட்டுமே இது செயல்படும்
                delete_res = requests.post(f"{BASE_URL}?sheet=Students&action=delete", json={"emis_no": target_emis}, allow_redirects=True)
                st.warning(f"{student_to_delete} நீக்கப்பட்டார் (சீட்டில் சரிபார்க்கவும்).")
                st.rerun()
        else:
            st.info("மாணவர் பட்டியலில் தரவுகள் ஏதுமில்லை.")
    else:
        st.error("API-லிருந்து தரவுகளைப் பெற முடியவில்லை.")
except Exception as e:
    st.error(f"பிழை: {e}")
