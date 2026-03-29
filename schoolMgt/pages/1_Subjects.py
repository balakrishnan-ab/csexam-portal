import streamlit as st
import requests
import pandas as pd

API_URL = "https://sheetdb.io/api/v1/sb3mxuvdynqos?sheet=Subjects"

st.title("📚 பாடம் மேலாண்மை (Subject Master)")

# 1. உள்ளீடு பகுதி
with st.expander("➕ புதிய பாடம் சேர்க்க / திருத்த", expanded=True):
    col1, col2 = st.columns(2)
    s_name = col1.text_input("பாடத்தின் பெயர்", placeholder="எ.கா: தமிழ்")
    e_type = col2.selectbox("மதிப்பீட்டு முறை", ["90 + 10", "70 + 20 + 10"])
    
    if st.button("💾 பாடத்தைச் சேமி"):
        if s_name:
            new_data = {"id": s_name, "subject_name": s_name, "eval_type": e_type}
            requests.post(API_URL, json={"data": [new_data]})
            st.success(f"{s_name} வெற்றிகரமாகச் சேமிக்கப்பட்டது!")
            st.rerun()

# 2. தரவுகளைப் பட்டியலிடுதல்
st.subheader("📋 பாடங்களின் பட்டியல்")
response = requests.get(API_URL)
data = response.json() if response.status_code == 200 else []

if data:
    df = pd.DataFrame(data)
    st.table(df[['subject_name', 'eval_type']])
    
    # நீக்கும் வசதி
    del_sub = st.selectbox("🗑️ நீக்க வேண்டிய பாடத்தைத் தேர்வு செய்க:", [d['subject_name'] for d in data])
    if st.button("🗑️ பாடத்தை நீக்கு", type="primary"):
        requests.delete(f"{API_URL}/id/{del_sub}")
        st.warning(f"{del_sub} நீக்கப்பட்டது!")
        st.rerun()
else:
    st.info("பாடங்கள் இன்னும் சேர்க்கப்படவில்லை.")
