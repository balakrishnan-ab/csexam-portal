import streamlit as st
import requests

# API URL
EXAM_API = "https://sheetdb.io/api/v1/sb3mxuvdynqos?sheet=Exams"

st.title("🛠️ API சோதனை")

try:
    res = requests.get(EXAM_API)
    st.write(f"API பதில் குறியீடு (Status): {res.status_code}")
    
    data = res.json()
    st.write("கிடைத்த தரவுகள்:")
    st.write(data)
    
    if isinstance(data, list) and len(data) > 0:
        st.success("Exams API வெற்றிகரமாக வேலை செய்கிறது!")
        st.write(f"தேர்வு பெயர்: {data[0]['exam_name']}")
    else:
        st.warning("API பதில் கிடைக்கிறது, ஆனால் அதில் தரவுகள் ஏதுமில்லை.")

except Exception as e:
    st.error(f"முழுமையான பிழை விவரம்: {e}")
