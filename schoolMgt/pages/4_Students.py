import streamlit as st
import requests
import pandas as pd

# உங்களது புதிய Google Web App URL
BASE_URL = "https://script.google.com/macros/s/AKfycbzgqCZ6f-kwO46eZPWb_Tr7gz-JdLQSSOL8kVLzRbhPIrinmdQrGiNjNHYIYANNPO8xYg/exec"

st.set_page_config(page_title="Students Management", layout="wide")

# ⚡ வேகம் அதிகரிக்க தரவுகளை தற்காலிகமாக சேமித்தல் (Caching)
@st.cache_data(ttl=60)
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
    
    # .upper() மூலம் உள்ளீடு செய்யும் போதே பெரிய எழுத்தாக மாற்றப்படுகிறது
    input_name = col1.text_input("பெயர் (Name)")
    emis = col2.text_input("EMIS எண்")
    
    col3, col4 = st.columns(2)
    gender = col3.selectbox("பாலினம்", ["Female", "Male"])
    cname = col4.selectbox("வகுப்பைத் தேர்ந்தெடுக்கவும்", class_list)
    
    submit = st.form_submit_button("💾 மாணவரைச் சேமி")
    
    if submit:
        if input_name and emis and cname:
            # பெயரை பெரிய எழுத்துக்களாக மாற்றி சேமித்தல்
            final_name = input_name.upper().strip()
            payload = {
                "student_name": final_name, 
                "emis_no": emis, 
                "Gender": gender, 
                "class_name": cname
            }
            try:
                requests.post(f"{BASE_URL}?sheet=Students", json={"data": [payload]}, allow_redirects=True)
                st.success(f"மாணவர் {final_name} வெற்றிகரமாகச் சேர்க்கப்பட்டார்!")
                # தரவை புதுப்பிக்க Cache-ஐ அழித்தல்
                st.cache_data.clear()
                st.rerun()
            except Exception as e:
                st.error(f"சேமிப்பதில் பிழை: {e}")
        else:
            st.warning("பெயர் மற்றும் EMIS எண் கட்டாயம் தேவை.")

st.divider()

# 2. மாணவர்கள் பட்டியல் (வரிசைப்படுத்தப்பட்டது)
st.subheader("📋 மாணவர்கள் பட்டியல்")
if students_data:
    df = pd.DataFrame(students_data)
    
    # ஏற்கெனவே உள்ள பெயர்களையும் பெரிய எழுத்துக்களாக மாற்றி வரிசைப்படுத்துதல்
    df['student_name'] = df['student_name'].str.upper()
    
    filter_classes = ["அனைத்தும்"] + sorted(df['class_name'].unique().tolist())
    selected_filter = st.selectbox("வகுப்பு வாரியாகப் பார்க்க:", filter_classes)
    
    df_filtered = df if selected_filter == "அனைத்தும்" else df[df['class_name'] == selected_filter]

    if not df_filtered.empty:
        # நீங்கள் கேட்ட வரிசை: 1.வகுப்பு, 2.பாலினம் (பெண்கள் முதலில்), 3.பெயர் (A-Z)
        df_sorted = df_filtered.sort_values(
            by=['class_name', 'Gender', 'student_name'], 
            ascending=[True, True, True]
        ).reset_index(drop=True)
        
        # வரிசை எண் (S.No) 1-லிருந்து தொடங்குதல்
        df_sorted.index = df_sorted.index + 1
        df_sorted.index.name = "S.No"
        
        # தேவையான காலங்களை மட்டும் காட்டுதல்
        st.dataframe(df_sorted[['student_name', 'Gender', 'class_name', 'emis_no']], use_container_width=True)

        # 3. பாதுகாப்பான நீக்கல் வசதி
        st.write("---")
        st.subheader("🗑️ மாணவரை நீக்க")
        del_student = st.selectbox("நீக்க வேண்டிய மாணவர்:", df_sorted['student_name'].tolist())
        
        if st.checkbox(f"நான் உறுதியாக {del_student}-ஐ நீக்க விரும்புகிறேன்"):
            if st.button(f"❌ {del_student}-ஐ நீக்கு", type="primary"):
                # EMIS எண்ணை எடுத்து URL மூலம் நீக்குதல் (TypeError பிழையைத் தவிர்க்க)
                target_emis = str(df[df['student_name'] == del_student]['emis_no'].values[0])
                del_url = f"{BASE_URL}?sheet=Students&action=delete&emis_no={target_emis}"
                
                requests.post(del_url, allow_redirect
