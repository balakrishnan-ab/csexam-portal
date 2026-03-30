import streamlit as st
import requests
import pandas as pd

# API URLs - உங்கள் SheetDB ID-யைப் பயன்படுத்துகிறது
SUB_API = "https://sheetdb.io/api/v1/sb3mxuvdynqos?sheet=Subjects"
GROUP_API = "https://sheetdb.io/api/v1/sb3mxuvdynqos?sheet=Groups"

st.set_page_config(page_title="Group Master", layout="wide")
st.title("🧬 பாடப்பிரிவு உருவாக்கம் (Group Master)")

# 1. ஏற்கனவே உள்ள பாடங்களின் பட்டியலைப் பெறுதல்
try:
    sub_response = requests.get(SUB_API)
    sub_data = sub_response.json()
    # பாடங்களின் பெயர்களை மட்டும் ஒரு லிஸ்ட்டாக எடுக்கிறோம்
    sub_list = [s['subject_name'] for s in sub_data] if isinstance(sub_data, list) else []
except:
    sub_list = []
    st.error("பாடங்கள் பட்டியலைப் பெறுவதில் சிக்கல்!")

# 2. புதிய பாடப்பிரிவை உருவாக்கும் பகுதி
with st.expander("➕ புதிய பாடப்பிரிவை உருவாக்கு", expanded=True):
    col1, col2 = st.columns([1, 2])
    
    g_name = col1.text_input("பிரிவின் பெயர்", placeholder="எ.கா: உயிர்-கணிதம்")
    
    # பாடப்பிரிவுக்குத் தேவையான 6 பாடங்களைத் தேர்ந்தெடுக்கும் வசதி
    selected_subs = col2.multiselect(
        "பாடங்களைத் தேர்ந்தெடுக்கவும் (அதிகபட்சம் 6)", 
        options=sub_list,
        help="இந்த பிரிவிற்குரிய 6 பாடங்களைத் தேர்வு செய்யவும்"
    )
    
    if st.button("💾 பாடப்பிரிவைச் சேமி"):
        if not g_name:
            st.warning("தயவுசெய்து பிரிவின் பெயரை உள்ளிடவும்!")
        elif len(selected_subs) == 0:
            st.warning("குறைந்தது ஒரு பாடத்தையாவது தேர்ந்தெடுக்கவும்!")
        else:
            # பாடங்களை ஒரு வரியாக (Comma Separated) மாற்றுகிறோம்
            subjects_string = ", ".join(selected_subs)
            
            payload = {
                "group_name": g_name,
                "subjects": subjects_string
            }
            
            # SheetDB-க்கு தரவை அனுப்புதல்
            res = requests.post(GROUP_API, json={"data": [payload]})
            
            if res.status_code == 201:
                st.success(f"'{g_name}' பிரிவு உருவாக்கப்பட்டது!")
                st.rerun()
            else:
                st.error("சேமிப்பதில் பிழை ஏற்பட்டது. Groups தாள் இருப்பதை உறுதி செய்யவும்.")

# 3. உருவாக்கப்பட்ட பாடப்பிரிவுகளின் பட்டியல்
st.subheader("📋 தற்போதுள்ள பாடப்பிரிவுகள்")

try:
    g_response = requests.get(GROUP_API)
    g_data = g_response.json()
    
    if g_data and isinstance(g_data, list):
        # தலைப்புகள்
        h1, h2, h3 = st.columns([3, 6, 1])
        h1.markdown("**பிரிவு பெயர்**")
        h2.markdown("**இணைக்கப்பட்ட பாடங்கள்**")
        h3.markdown("**நீக்க**")
        st.divider()

        for group in g_data:
            c1, c2, c3 = st.columns([3, 6, 1])
            c1.text(group.get('group_name', ''))
            c2.info(group.get('subjects', ''))
            
            # 🗑️ நீக்குதல் பட்டன்
            if c3.button("🗑️", key=f"del_g_{group['group_name']}"):
                requests.delete(f"{GROUP_API}/group_name/{group['group_name']}")
                st.warning(f"'{group['group_name']}' நீக்கப்பட்டது!")
                st.rerun()
    else:
        st.info("பாடப்பிரிவுகள் இன்னும் உருவாக்கப்படவில்லை.")
except:
    st.info("Groups தாளில் தரவுகள் ஏதுமில்லை.")
