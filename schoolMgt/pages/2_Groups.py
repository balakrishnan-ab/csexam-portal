import streamlit as st
import requests
import pandas as pd

# கூகுள் ஸ்கிரிப்ட் URL
BASE_URL = "https://script.google.com/macros/s/AKfycbzgqCZ6f-kwO46eZPWb_Tr7gz-JdLQSSOL8kVLzRbhPIrinmdQrGiNjNHYIYANNPO8xYg/exec"

st.set_page_config(page_title="Groups Management", layout="wide")

# ⚡ வேகமான தரவு சேமிப்பு (Caching)
@st.cache_data(ttl=300)
def fetch_groups():
    try:
        res = requests.get(f"{BASE_URL}?sheet=Groups", allow_redirects=True)
        return res.json()
    except:
        return []

st.title("👥 பாடப்பிரிவுகள் மேலாண்மை")

# 1. புதிய பாடப்பிரிவு சேர்க்கும் படிவம்
with st.form("add_group_form", clear_on_submit=True):
    st.subheader("🆕 புதிய பாடப்பிரிவு (Group)")
    gname = st.text_input("பாடப்பிரிவு பெயர் (எ.கா: SCIENCE)").upper().strip()
    subjects = st.text_area("பாடங்கள் (பாடங்களுக்கு இடையே கமா (,) இடவும்)").upper()
    
    if st.form_submit_button("💾 பாடப்பிரிவைச் சேமி"):
        if gname and subjects:
            payload = {"group_name": gname, "subjects": subjects}
            requests.post(f"{BASE_URL}?sheet=Groups", json={"data": [payload]}, allow_redirects=True)
            st.success(f"பாடப்பிரிவு '{gname}' வெற்றிகரமாகச் சேர்க்கப்பட்டது!")
            st.cache_data.clear()
            st.rerun()

st.divider()

# 2. பாடப்பிரிவுகள் பட்டியல் (ID மறைக்கப்பட்டது)
groups_data = fetch_groups()
if groups_data:
    df = pd.DataFrame(groups_data)
    df_sorted = df.sort_values(by='group_name').reset_index(drop=True)
    df_sorted.index = df_sorted.index + 1
    df_sorted.index.name = "S.No"
    
    st.subheader("📋 பாடப்பிரிவுகள் பட்டியல்")
    # 🛡️ 'id' காலத்தை மறைத்துவிட்டுத் தேவையானவற்றை மட்டும் காட்டுதல்
    st.dataframe(df_sorted[['group_name', 'subjects']], use_container_width=True)

    st.divider()

    # 3. திருத்துதல் மற்றும் நீக்குதல் (Edit & Delete)
    st.subheader("⚙️ பாடப்பிரிவை மாற்றியமைக்க / நீக்க")
    
    g_list = ["-- பாடப்பிரிவைத் தேர்வு செய்க --"] + df_sorted['group_name'].tolist()
    selected_group = st.selectbox("மேலாண்மை செய்ய வேண்டிய பாடப்பிரிவு:", g_list)

    if selected_group != "-- பாடப்பிரிவைத் தேர்வு செய்க --":
        # பழைய தரவுகளை எடுத்தல்
        old_data = df[df['group_name'] == selected_group].iloc[0]
        
        col1, col2 = st.columns(2)
        with col1:
            st.write("📝 திருத்துதல் (Edit)")
            new_gname = st.text_input("புதிய பெயர்:", value=old_data['group_name']).upper()
            new_subjects = st.text_area("புதிய பாடங்கள் பட்டியல்:", value=old_data['subjects']).upper()
            
            if st.button("🆙 திருத்து (Update)"):
                update_url = f"{BASE_URL}?sheet=Groups&action=update&old_group={selected_group}"
                payload = {"group_name": new_gname, "subjects": new_subjects}
                requests.post(update_url, json={"data": [payload]}, allow_redirects=True)
                st.success("மாற்றப்பட்டது!")
                st.cache_data.clear()
                st.rerun()

        with col2:
            st.write("⚠️ எச்சரிக்கை")
            confirm_del = st.checkbox(f"நான் {selected_group}-ஐ நீக்க விரும்புகிறேன்")
            if confirm_del:
                if st.button(f"❌ {selected_group}-ஐ நீக்கு", type="primary"):
                    del_url = f"{BASE_URL}?sheet=Groups&action=delete&group_name={selected_group}"
                    requests.post(del_url, allow_redirects=True)
                    st.warning("நீக்கப்பட்டது!")
                    st.cache_data.clear()
                    st.rerun()
else:
    st.info("பாடப்பிரிவுகள் இன்னும் சேர்க்கப்படவில்லை.")
