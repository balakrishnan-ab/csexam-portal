import streamlit as st
import requests
import pandas as pd

BASE_URL = "https://script.google.com/macros/s/AKfycbzgqCZ6f-kwO46eZPWb_Tr7gz-JdLQSSOL8kVLzRbhPIrinmdQrGiNjNHYIYANNPO8xYg/exec"

st.set_page_config(page_title="Students Management", layout="wide")

st.title("👨‍🎓 மாணவர்கள் மேலாண்மை")

# 1. தரவுகளைப் பெறுதல்
def fetch_all_data():
    try:
        s_res = requests.get(f"{BASE_URL}?sheet=Students", allow_redirects=True)
        c_res = requests.get(f"{BASE_URL}?sheet=Classes", allow_redirects=True)
        return s_res.json(), c_res.json()
    except:
        return [], []

students_data, classes_data = fetch_all_data()
# வகுப்புகளை பட்டியலாக மாற்றுதல்
class_list = [c['class_name'] for c in classes_data] if isinstance(classes_data, list) else []

# 2. புதிய மாணவர் சேர்க்கை படிவம்
st.subheader("🆕 புதிய மாணவர் சேர்க்கை")
with st.form("add_student_form", clear_on_submit=True):
    col1, col2 = st.columns(2)
    name = col1.text_input("பெயர்")
    emis = col2.text_input("EMIS எண்")
    
    col3, col4 = st.columns(2)
    # பாலினத்தை முழுமையாக மாற்றியுள்ளேன்
    gender = col3.selectbox("பாலினம்", ["Male", "Female"])
    # வகுப்பை கீழிறக்கு பட்டியலாக (Dropdown) மாற்றியுள்ளேன்
    cname = col4.selectbox("வகுப்பைத் தேர்ந்தெடுக்கவும்", class_list)
    
    submit = st.form_submit_button("💾 மாணவரைச் சேமி")
    
    if submit:
        if name and emis and cname:
            payload = {"student_name": name, "emis_no": emis, "Gender": gender, "class_name": cname}
            try:
                requests.post(f"{BASE_URL}?sheet=Students", json={"data": [payload]}, allow_redirects=True)
                st.success(f"மாணவர் {name} ({gender}) சேர்க்கப்பட்டார்!")
                st.rerun()
            except Exception as e:
                st.error(f"பிழை: {e}")

st.divider()

# 3. மாணவர்கள் பட்டியல் மற்றும் தேடல் (கீழே)
st.subheader("📋 மாணவர்கள் பட்டியல்")
if students_data:
    df = pd.DataFrame(students_data)
    
    # Filter வசதி
    filter_classes = ["அனைத்தும்"] + sorted(df['class_name'].unique().tolist())
    selected_filter = st.selectbox("வகுப்பு வாரியாகப் பார்க்க:", filter_classes)
    
    df_display = df if selected_filter == "அனைத்தும்" else df[df['class_name'] == selected_filter]
    st.dataframe(df_display, use_container_width=True)

    # 4. பாதுகாப்பான நீக்கல் வசதி
    st.write("---")
    st.subheader("🗑️ மாணவரை நீக்க")
    
    del_student = st.selectbox("நீக்க வேண்டிய மாணவர்:", df_display['student_name'].tolist() if not df_display.empty else [])
    
    # தெரியாமல் நீக்குவதைத் தவிர்க்க உறுதிப்படுத்தல்
    confirm_delete = st.checkbox(f"நான் உறுதியாக {del_student}-ஐ நீக்க விரும்புகிறேன்")
    
    if confirm_delete:
        if st.button(f"❌ {del_student}-ஐ நிரந்தரமாக நீக்கு", type="primary"):
            target_emis = df[df['student_name'] == del_student]['emis_no'].values[0]
            # நீக்கும் கோரிக்கை
            requests.post(f"{BASE_URL}?sheet=Students&action=delete", json={"emis_no": target_emis}, allow_redirects=True)
            st.warning("நீக்கப்பட்டது! சீட்டில் சரிபார்க்கவும்.")
            st.rerun()
else:
    st.info("மாணவர் விவரங்கள் இன்னும் சேர்க்கப்படவில்லை.")
