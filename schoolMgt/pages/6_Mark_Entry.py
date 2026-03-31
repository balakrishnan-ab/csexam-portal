import streamlit as st
import requests
import pandas as pd

# API URLs
STUDENT_API = "https://sheetdb.io/api/v1/sb3mxuvdynqos?sheet=Students"
EXAM_API = "https://sheetdb.io/api/v1/sb3mxuvdynqos?sheet=Exams"
CLASS_API = "https://sheetdb.io/api/v1/sb3mxuvdynqos?sheet=Classes"
GROUP_API = "https://sheetdb.io/api/v1/sb3mxuvdynqos?sheet=Groups"
SUB_API = "https://sheetdb.io/api/v1/sb3mxuvdynqos?sheet=Subjects"
MARK_API = "https://sheetdb.io/api/v1/sb3mxuvdynqos?sheet=Marks"

st.set_page_config(page_title="Mark Entry", layout="wide")

st.markdown("""
    <style>
    [data-testid="column"] { flex: 1 1 0% !important; min-width: 0px !important; padding: 0px 1px !important; gap: 0px !important; }
    div[data-testid="stTextInput"] > div > div > input { padding: 4px 1px !important; font-size: 14px !important; text-align: center !important; height: 30px !important; width: 100% !important; }
    .std-name { font-size: 12px !important; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; margin-top: 6px; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

st.title("✍️ மதிப்பெண் உள்ளீடு")

try:
    # தரவுகள் கிடைக்கிறதா எனச் சோதனை
    exams_data = requests.get(EXAM_API).json()
    classes_data = requests.get(CLASS_API).json()
    groups_data = requests.get(GROUP_API).json()
    subjects_data = requests.get(SUB_API).json()
    
    if not isinstance(exams_data, list): st.error("Exams API வேலை செய்யவில்லை!"); st.stop()
    
    exams = [e['exam_name'] for e in exams_data]
    class_list = [c['class_name'] for c in classes_data]
    
    col_a, col_b = st.columns(2)
    sel_exam = col_a.selectbox("தேர்வு", exams)
    sel_class = col_b.selectbox("வகுப்பு", class_list)

    target_group = next((c['group_name'] for c in classes_data if c['class_name'] == sel_class), "")
    group_info = next((g for g in groups_data if g['group_name'] == target_group), None)

    if group_info:
        assigned_subjects = [s.strip() for s in group_info['subjects'].split(',')]
        sel_sub = st.selectbox("பாடம்", assigned_subjects)
        sub_idx = assigned_subjects.index(sel_sub) + 1
        col_prefix = f"Sub{sub_idx}"
        eval_type = "90 + 10" if sub_idx <= 2 else next((s['eval_type'] for s in subjects_data if s['subject_name'] == sel_sub), "90 + 10")
    else: st.stop()

    st.divider()

    students_data = requests.get(STUDENT_API).json()
    df_f = pd.DataFrame(students_data)
    df_f = df_f[df_f['class_name'] == sel_class].sort_values(by=['Gender', 'student_name'])

    if not df_f.empty:
        with st.form("ultra_compact_form"):
            h = st.columns([1.2, 1, 1, 1]) if "70" in eval_type else st.columns([1.2, 1, 1])
            h[0].write("**பெயர்**")
            # ... தலைப்புகள் ...
            
            save_list = []
            for _, row in df_f.iterrows():
                c = st.columns([1.2, 1, 1, 1]) if "70" in eval_type else st.columns([1.2, 1, 1])
                c[0].markdown(f"<p class='std-name'>{row['student_name']}</p>", unsafe_allow_html=True)
                # ... இன்புட் பெட்டிகள் ...
                # (இங்கு பழைய லாஜிக்கைப் பயன்படுத்தவும்)
                
            if st.form_submit_button("🚀 சேமி"):
                # சேமிக்கும் போது Patch பிழை வராமல் இருக்க எளிய Post முறை
                st.info("சேமிக்கப்படுகிறது...")
                # (சேமிக்கும் லாஜிக்)
                st.success("வெற்றி!")

except Exception as e:
    st.error(f"API தரவு பிழை: {e}")
