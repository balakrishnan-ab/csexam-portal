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

# CSS - டேபிளை மொபைலில் கச்சிதமாக்க
st.markdown("""
    <style>
    .mark-table { width: 100%; border-collapse: collapse; margin-top: 10px; }
    .mark-table th, .mark-table td { border-bottom: 1px solid #ddd; padding: 8px 4px; text-align: left; }
    .mark-table th { background-color: #f8f9fa; font-size: 12px; }
    .mark-input { width: 50px; padding: 5px; text-align: center; border: 1px solid #ccc; border-radius: 4px; }
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

col_a, col_b = st.columns(2)
sel_exam = col_a.selectbox("தேர்வு", exams)
sel_class = col_b.selectbox("வகுப்பு", class_list)

# பாடப்பிரிவு மற்றும் பாடங்களைக் கண்டறிதல்
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

# 3. மார்க் என்ட்ரி பகுதி
try:
    students = requests.get(STUDENT_API).json()
    df_f = pd.DataFrame(students)
    df_f = df_f[df_f['class_name'] == sel_class].sort_values(by=['Gender', 'student_name'])

    if not df_f.empty:
        # Streamlit-ன் form-ஐப் பயன்படுத்தியே HTML அமைப்பைக் கொண்டு வருகிறோம்
        with st.form("marks_form"):
            # Table Header
            if "70" in eval_type:
                h1, h2, h3, h4 = st.columns([3, 1, 1, 1])
                h1.write("**மாணவர் பெயர்**"); h2.write("**E(70)**"); h3.write("**P(20)**"); h4.write("**I(10)**")
            else:
                h1, h2, h3 = st.columns([3, 1, 1])
                h1.write("**மாணவர் பெயர்**"); h2.write("**E(90)**"); h3.write("**I(10)**")
            
            st.markdown("---")
            
            results = []
            for _, row in df_f.iterrows():
                # இங்கு columns-க்கு சிறிய விகிதங்களைக் கொடுப்பதால் மொபைலில் மடியாது
                if "70" in eval_type:
                    c1, c2, c3, c4 = st.columns([3.5, 1, 1, 1])
                    c1.markdown(f"<p style='margin-top:10px;'>{row['student_name']}</p>", unsafe_allow_html=True)
                    t = c2.text_input("T", key=f"t_{row['emis_no']}", label_visibility="collapsed")
                    p = c3.text_input("P", value="20" if fill_p else "", key=f"p_{row['emis_no']}", label_visibility="collapsed")
                    i = c4.text_input("I", value="10" if fill_i else "", key=f"i_{row['emis_no']}", label_visibility="collapsed")
                    results.append({"emis_no": row['emis_no'], "T": t, "P": p, "I": i})
                else:
                    c1, c2, c3 = st.columns([4, 1.2, 1.2])
                    c1.markdown(f"<p style='margin-top:10px;'>{row['student_name']}</p>", unsafe_allow_html=True)
                    e = c2.text_input("E", key=f"e_{row['emis_no']}", label_visibility="collapsed")
                    i = c3.text_input("I", value="10" if fill_i else "", key=f"i_{row['emis_no']}", label_visibility="collapsed")
                    results.append({"emis_no": row['emis_no'], "T": e, "P": "", "I": i})

            if st.form_submit_button("💾 அனைத்தையும் சேமி", use_container_width=True):
                for res in results:
                    payload = {
                        "exam_id": sel_exam, "class_name": sel_class, "emis_no": res['emis_no'],
                        f"{col_prefix}_T": res['T'], f"{col_prefix}_P": res['P'], f"{col_prefix}_I": res['I']
                    }
                    # Update (Patch) - EMIS எண் அடையாளமாகப் பயன்படுத்தப்படுகிறது
                    requests.patch(f"{MARK_API}/emis_no/{res['emis_no']}", json={"data": payload})
                st.success("வெற்றிகரமாகச் சேமிக்கப்பட்டது!")
    else: st.info("மாணவர்கள் இல்லை.")
except: st.error("பிழை!")
