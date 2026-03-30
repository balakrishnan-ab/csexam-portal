import streamlit as st
import requests
import pandas as pd

CLASS_API = "https://sheetdb.io/api/v1/sb3mxuvdynqos?sheet=Classes"
GROUP_API = "https://sheetdb.io/api/v1/sb3mxuvdynqos?sheet=Groups"

# போன் திரைக்கு ஏற்றவாறு Layout
st.set_page_config(page_title="Classes", layout="wide")

st.title("🏫 வகுப்பு மேலாண்மை")

# 1. பிரிவுகளைப் பெறுதல்
try:
    groups = requests.get(GROUP_API).json()
    group_list = [g['group_name'] for g in groups] if isinstance(groups, list) else []
except:
    group_list = []

# 2. புதிய வகுப்பைச் சேர்க்க (Input Area)
with st.expander("➕ புதிய வகுப்பைச் சேர்க்க", expanded=False):
    c_name = st.text_input("வகுப்பு (எ.கா: 12-A1)")
    c_group = st.selectbox("ஒதுக்கப்பட்ட பிரிவு", group_list)
    c_med = st.radio("பயிற்று மொழி", ["தமிழ் வழி", "ஆங்கில வழி"], horizontal=True)
    
    if st.button("➕ வகுப்பை உருவாக்கு", use_container_width=True):
        if c_name:
            payload = {"class_name": c_name, "group_name": c_group, "medium": c_med}
            requests.post(CLASS_API, json={"data": [payload]})
            st.success("வகுப்பு சேர்க்கப்பட்டது!")
            st.rerun()

st.divider()

# 3. அட்டவணை - புதிய நெடுவரிசையுடன் (Column-wise Table)
st.subheader("📋 வகுப்புகளின் விவரம்")

try:
    c_data = requests.get(CLASS_API).json()
    if c_data:
        # தலைப்புகள் (Header)
        # [வகுப்பு, பிரிவு, மொழி, செயல்] - 4 நெடுவரிசைகள்
        h1, h2, h3, h4 = st.columns([2, 3, 2, 1])
        h1.markdown("**வகுப்பு**")
        h2.markdown("**பிரிவு**")
        h3.markdown("**மொழி**")
        h4.markdown("**நீக்க**")
        st.divider()

        for cls in c_data:
            col1, col2, col3, col4 = st.columns([2, 3, 2, 1])
            
            col1.text(cls.get('class_name', ''))
            col2.text(cls.get('group_name', ''))
            col3.text(cls.get('medium', ''))
            
            # 🗑️ சிறிய நீக்குதல் பட்டன்
            if col4.button("🗑️", key=f"del_{cls['class_name']}"):
                requests.delete(f"{CLASS_API}/class_name/{cls['class_name']}")
                st.warning(f"{cls['class_name']} நீக்கப்பட்டது!")
                st.rerun()
    else:
        st.info("வகுப்புகள் ஏதுமில்லை.")
except:
    st.error("தரவுகளைப் பெறுவதில் சிக்கல்!")
