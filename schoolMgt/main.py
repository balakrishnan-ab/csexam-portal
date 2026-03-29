import streamlit as st
import requests
import pandas as pd

# SheetDB Base URL
BASE_URL = "https://sheetdb.io/api/v1/sb3mxuvdynqos"

st.set_page_config(page_title="GHSS Portal", layout="wide")

# இடதுபுற மெனு (Sidebar Navigation)
menu = st.sidebar.selectbox("மெனுவைத் தேர்வு செய்க", ["பாடம் மேலாண்மை", "பாடப்பிரிவு உருவாக்கம்", "வகுப்பு மேலாண்மை"])

# --- 1. பாடம் மேலாண்மை (Subject Master) ---
if menu == "பாடம் மேலாண்மை":
    st.header("📚 பாடம் மேலாண்மை (Subject Master)")
    
    with st.expander("➕ புதிய பாடம் சேர்க்க", expanded=True):
        col1, col2 = st.columns(2)
        sub_name = col1.text_input("பாடத்தின் பெயர்")
        eval_type = col2.selectbox("வகை", ["90 + 10", "70 + 20 + 10"])
        
        if st.button("பாடத்தைச் சேமி"):
            requests.post(f"{BASE_URL}?sheet=Subjects", json={"data": [{"id": sub_name, "subject_name": sub_name, "eval_type": eval_type}]})
            st.rerun()

    # பாடப்பார்வை (Table)
    data = requests.get(f"{BASE_URL}?sheet=Subjects").json()
    if data:
        st.table(pd.DataFrame(data)[['subject_name', 'eval_type']])

# --- 2. பாடப்பிரிவு உருவாக்கம் (Group Master) ---
elif menu == "பாடப்பிரிவு உருவாக்கம்":
    st.header("🧬 பாடப்பிரிவு மேலாண்மை (Group Master)")
    
    # பாடங்களின் பட்டியலை எடுத்துக்கொள்ளுதல்
    sub_data = requests.get(f"{BASE_URL}?sheet=Subjects").json()
    sub_list = [s['subject_name'] for s in sub_data] if sub_data else []

    with st.form("group_form"):
        g_name = st.text_input("பிரிவின் பெயர் (எ.கா: உயிர்-கணிதம்)")
        st.write("6 பாடங்களைத் தேர்ந்தெடுக்கவும்:")
        selected_subs = st.multiselect("பாடங்கள்", sub_list, max_selections=6)
        
        if st.form_submit_button("பிரிவை உருவாக்கு"):
            # இங்கே பிரிவைச் சேமிக்கும் லாஜிக் வரும்
            st.success(f"{g_name} பிரிவு உருவாக்கப்பட்டது!")

# --- 3. வகுப்பு மேலாண்மை (Class Master) ---
elif menu == "வகுப்பு மேலாண்மை":
    st.header("🏫 வகுப்பு மேலாண்மை (Class Master)")
    # நீங்கள் ஏற்கனவே வைத்திருக்கும் வகுப்பு மேலாண்மை கோட் இங்கே வரும்
    st.info("இங்கே வகுப்புகளைப் பிரிவுகளுடன் இணைக்கலாம்.")
