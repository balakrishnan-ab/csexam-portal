import streamlit as st
import requests
import pandas as pd

# 1. பக்க அமைப்பு
st.set_page_config(page_title="Exams Management", layout="wide")

# 2. URL அமைப்பு
try:
    BASE_URL = st.secrets["BASE_URL"]
except:
    st.error("BASE_URL secrets-ல் கண்டறியப்படவில்லை!")
    st.stop()

# 3. ⚡ அனைத்து தரவுகளையும் ஒரே முறையில் பெறுதல் (மின்னல் வேகம்)
@st.cache_data(ttl=300)
def fetch_all_data():
    try:
        # நாம் ஏற்கனவே Script-ஐ மாற்றியதால் வெறும் BASE_URL போதுமானது
        res = requests.get(BASE_URL).json()
        return res
    except:
        return None

data = fetch_all_data()
exams_list = data.get('exams', []) if data else []

st.title("📝 தேர்வு மேலாண்மை")

# 1. புதிய தேர்வு சேர்க்கும் படிவம்
with st.form("add_exam_form", clear_on_submit=True):
    st.subheader("🆕 புதிய தேர்வு சேர்க்கை")
    col1, col2 = st.columns(2)
    ename = col1.text_input("தேர்வின் பெயர் (எ.கா: ANNUAL EXAM)").upper().strip()
    ayear = col2.text_input("கல்வியாண்டு (Academic Year)", value="2025-26")
    
    if st.form_submit_button("💾 தேர்வைச் சேமி"):
        if ename:
            # ID-யை உருவாக்குதல்
            eid = ename.replace(" ", "_").lower()
            payload = {"exam_id": eid, "exam_name": ename, "academic_year": ayear}
            try:
                # தரவைச் சேமிக்கிறோம்
                requests.post(f"{BASE_URL}?sheet=Exams", json={"data": [payload]})
                st.success(f"தேர்வு '{ename}' வெற்றிகரமாகச் சேர்க்கப்பட்டது!")
                st.cache_data.clear() # பழைய கேச்-ஐ நீக்குதல்
                st.rerun()
            except Exception as e:
                st.error(f"பிழை: {e}")
        else:
            st.warning("தேர்வின் பெயரை உள்ளிடவும்.")

st.divider()

# 2. தேர்வுகள் பட்டியல் (பிழை வராமல் கையாளுதல்)
if exams_list:
    st.subheader("📋 தேர்வுகள் பட்டியல்")
    try:
        df = pd.DataFrame(exams_list)
        # நமக்குத் தேவையான காலம்கள் மட்டும் (exam_name, academic_year)
        display_df = df[['exam_name', 'academic_year']].copy()
        display_df.index = range(1, len(display_df) + 1)
        st.table(display_df) # dataframe-க்கு பதில் table இன்னும் வேகமாகத் தெரியும்
    except Exception as e:
        st.error("தரவுகளைக் காட்டுவதில் பிழை. கூகுள் சீட்டில் காலம்கள் (Headers) சரியாக உள்ளனவா எனப் பார்க்கவும்.")

    st.divider()

    # 3. திருத்துதல் மற்றும் நீக்குதல்
    st.subheader("⚙️ நிர்வாகம்")
    
    e_names = [e['exam_name'] for e in exams_list]
    sel_exam = st.selectbox("நிர்வகிக்க வேண்டிய தேர்வு:", ["-- தேர்வு செய்க --"] + e_names)

    if sel_exam != "-- தேர்வு செய்க --":
        # தேர்ந்தெடுக்கப்பட்ட தேர்வின் தற்போதைய விவரம்
        curr_exam = next(e for e in exams_list if e['exam_name'] == sel_exam)
        
        c1, c2 = st.columns(2)
        with c1:
            st.info("📝 திருத்துதல்")
            new_name = st.text_input("புதிய பெயர்:", value=curr_exam['exam_name']).upper()
            new_year = st.text_input("புதிய ஆண்டு:", value=curr_exam['academic_year'])
            if st.button("🆙 அப்டேட் செய்"):
                upd_url = f"{BASE_URL}?sheet=Exams&action=update&old_exam={sel_exam}"
                requests.post(upd_url, json={"data": [{"exam_name": new_name, "academic_year": new_year}]})
                st.cache_data.clear()
                st.rerun()

        with c2:
            st.warning("⚠️ நீக்குதல்")
            if st.button(f"❌ {sel_exam}-ஐ நீக்கு"):
                del_url = f"{BASE_URL}?sheet=Exams&action=delete&exam_name={sel_exam}"
                requests.post(del_url)
                st.cache_data.clear()
                st.rerun()
else:
    st.info("தேர்வுகள் இன்னும் சேர்க்கப்படவில்லை.")
