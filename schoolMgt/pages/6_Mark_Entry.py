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

# CSS - பெயருக்கும் பெட்டிக்கும் இடைவெளியைக் குறைக்க
st.markdown("""
    <style>
    /* காலம்களுக்கு இடையிலான இடைவெளியைக் குறைத்தல் */
    [data-testid="column"] {
        width: min-content !important;
        flex-basis: auto !important;
        padding: 0px 1px !important;
    }
    /* இன்புட் பாக்ஸ் அளவைச் சிறியதாக்குதல் */
    input {
        padding: 4px !important;
        font-size: 13px !important;
        text-align: center;
    }
    /* பெயரின் அளவைச் சிறியதாக்கி இடைவெளியைக் குறைத்தல் */
    .student-name {
        font-size: 12px !important;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        margin-top: 8px;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("✍️ மதிப்பெண் உள்ளீடு")

# 1. தரவுகளைப் பெறுதல்
try:
    exams = [e['exam_name'] for e in requests.get(EXAM_API).json()]
    classes_data = requests.get(CLASS_API).json()
    groups_data = requests.get(GROUP_API).json()
    subjects_data = requests.get(SUB_API).json()
    class_list = [c['class_name'] for c in classes_data]
except:
    st.error("API Error!")
    st.stop()

c1, c2 = st.columns(2)
sel_exam = c1.selectbox("தேர்வு", exams)
sel_class = c2.selectbox("வகுப்பு", class_list)

# பாடப்பிரிவு கண்டறிதல்
target_group = next((c['group_name'] for c in classes_data if c['class_name'] == sel_class), "")
group_info = next((g for g in groups_data if g['group_name'] == target_group), None)

if group_info:
    assigned_subjects = [s.strip() for s in group_info['subjects'].split(',')]
    sel_sub = st.selectbox("பாடம்", assigned_subjects)
    sub_idx = assigned_subjects.index(sel_sub) + 1
    col_prefix = f"Sub{sub_idx}"
    
    if sub_idx <= 2: eval_type = "90 + 10"
    else:
        sub_info = next((s for s in subjects_data if s['subject_name'] == sel_sub), None)
        eval_type = sub_info['eval_type'] if sub_info else "90 + 10"
else: st.stop()

st.divider()

# 2. ஸ்மார்ட் ஃபில் (Smart Fill)
cf1, cf2 = st.columns(2)
fill_i = cf1.checkbox("I (10) அனைவருக்கும்")
fill_p = False
if "70" in eval_type:
    fill_p = cf2.checkbox("P (20) அனைவருக்கும்")

# 3. மார்க் என்ட்ரி (Compact Table)
try:
    students = requests.get(STUDENT_API).json()
    df_f = pd.DataFrame(students)
    df_f = df_f[df_f['class_name'] == sel_class].sort_values(by=['Gender', 'student_name'])

    if not df_f.empty:
        with st.form("marks_form"):
            # தலைப்பு வரிசை (Headers) - மிக நெருக்கமாக
            if "70" in eval_type:
                h1, h2, h3, h4 = st.columns([2, 1, 1, 1])
                h1.write("**பெயர்**"); h2.write("**E70**"); h3.write("**P20**"); h4.write("**I10**")
            else:
                h1, h2, h3 = st.columns([2, 1, 1])
                h1.write("**பெயர்**"); h2.write("**E90**"); h3.write("**I10**")
            
            st.markdown("---")
            
            save_data = []
            for _, row in df_f.iterrows():
                # விகிதம் [2, 1, 1, 1] - பெயருக்கு 2 பங்கு, மற்றவைக்கு 1 பங்கு
                if "70" in eval_type:
                    c1, c2, c3, c4 = st.columns([2, 1, 1, 1])
                    c1.markdown(f"<div class='student-name'>{row['student_name']}</div>", unsafe_allow_html=True)
                    t = c2.text_input("T", key=f"t_{row['emis_no']}", label_visibility="collapsed")
                    p = c3.text_input("P", value="20" if fill_p else "", key=f"p_{row['emis_no']}", label_visibility="collapsed")
                    i = c4.text_input("I", value="10" if fill_i else "", key=f"i_{row['emis_no']}", label_visibility="collapsed")
                    save_data.append({"emis_no": row['emis_no'], "T": t, "P": p, "I": i})
                else:
                    c1, c2, c3 = st.columns([2, 1, 1])
                    c1.markdown(f"<div class='student-name'>{row['student_name']}</div>", unsafe_allow_html=True)
                    e = c2.text_input("E", key=f"e_{row['emis_no']}", label_visibility="collapsed")
                    i = c3.text_input("I", value="10" if fill_i else "", key=f"i_{row['emis_no']}", label_visibility="collapsed")
                    save_data.append({"emis_no": row['emis_no'], "T": e, "P": "", "I": i})

            if st.form_submit_button("💾 அனைத்தையும் சேமி (Submit)", use_container_width=True):
                for res in save_data:
                    payload = {
                        "exam_id": sel_exam, "class_name": sel_class, "emis_no": res['emis_no'],
                        f"{col_prefix}_T": res['T'], f"{col_prefix}_P": res['P'], f"{col_prefix}_I": res['I']
                    }
                    requests.patch(f"{MARK_API}/emis_no/{res['emis_no']}", json={"data": payload})
                st.success("வெற்றிகரமாகச் சேமிக்கப்பட்டது!")
    else: st.info("மாணவர்கள் இல்லை.")
except: st.error("பிழை!")
