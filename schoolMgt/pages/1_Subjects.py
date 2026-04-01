import streamlit as st
import requests
import pandas as pd

BASE_URL = "https://script.google.com/macros/s/AKfycbzgqCZ6f-kwO46eZPWb_Tr7gz-JdLQSSOL8kVLzRbhPIrinmdQrGiNjNHYIYANNPO8xYg/exec"

st.set_page_config(page_title="Subjects", layout="wide")

@st.cache_data(ttl=300)
def fetch_subjects():
    try:
        res = requests.get(f"{BASE_URL}?sheet=Subjects", allow_redirects=True)
        return res.json()
    except: return []

st.title("📚 பாடங்கள் மேலாண்மை")

# படிவம்
with st.form("add_subject", clear_on_submit=True):
    name = st.text_input("பாடம் பெயர்").upper()
    etype = st.selectbox("மதிப்பீட்டு முறை", ["90 + 10", "70 + 20 + 10"])
    if st.form_submit_button("💾 சேமி"):
        if name:
            requests.post(f"{BASE_URL}?sheet=Subjects", json={"data": [{"subject_name": name, "eval_type": etype}]}, allow_redirects=True)
            st.cache_data.clear()
            st.rerun()

st.divider()

# பட்டியல்
data = fetch_subjects()
if data:
    df = pd.DataFrame(data).sort_values(by='subject_name').reset_index(drop=True)
    df.index += 1
    st.dataframe(df, use_container_width=True)
