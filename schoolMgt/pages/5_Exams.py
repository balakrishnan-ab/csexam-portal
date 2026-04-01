import streamlit as st
import requests
import pandas as pd

# கூகுள் ஸ்கிரிப்ட் URL
BASE_URL = "https://script.google.com/macros/s/AKfycbzgqCZ6f-kwO46eZPWb_Tr7gz-JdLQSSOL8kVLzRbhPIrinmdQrGiNjNHYIYANNPO8xYg/exec"

st.set_page_config(page_title="Exams Management", layout="wide")

# ⚡ தரவுகளை வேகமாகப் பெறுதல் (Caching)
@st.cache_data(ttl=300)
def fetch_exams():
    try:
        res = requests.get(f"{BASE_URL}?sheet=Exams", allow_redirects=True)
        return res.json()
    except:
        return []

st.title("📝 தேர்வு மேலாண்மை")

# 1. புதிய தேர்வு சேர்க்கும் படிவம்
with st.form("add_exam_form", clear_on_submit=True):
    st.subheader("🆕 புதிய தேர்வு சேர்க்கை")
    col1, col2 = st.columns(2)
    ename = col1.text_input("தேர்வின் பெயர் (எ.கா: ANNUAL EXAM)").upper().strip()
    ayear = col2.text_input("கல்வியாண்டு (Academic Year)", value="2025-26")
    
    if st.form_submit_button("💾 தேர்வைச் சேமி"):
        if ename:
            # தேர்வுக்கான ஒரு ID-யை பெயரிலிருந்தே உருவாக்குதல்
            eid = ename.replace(" ", "_").lower()
            payload = {"exam_id": eid, "exam_name": ename, "academic_year": ayear}
            try:
                requests.post(f"{BASE_URL}?sheet=Exams", json={"data": [payload]}, allow_redirects=True)
                st.success(f"தேர்வு '{ename}' வெற்றிகரமாகச் சேர்க்கப்பட்டது!")
                st.cache_data.clear()
                st.rerun()
            except Exception as e:
                st.error(f"பிழை: {e}")
        else:
            st.warning("தேர்வின் பெயரை உள்ளிடவும்.")

st.divider()

# 2. தேர்வுகள் பட்டியல் (ID மறைக்கப்பட்டது)
exams_data = fetch_exams()
if exams_data:
    df = pd.DataFrame(exams_data)
    df_sorted = df.reset_index(drop=True)
    df_sorted.index = df_sorted.index + 1
    df_sorted.index.name = "S.No"
    
    st.subheader("📋 தேர்வுகள் பட்டியல்")
    # 🛡️ 'exam_id' காலத்தை மறைத்துவிட்டுப் பெயரை மட்டும் காட்டுதல்
    st.dataframe(df_sorted[['exam_name', 'academic_year']], use_container_width=True)

    st.divider()

    # 3. திருத்துதல் மற்றும் நீக்குதல் (Edit & Delete)
    st.subheader("⚙️ தேர்வை மாற்றியமைக்க / நீக்க")
    
    e_list = ["-- தேர்வைத் தேர்வு செய்க --"] + df_sorted['exam_name'].tolist()
    sel_exam = st.selectbox("நிர்வகிக்க வேண்டிய தேர்வு:", e_list)

    if sel_exam != "-- தேர்வைத் தேர்வு செய்க --":
        old_data = df[df['exam_name'] == sel_exam].iloc[0]
        
        col1, col2 = st.columns(2)
        with col1:
            st.write("📝 திருத்துதல் (Edit)")
            new_ename = st.text_input("புதிய தேர்வு பெயர்:", value=old_data['exam_name']).upper()
            new_ayear = st.text_input("புதிய கல்வியாண்டு:", value=old_data['academic_year'])
            
            if st.button("🆙 திருத்து (Update)"):
                update_url = f"{BASE_URL}?sheet=Exams&action=update&old_exam={sel_exam}"
                payload = {"exam_name": new_ename, "academic_year": new_ayear}
                requests.post(update_url, json={"data": [payload]}, allow_redirects=True)
                st.success("தேர்வு விவரங்கள் மாற்றப்பட்டது!")
                st.cache_data.clear()
                st.rerun()

        with col2:
            st.write("⚠️ நீக்குதல் (Delete)")
            if st.checkbox(f"நான் {sel_exam}-ஐ நீக்க விரும்புகிறேன்"):
                if st.button(f"❌ {sel_exam}-ஐ நீக்கு", type="primary"):
                    del_url = f"{BASE_URL}?sheet=Exams&action=delete&exam_name={sel_exam}"
                    requests.post(del_url, allow_redirects=True)
                    st.warning("தேர்வு நீக்கப்பட்டது!")
                    st.cache_data.clear()
                    st.rerun()
else:
    st.info("தேர்வுகள் இன்னும் சேர்க்கப்படவில்லை.")
