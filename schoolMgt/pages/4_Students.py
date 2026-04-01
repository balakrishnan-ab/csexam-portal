import streamlit as st
import requests

BASE_URL = "https://script.google.com/macros/s/AKfycbzgqCZ6f-kwO46eZPWb_Tr7gz-JdLQSSOL8kVLzRbhPIrinmdQrGiNjNHYIYANNPO8xYg/exec"

st.title("👨‍🎓 மாணவர்கள்")

try:
    res = requests.get(f"{BASE_URL}?sheet=Students", follow_redirects=True)
    data = res.json()
    st.dataframe(data)
except:
    st.error("தரவு பெற முடியவில்லை!")

with st.form("add_student"):
    name = st.text_input("பெயர்")
    emis = st.text_input("EMIS எண்")
    gender = st.selectbox("பாலினம்", ["M", "F"])
    cname = st.text_input("வகுப்பு")
    if st.form_submit_button("சேமி"):
        payload = {"student_name": name, "emis_no": emis, "Gender": gender, "class_name": cname}
        requests.post(f"{BASE_URL}?sheet=Students", json={"data": [payload]}, follow_redirects=True)
        st.success("மாணவர் சேர்க்கப்பட்டார்!")
        st.rerun()
