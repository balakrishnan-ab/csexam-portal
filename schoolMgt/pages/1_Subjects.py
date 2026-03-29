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
    # தலைப்பு வரிசை (Header Row)
    h_col1, h_col2, h_col3 = st.columns([3, 2, 2])
    h_col1.markdown("**பாடத்தின் பெயர்**")
    h_col2.markdown("**மதிப்பீட்டு முறை**")
    h_col3.markdown("**செயல்கள்**")
    st.divider()

    for sub in data:
        col1, col2, col3 = st.columns([3, 2, 2])
        
        # பாட விவரங்கள்
        col1.text(sub.get('subject_name', ''))
        col2.text(sub.get('eval_type', ''))
        
        # வலது ஓரத்தில் குறும்படங்கள்
        action_cols = col3.columns(2)
        
        # 📝 பதிப்பி (Edit) பட்டன்
        if action_cols[0].button("📝", key=f"edit_{sub['subject_name']}", help="திருத்த"):
            st.info(f"{sub['subject_name']} - விவரங்களை மேலே உள்ள பெட்டியில் மாற்றி மீண்டும் சேமிக்கவும்.")
            # குறிப்பு: இங்கு திருத்துவதற்கான தரவுகளை மேலே உள்ள input பெட்டிகளுக்கு கொண்டு செல்லலாம்
            
        # 🗑️ நீக்கு (Delete) பட்டன்
        if action_cols[1].button("🗑️", key=f"del_{sub['subject_name']}", help="நீக்க"):
            requests.delete(f"{API_URL}/id/{sub['subject_name']}")
            st.warning(f"{sub['subject_name']} நீக்கப்பட்டது!")
            st.rerun()
else:
    st.info("பாடங்கள் இன்னும் சேர்க்கப்படவில்லை.")
