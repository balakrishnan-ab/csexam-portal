import streamlit as st
import requests
import pandas as pd

CLASS_API = "https://sheetdb.io/api/v1/sb3mxuvdynqos?sheet=Classes"
GROUP_API = "https://sheetdb.io/api/v1/sb3mxuvdynqos?sheet=Groups"

st.title("🏫 வகுப்பு மேலாண்மை (Class Master)")

# பிரிவுகளைப் பெறுதல்
groups = requests.get(GROUP_API).json()
group_list = [g['group_name'] for g in groups] if isinstance(groups, list) else []

with st.expander("➕ புதிய வகுப்பைச் சேர்க்க", expanded=True):
    c_name = st.text_input("வகுப்பு (எ.கா: 12-A1)")
    c_group = st.selectbox("ஒதுக்கப்பட வேண்டிய பிரிவு", group_list)
    c_med = st.radio("பயிற்று மொழி", ["தமிழ் வழி", "ஆங்கில வழி"], horizontal=True)
    
    if st.button("➕ வகுப்பை உருவாக்கு"):
        payload = {"class_name": c_name, "group_name": c_group, "medium": c_med}
        requests.post(CLASS_API, json={"data": [payload]})
        st.success("வகுப்பு சேர்க்கப்பட்டது!")
        st.rerun()

# பட்டியல்
st.subheader("🏫 வகுப்புகளின் விவரம்")
c_data = requests.get(CLASS_API).json()
if c_data:
    st.table(pd.DataFrame(c_data)[['class_name', 'group_name', 'medium']])
    del_cls = st.selectbox("🗑️ நீக்க வேண்டிய வகுப்பைத் தேர்வு செய்க:", [c['class_name'] for c in c_data])
    if st.button("🗑️ வகுப்பை நீக்கு"):
        requests.delete(f"{CLASS_API}/class_name/{del_cls}")
        st.rerun()
