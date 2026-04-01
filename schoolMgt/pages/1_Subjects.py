import streamlit as st
import requests
import pandas as pd

# கூகுள் ஸ்கிரிப்ட் URL
BASE_URL = "https://script.google.com/macros/s/AKfycbzgqCZ6f-kwO46eZPWb_Tr7gz-JdLQSSOL8kVLzRbhPIrinmdQrGiNjNHYIYANNPO8xYg/exec"

st.set_page_config(page_title="Subjects Management", layout="wide")

# ⚡ வேகமான தரவு சேமிப்பு (Caching)
@st.cache_data(ttl=300)
def fetch_subjects():
    try:
        res = requests.get(f"{BASE_URL}?sheet=Subjects", allow_redirects=True)
        return res.json()
    except:
        return []

st.title("📚 பாடங்கள் மேலாண்மை")

# 1. புதிய பாடம் சேர்க்கும் படிவம்
with st.form("add_subject_form", clear_on_submit=True):
    st.subheader("🆕 புதிய பாடம்")
    name = st.text_input("பாடம் பெயர்").upper().strip()
    etype = st.selectbox("மதிப்பீட்டு முறை", ["90 + 10", "70 + 20 + 10"])
    
    if st.form_submit_button("💾 பாடத்தைச் சேமி"):
        if name:
            payload = {"subject_name": name, "eval_type": etype}
            requests.post(f"{BASE_URL}?sheet=Subjects", json={"data": [payload]}, allow_redirects=True)
            st.success(f"பாடம் '{name}' சேர்க்கப்பட்டது!")
            st.cache_data.clear()
            st.rerun()

st.divider()

# 2. பாடங்கள் பட்டியல் (ID மறைக்கப்பட்டது)
subjects_data = fetch_subjects()
if subjects_data:
    df = pd.DataFrame(subjects_data)
    df_sorted = df.sort_values(by='subject_name').reset_index(drop=True)
    df_sorted.index = df_sorted.index + 1
    
    st.subheader("📋 பாடங்கள் பட்டியல்")
    st.dataframe(df_sorted[['subject_name', 'eval_type']], use_container_width=True)

    st.divider()

    # 3. திருத்துதல் மற்றும் நீக்குதல் (Edit & Delete)
    st.subheader("⚙️ பாடத்தை மாற்றியமைக்க / நீக்க")
    
    sub_list = ["-- பாடத்தைத் தேர்வு செய்க --"] + df_sorted['subject_name'].tolist()
    selected_sub = st.selectbox("மேலாண்மை செய்ய வேண்டிய பாடம்:", sub_list)

    if selected_filter != "-- பாடத்தைத் தேர்வு செய்க --":
        # பழைய தரவுகளைக் கண்டறிதல்
        old_data = df[df['subject_name'] == selected_sub].iloc[0]
        
        col1, col2 = st.columns(2)
        with col1:
            new_name = st.text_input("புதிய பெயர்:", value=old_data['subject_name']).upper()
            new_etype = st.selectbox("புதிய மதிப்பீட்டு முறை:", ["90 + 10", "70 + 20 + 10"], 
                                    index=0 if old_data['eval_type'] == "90 + 10" else 1)
            
            if st.button("🆙 திருத்து (Update)"):
                # திருத்துவதற்கான logic (குறிப்பு: உங்கள் Apps Script-ல் update action இருக்க வேண்டும்)
                update_url = f"{BASE_URL}?sheet=Subjects&action=update&old_name={selected_sub}"
                requests.post(update_url, json={"data": [{"subject_name": new_name, "eval_type": new_etype}]}, allow_redirects=True)
                st.success("மாற்றப்பட்டது!")
                st.cache_data.clear()
                st.rerun()

        with col2:
            st.write("⚠️ எச்சரிக்கை")
            confirm_del = st.checkbox(f"நான் {selected_sub}-ஐ நீக்க விரும்புகிறேன்")
            if confirm_del:
                if st.button(f"❌ {selected_sub}-ஐ நீக்கு", type="primary"):
                    del_url = f"{BASE_URL}?sheet=Subjects&action=delete&name={selected_sub}"
                    requests.post(del_url, allow_redirects=True)
                    st.warning("நீக்கப்பட்டது!")
                    st.cache_data.clear()
                    st.rerun()
else:
    st.info("பாடங்கள் இன்னும் சேர்க்கப்படவில்லை.")
