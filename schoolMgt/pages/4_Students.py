import streamlit as st
import requests
import pandas as pd

# கூகுள் ஸ்கிரிப்ட் URL
BASE_URL = "https://script.google.com/macros/s/AKfycbzgqCZ6f-kwO46eZPWb_Tr7gz-JdLQSSOL8kVLzRbhPIrinmdQrGiNjNHYIYANNPO8xYg/exec"

st.set_page_config(page_title="Students Management", layout="wide")

# ⚡ மிக வேகமான தரவு சேமிப்பு (Caching)
@st.cache_data(ttl=300)
def fetch_data(sheet_name):
    try:
        res = requests.get(f"{BASE_URL}?sheet={sheet_name}", allow_redirects=True)
        return res.json()
    except:
        return []

st.title("👨‍🎓 மாணவர்கள் மேலாண்மை")

# தரவுகளைப் பெறுதல்
students_data = fetch_data("Students")
classes_data = fetch_data("Classes")
class_list = [c['class_name'] for c in classes_data] if isinstance(classes_data, list) else []

# 1. புதிய மாணவர் சேர்க்கை படிவம்
st.subheader("🆕 புதிய மாணவர் சேர்க்கை")
with st.form("add_student_form", clear_on_submit=True):
    col1, col2 = st.columns(2)
    input_name = col1.text_input("பெயர் (Name)")
    emis = col2.text_input("EMIS எண்")
    
    col3, col4 = st.columns(2)
    gender = col3.selectbox("பாலினம்", ["Female", "Male"])
    cname = col4.selectbox("வகுப்பைத் தேர்ந்தெடுக்கவும்", class_list)
    
    if st.form_submit_button("💾 மாணவரைச் சேமி"):
        if input_name and emis:
            final_name = input_name.upper().strip()
            payload = {"student_name": final_name, "emis_no": emis, "Gender": gender, "class_name": cname}
            requests.post(f"{BASE_URL}?sheet=Students", json={"data": [payload]}, allow_redirects=True)
            st.success(f"மாணவர் {final_name} சேர்க்கப்பட்டார்!")
            st.cache_data.clear() # தரவை உடனே புதுப்பிக்க
            st.rerun()

st.divider()

# 2. மாணவர்கள் பட்டியல்
st.subheader("📋 மாணவர்கள் பட்டியல்")
if students_data:
    df = pd.DataFrame(students_data)
    df['student_name'] = df['student_name'].str.upper()
    
    filter_classes = ["அனைத்தும்"] + sorted(df['class_name'].unique().tolist())
    selected_filter = st.selectbox("வகுப்பு வாரியாகப் பார்க்க:", filter_classes)
    
    df_f = df if selected_filter == "அனைத்தும்" else df[df['class_name'] == selected_filter]

    if not df_f.empty:
        # நீங்கள் கேட்ட வரிசை (வகுப்பு -> பாலினம் -> பெயர்)
        df_sorted = df_f.sort_values(by=['class_name', 'Gender', 'student_name']).reset_index(drop=True)
        df_sorted.index = df_sorted.index + 1
        st.dataframe(df_sorted[['student_name', 'Gender', 'class_name', 'emis_no']], use_container_width=True)

        # 3. பாதுகாப்பான நீக்கல் வசதி (உறுதிப்படுத்தலுடன்)
        st.write("---")
        st.subheader("🗑️ மாணவரை நீக்க")
        
        # 'தேர்வு செய்க' என்ற வார்த்தை முதலில் வருமாறு மாற்றம்
        names_list = ["-- மாணவரைத் தேர்வு செய்க --"] + df_sorted['student_name'].tolist()
        del_choice = st.selectbox("நீக்க வேண்டிய மாணவர்:", names_list)
        
        if del_choice != "-- மாணவரைத் தேர்வு செய்க --":
            if st.checkbox(f"நான் உறுதியாக {del_choice}-ஐ நீக்க விரும்புகிறேன்"):
                if st.button(f"❌ {del_choice}-ஐ நிரந்தரமாக நீக்கு", type="primary"):
                    target_emis = str(df[df['student_name'] == del_choice]['emis_no'].values[0])
                    del_url = f"{BASE_URL}?sheet=Students&action=delete&emis_no={target_emis}"
                    requests.post(del_url, allow_redirects=True)
                    st.cache_data.clear()
                    st.rerun()
    else:
        st.info("மாணவர்கள் இல்லை.")
