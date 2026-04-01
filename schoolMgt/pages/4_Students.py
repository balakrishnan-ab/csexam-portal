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
class_list = [c['class_name'] for c in classes_data] if isinstance(classes_data, list) else []

# 2. புதிய மாணவர் சேர்க்கை படிவம்
st.subheader("🆕 புதிய மாணவர் சேர்க்கை")
with st.form("add_student_form", clear_on_submit=True):
    col1, col2 = st.columns(2)
    name = col1.text_input("பெயர்")
    emis = col2.text_input("EMIS எண்")
    
    col3, col4 = st.columns(2)
    gender = col3.selectbox("பாலினம்", ["Female", "Male"]) # பெண்களை முதலில் காட்ட Female முதன்மை
    cname = col4.selectbox("வகுப்பைத் தேர்ந்தெடுக்கவும்", class_list)
    
    submit = st.form_submit_button("💾 மாணவரைச் சேமி")
    
    if submit:
        if name and emis and cname:
            payload = {"student_name": name, "emis_no": emis, "Gender": gender, "class_name": cname}
            try:
                requests.post(f"{BASE_URL}?sheet=Students", json={"data": [payload]}, allow_redirects=True)
                st.success(f"மாணவர் {name} சேர்க்கப்பட்டார்!")
                st.rerun()
            except:
                st.error("சேமிப்பதில் பிழை!")

st.divider()

# 3. மாணவர்கள் பட்டியல் (குறிப்பிட்ட வரிசை அமைப்புடன்)
st.subheader("📋 மாணவர்கள் பட்டியல்")
if students_data:
    df = pd.DataFrame(students_data)
    
    filter_classes = ["அனைத்தும்"] + sorted(df['class_name'].unique().tolist())
    selected_filter = st.selectbox("வகுப்பு வாரியாகப் பார்க்க:", filter_classes)
    
    df_filtered = df if selected_filter == "அனைத்தும்" else df[df['class_name'] == selected_filter]

    if not df_filtered.empty:
        # வரிசைப்படுத்துதல்: 1. வகுப்பு, 2. பாலினம் (Female முதலில்), 3. பெயர் (அகர வரிசை)
        # Gender 'Female' என்பது 'Male' ஐ விட அகர வரிசையில் முதலில் வரும் என்பதால் ascending=True சரியாக இருக்கும்
        df_sorted = df_filtered.sort_values(by=['class_name', 'Gender', 'student_name'], ascending=[True, True, True]).reset_index(drop=True)
        
        # வரிசை எண் 1-லிருந்து தொடங்குதல்
        df_sorted.index = df_sorted.index + 1
        df_sorted.index.name = "S.No"
        
        # காலங்களின் வரிசை
        cols = ['student_name', 'Gender', 'class_name', 'emis_no']
        st.dataframe(df_sorted[cols], use_container_width=True)

        # 4. பாதுகாப்பான நீக்கல் வசதி (திருத்தப்பட்டது)
        st.write("---")
        st.subheader("🗑️ மாணவரை நீக்க")
        
        del_student_name = st.selectbox("நீக்க வேண்டிய மாணவர்:", df_sorted['student_name'].tolist())
        confirm_delete = st.checkbox(f"நான் உறுதியாக {del_student_name}-ஐ நீக்க விரும்புகிறேன்")
        
        if confirm_delete:
            if st.button(f"❌ {del_student_name}-ஐ நிரந்தரமாக நீக்கு", type="primary"):
                # EMIS எண்ணை சரியாக எடுத்தல்
                target_emis = df[df['student_name'] == del_student_name]['emis_no'].values[0]
                
                # பிழையைத் தவிர்க்க URL parameters மூலம் அனுப்புதல்
                del_url = f"{BASE_URL}?sheet=Students&action=delete&emis_no={target_emis}"
                try:
                    requests.post(del_url, allow_redirects=True)
                    st.warning(f"{del_student_name} நீக்கப்பட்டார். பக்கத்தை புதுப்பிக்கவும்.")
                    st.rerun()
                except:
                    st.error("நீக்குதலில் பிழை! கூகுள் சீட்டில் நேரடியாக நீக்கவும்.")
    else:
        st.info("தரவுகள் இல்லை.")
