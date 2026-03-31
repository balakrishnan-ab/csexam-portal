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

# CSS - பெட்டிகள் மிகச் சிறியதாகவும் ஒரே வரியிலும் இருக்க
st.markdown("""
    <style>
    div[data-testid="stColumn"] { padding: 0px 2px !important; }
    input { font-size: 14px !important; padding: 5px !important; text-align: center; }
    .stMarkdown p { font-size: 13px !important; margin-bottom: 0px; }
    </style>
    """, unsafe_allow_html=True)

st.title("✍️ மதிப்பெண் உள்ளீடு")

# 1. அடிப்படைத் தரவுகள்
try:
    exams = [e['exam_name'] for e in requests.get(EXAM_API).json()]
    classes_data = requests.get(CLASS_API).json()
    groups_data = requests.get(GROUP_API).json()
    subjects_data = requests.get(SUB_API).json()
    class_list = [c['class_name'] for c in classes_data]
except:
    st.error("API பிழை!")
    st.stop()

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
    
    if sub_idx <= 2: eval_type = "90 + 10"
    else:
        sub_info = next((s for s in subjects_data if s['subject_name'] == sel_sub), None)
        eval_type = sub_info['eval_type'] if sub_info else "90 + 10"
else: st.stop()

st.divider()

# 2. ஸ்மார்ட் மார்க் செக்-பாக்ஸ்
c_fill1, c_fill2 = st.columns(2)
fill_i = c_fill1.checkbox("I (10) அனைவருக்கும்")
fill_p = False
if "70" in eval_type:
    fill_p = c_fill2.checkbox("P (20) அனைவருக்கும்")

# 3. மார்க் என்ட்ரி படிவம்
try:
    students = requests.get(STUDENT_API).json()
    df_f = pd.DataFrame(students)
    df_f = df_f[df_f['class_name'] == sel_class].sort_values(by=['Gender', 'student_name'])

    if not df_f.empty:
        with st.form("marks_form"):
            # தலைப்பு வரிசை
            if "70" in eval_type:
                h_n, h_t, h_p, h_i = st.columns([3, 1, 1, 1])
                h_n.write("**பெயர்**"); h_t.write("**E(70)**"); h_p.write("**P(20)**"); h_i.write("**I(10)**")
            else:
                h_n, h_e, h_i = st.columns([3, 1, 1])
                h_n.write("**பெயர்**"); h_e.write("**E(90)**"); h_i.write("**I(10)**")
            
            st.markdown("---")
            
            results = []
            for _, row in df_f.iterrows():
                if "70" in eval_type:
                    c1, c2, c3, c4 = st.columns([3, 1, 1, 1])
                    c1.write(row['student_name'])
                    t = c2.text_input("T", key=f"t_{row['emis_no']}", label_visibility="collapsed")
                    p = c3.text_input("P", value="20" if fill_p else "", key=f"p_{row['emis_no']}", label_visibility="collapsed")
                    i = c4.text_input("I", value="10" if fill_i else "", key=f"i_{row['emis_no']}", label_visibility="collapsed")
                    results.append({"emis_no": row['emis_no'], "T": t, "P": p, "I": i})
                else:
                    c1, c2, c3 = st.columns([3, 1, 1])
                    c1.write(row['student_name'])
                    e = c2.text_input("E", key=f"e_{row['emis_no']}", label_visibility="collapsed")
                    i = c3.text_input("I", value="10" if fill_i else "", key=f"i_{row['emis_no']}", label_visibility="collapsed")
                    results.append({"emis_no": row['emis_no'], "T": e, "P": "", "I": i})

            if st.form_submit_button("💾 அனைத்தையும் சேமி", use_container_width=True):
                for res in results:
                    payload = {
                        "exam_id": sel_exam, "class_name": sel_class, "emis_no": res['emis_no'],
                        f"{col_prefix}_T": res['T'], f"{col_prefix}_P": res['P'], f"{col_prefix}_I": res['I']
                    }
                    # Patch: ஏற்கனவே EMIS இருந்தால் மாற்றிவிடும் (Update)
                    requests.patch(f"{MARK_API}/emis_no/{res['emis_no']}", json={"data": payload})
                st.success("வெற்றிகரமாகச் சேமிக்கப்பட்டது!")
    else: st.info("மாணவர்கள் இல்லை.")
except: st.error("பிழை!")
