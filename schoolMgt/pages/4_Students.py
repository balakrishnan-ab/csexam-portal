import streamlit as st
import requests
import pandas as pd

# 1. பக்க அமைப்பு
st.set_page_config(page_title="Students Management", layout="wide")

# 2. URL அமைப்பு
try:
    BASE_URL = st.secrets["BASE_URL"]
except:
    st.error("BASE_URL secrets-ல் கண்டறியப்படவில்லை!")
    st.stop()

# 3. ⚡ மின்னல் வேகத்தில் அனைத்து தரவுகளையும் பெறுதல்
@st.cache_data(ttl=300)
def fetch_everything():
    try:
        # புதிய கூகுள் ஸ்கிரிப்ட் படி ஒரே முறையில் அனைத்து சீட்களையும் எடுக்கும்
        res = requests.get(BASE_URL).json()
        return res
    except:
        return None

all_data = fetch_everything()

if not all_data:
    st.warning("கூகுள் சீட்டில் இருந்து தகவல்கள் வரவில்லை.")
    st.stop()

# தரவுகளைப் பிரித்தல்
students_list = all_data.get('students', [])
classes_list = all_data.get('classes', [])
class_names = [c['class_name'] for c in classes_list]

st.title("👨‍🎓 மாணவர்கள் மேலாண்மை")

# 1. புதிய மாணவர் சேர்க்கை படிவம்
with st.form("add_student_form", clear_on_submit=True):
    st.subheader("🆕 புதிய மாணவர் சேர்க்கை")
    
    c1, c2, c3 = st.columns(3)
    input_name = c1.text_input("மாணவர் பெயர் (Name)").upper().strip()
    emis = c2.text_input("EMIS எண்")
    roll_no = c3.text_input("தேர்வு எண் (Roll No)") # ஆசிரியர்களுக்காக புதிய காலம்
    
    c4, c5 = st.columns(2)
    gender = c4.selectbox("பாலினம்", ["Female", "Male"])
    cname = c5.selectbox("வகுப்பைத் தேர்ந்தெடுக்கவும்", class_names)
    
    if st.form_submit_button("💾 மாணவரைச் சேமி"):
        if input_name and emis:
            payload = {
                "student_name": input_name, 
                "emis_no": emis, 
                "roll_no": roll_no, # தேர்வு எண் சேமிக்கப்படுகிறது
                "Gender": gender, 
                "class_name": cname
            }
            try:
                # தரவைச் சேமிக்கிறோம்
                requests.post(f"{BASE_URL}?sheet=Students", json={"data": [payload]})
                st.success(f"மாணவர் {input_name} சேர்க்கப்பட்டார்!")
                st.cache_data.clear() # Cache-ஐத் துடைத்துவிட்டு புதுப்பிக்கவும்
                st.rerun()
            except Exception as e:
                st.error(f"பிழை: {e}")
        else:
            st.warning("பெயர் மற்றும் EMIS எண்ணை உள்ளிடவும்.")

st.divider()

# 2. மாணவர்கள் பட்டியல்
if students_list:
    st.subheader("📋 மாணவர்கள் பட்டியல்")
    df = pd.DataFrame(students_list)
    
    # Filter: வகுப்பு வாரியாகப் பார்த்தல்
    filter_classes = ["அனைத்தும்"] + sorted(df['class_name'].unique().tolist())
    selected_filter = st.selectbox("வகுப்பு வாரியாகப் பார்க்க:", filter_classes)
    
    df_f = df if selected_filter == "அனைத்தும்" else df[df['class_name'] == selected_filter]

    if not df_f.empty:
        # வரிசைப்படுத்துதல்: வகுப்பு -> பாலினம் -> பெயர்
        df_sorted = df_f.sort_values(by=['class_name', 'Gender', 'student_name']).reset_index(drop=True)
        df_sorted.index = range(1, len(df_sorted) + 1)
        
        # 'roll_no' காலத்தை முன்னால் காட்டுதல்
        cols_to_show = ['roll_no', 'student_name', 'Gender', 'class_name', 'emis_no']
        st.dataframe(df_sorted[cols_to_show], use_container_width=True)

        st.divider()

        # 3. மாணவரை நீக்க (Delete)
        st.subheader("🗑️ மாணவரை நீக்க")
        
        # EMIS மற்றும் பெயரைக் காட்டித் தேர்வு செய்தல்
        df_sorted['display_name'] = df_sorted['student_name'] + " (" + df_sorted['emis_no'].astype(str) + ")"
        del_choice = st.selectbox("நீக்க வேண்டிய மாணவரைத் தேர்வு செய்க:", ["-- தேர்வு செய்க --"] + df_sorted['display_name'].tolist())
        
        if del_choice != "-- தேர்வு செய்க --":
            # EMIS எண்ணைப் பிரித்தெடுத்தல்
            target_emis = del_choice.split('(')[-1].replace(')', '')
            
            if st.checkbox(f"நான் {del_choice}-ஐ நீக்க விரும்புகிறேன்"):
                if st.button(f"❌ மாணவரை நிரந்தரமாக நீக்கு", type="primary"):
                    del_url = f"{BASE_URL}?sheet=Students&action=delete&emis_no={target_emis}"
                    requests.post(del_url)
                    st.success("மாணவர் நீக்கப்பட்டார்!")
                    st.cache_data.clear()
                    st.rerun()
    else:
        st.info("இந்த வகுப்பில் மாணவர்கள் இல்லை.")
else:
    st.info("மாணவர்கள் பட்டியல் இன்னும் உருவாக்கப்படவில்லை.")
