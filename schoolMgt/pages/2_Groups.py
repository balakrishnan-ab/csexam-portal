import streamlit as st
import requests

# API URLs
SUB_API = "https://sheetdb.io/api/v1/sb3mxuvdynqos?sheet=Subjects"
GROUP_API = "https://sheetdb.io/api/v1/sb3mxuvdynqos?sheet=Groups"

# போன் திரைக்கு ஏற்ற அமைப்பு
st.set_page_config(page_title="Group Master", layout="centered")

st.markdown("""
    <style>
    .stButton>button { width: 100%; border-radius: 10px; height: 3em; }
    .group-card { 
        border: 1px solid #ddd; padding: 15px; border-radius: 10px; 
        margin-bottom: 10px; background-color: #f9f9f9;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("🧬 பாடப்பிரிவு உருவாக்கம்")

# 1. பாடங்களைப் பெறுதல்
try:
    sub_data = requests.get(SUB_API).json()
    sub_list = [s['subject_name'] for s in sub_data] if isinstance(sub_data, list) else []
except:
    sub_list = []

# 2. புதிய பாடப்பிரிவை உருவாக்குதல் (Input Area)
with st.container():
    st.subheader("➕ புதிய பிரிவு")
    g_name = st.text_input("பிரிவின் பெயர்", placeholder="எ.கா: 12-CS")
    selected_subs = st.multiselect("பாடங்களைத் தேர்வு செய்க", sub_list)
    
    if st.button("💾 பிரிவைச் சேமி"):
        if g_name and selected_subs:
            payload = {"group_name": g_name, "subjects": ", ".join(selected_subs)}
            res = requests.post(GROUP_API, json={"data": [payload]})
            if res.status_code == 201:
                st.success("சேமிக்கப்பட்டது!")
                st.rerun()
        else:
            st.warning("விவரங்களை நிரப்பவும்!")

st.divider()

# 3. மொபைல் வியூ பட்டியல் (Card View)
st.subheader("📋 உள்ள பாடப்பிரிவுகள்")
try:
    g_data = requests.get(GROUP_API).json()
    if g_data and isinstance(g_data, list):
        for g in g_data:
            # ஒவ்வொரு பிரிவும் ஒரு பெட்டி (Card) போலத் தெரியும்
            with st.container():
                st.markdown(f"""
                <div class="group-card">
                    <b>பிரிவு:</b> {g.get('group_name', '')}<br>
                    <small><b>பாடங்கள்:</b> {g.get('subjects', '')}</small>
                </div>
                """, unsafe_allow_html=True)
                
                # நீக்குதல் பட்டன் (Card-க்கு கீழே)
                if st.button(f"🗑️ {g['group_name']} நீக்கு", key=f"del_{g['group_name']}"):
                    requests.delete(f"{GROUP_API}/group_name/{g['group_name']}")
                    st.rerun()
    else:
        st.info("பிரிவுகள் ஏதுமில்லை.")
except:
    st.info("தரவுகள் இல்லை.")
