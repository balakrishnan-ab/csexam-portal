import streamlit as st
import requests
import pandas as pd

# உங்களது புதிய Google Web App URL
BASE_URL = "https://script.google.com/macros/s/AKfycbzgqCZ6f-kwO46eZPWb_Tr7gz-JdLQSSOL8kVLzRbhPIrinmdQrGiNjNHYIYANNPO8xYg/exec"

st.set_page_config(page_title="Students Management", layout="wide")

st.title("👨‍🎓 மாணவர்கள்")

# 1. மாணவர் பட்டியலைப் பெறுதல்
try:
    # follow_redirects=True என்பது கூகுள் ஸ்கிரிப்டிற்கு மிகவும் அவசியம்
    res = requests.get(f"{BASE_URL}?sheet=Students", follow_redirects=True)
    if res.status_code == 200:
        data = res.json()
        if data:
            df = pd.DataFrame(data)
            # முக்கியமான தகவல்களை மட்டும் காட்ட (விருப்பப்பட்டால்)
            st.dataframe(df, use_container_width=True)
        else:
            st.info("மாணவர் பட்டியலில் தரவுகள் ஏதுமில்லை.")
    else:
        st.error(f"API பிழை: {res.status_code}")
except Exception as e:
    st.error(f"தரவு பெற முடியவில்லை! விவரம்: {e}")

st.divider()

# 2. புதிய மாணவரைச் சேர்க்கும் படிவம்
st.subheader("🆕 புதிய மாணவர் சேர்க்கை")
with st.form("add_student_form", clear_on_submit=True):
    col1, col2 = st.columns(2)
    name = col1.text_input("பெயர்")
    emis = col2.text_input("EMIS எண்")
    
    col3, col4 = st.columns(2)
    gender = col3.selectbox("பாலினம்", ["M", "F"])
    cname = col4.text_input("வகுப்பு (எ.கா: 12-A1)")
    
    submit = st.form_submit_button("💾 சேமி")
    
    if submit:
        if name and emis and cname:
            payload = {
                "student_name": name, 
                "emis_no": emis, 
                "Gender": gender, 
                "class_name": cname
            }
            try:
                # மாணவர் தாளில் (Students Sheet) சேமித்தல்
                res_post = requests.post(f"{BASE_URL}?sheet=Students", json={"data": [payload]}, follow_redirects=True)
                
                # மதிப்பெண் தாளில் (Marks Sheet) ஒரு காலியான வரியை உருவாக்குதல்
                mark_payload = {"emis_no": emis, "class_name": cname}
                requests.post(f"{BASE_URL}?sheet=Marks", json={"data": [mark_payload]}, follow_redirects=True)
                
                st.success(f"மாணவர் {name} வெற்றிகரமாகச் சேர்க்கப்பட்டார்!")
                st.rerun()
            except Exception as e:
                st.error(f"சேமிப்பதில் பிழை: {e}")
        else:
            st.warning("அனைத்து விவரங்களையும் பூர்த்தி செய்யவும்.")
