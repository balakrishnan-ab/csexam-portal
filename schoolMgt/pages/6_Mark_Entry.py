import streamlit as st
import requests
import pandas as pd

# 1. உங்கள் புதிய Google Web App URL-ஐ இங்கே ஒட்டவும்
BASE_URL = "https://script.google.com/macros/s/AKfycbwi1fAX0GjXwzVLTFPZY0Tz_IKMbdphRM_uclgrVBILlhOpM0vgJoE1RVVUTUTE13p6-A/exec"

# 2. சீட் பெயர்களை URL உடன் இணைத்தல்
STUDENT_API = f"{BASE_URL}?sheet=Students"
EXAM_API    = f"{BASE_URL}?sheet=Exams"
CLASS_API   = f"{BASE_URL}?sheet=Classes"
GROUP_API   = f"{BASE_URL}?sheet=Groups"
SUB_API     = f"{BASE_URL}?sheet=Subjects"
MARK_API    = f"{BASE_URL}?sheet=Marks"

st.set_page_config(page_title="Mark Entry", layout="wide")

# (இடையில் உள்ள CSS மற்றும் பழைய லாஜிக் அப்படியே இருக்கட்டும்...)
# [முன்பு நாம் பேசிய CSS இங்கே வரும்]

st.title("✍️ மதிப்பெண் உள்ளீடு")

try:
    # தரவுகளைப் பெறுதல்
    exams_data = requests.get(EXAM_API).json()
    classes_data = requests.get(CLASS_API).json()
    groups_data = requests.get(GROUP_API).json()
    subjects_data = requests.get(SUB_API).json()
    
    exams = [e['exam_name'] for e in exams_data]
    class_list = [c['class_name'] for c in classes_data]
    
    col_a, col_b = st.columns(2)
    sel_exam = col_a.selectbox("தேர்வு", exams)
    sel_class = col_b.selectbox("வகுப்பு", class_list)

    # (பாடப்பிரிவு கண்டறியும் பகுதி...)
    # ...

    # 3. மதிப்பெண்களைச் சேமிக்கும் பகுதி (Patch-க்கு பதிலாக Post)
    if st.form_submit_button("🚀 சேமி (Submit)", use_container_width=True):
        for item in save_list:
            payload = {
                "exam_id": sel_exam, 
                "class_name": sel_class, 
                "emis_no": item['emis_no'],
                f"{col_prefix}_T": item['T'], 
                f"{col_prefix}_P": item['P'], 
                f"{col_prefix}_I": item['I']
            }
            # கூகுள் ஸ்கிரிப்ட்டிற்கு தரவை அனுப்புதல்
            requests.post(MARK_API, json={"data": [payload]})
        
        st.success("வெற்றிகரமாக கூகுள் சீட்டில் சேமிக்கப்பட்டது!")

except Exception as e:
    st.error(f"இணைப்பு பிழை: {e}")
