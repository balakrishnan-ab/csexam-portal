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
st.title("✍️ மதிப்பெண் உள்ளீடு (Smart Entry)")

# 1. தரவுகளைப் பெறுதல்
try:
    exams = [e['exam_name'] for e in requests.get(EXAM_API).json()]
    classes_data = requests.get(CLASS_API).json()
    groups_data = requests.get(GROUP_API).json()
    subjects_data = requests.get(SUB_API).json()
    class_list = [c['class_name'] for c in classes_data]
except:
    st.error("தரவு பிழை!")
    st.stop()

# 2. தேர்வுகள்
c1, c2 = st.columns(2)
sel_exam = c1.selectbox("தேர்வு", exams)
sel_class = c2.selectbox("வகுப்பு", class_list)

target_group = next((c['group_name'] for c in classes_data if c['class_name'] == sel_class), "")
group_info = next((g for g in groups_data if g['group_name'] == target_group), None)

if group_info:
    assigned_subjects = [s.strip() for s in group_info['subjects'].split(',')]
    sel_sub = st.selectbox("பாடம்", assigned_subjects)
    sub_index = assigned_subjects.index(sel_sub) + 1
    col_prefix = f"Sub{sub_index}"
    
    # மதிப்பீட்டு முறை (90+10 or 70+20+10)
    if sub_index <= 2: eval_type = "90 + 10"
    else:
        sub_info = next((s for s in subjects_data if s['subject_name'] == sel_sub), None)
        eval_type = sub_info['eval_type'] if sub_info else "90 + 10"
else: st.stop()

st.divider()

# 3. ஸ்மார்ட் மார்க் உள்ளீடு
try:
    students = requests.get(STUDENT_API).json()
    df_f = pd.DataFrame(students)
    df_f = df_f[df_f['class_name'] == sel_class].sort_values(by=['Gender', 'student_name'])

    if not df_f.empty:
        # --- மாஸ் அப்டேட் செக்பாக்ஸ் ---
        st.subheader(f"📋 {sel_sub} ({eval_type})")
        col_check1, col_check2 = st.columns(2)
        
        fill_internal = col_check1.checkbox("அனைவருக்கும் Internal (10) நிரப்பு")
        fill_practical = False
        if "70" in eval_type:
            fill_practical = col_check2.checkbox("அனைவருக்கும் Practical (20) நிரப்பு")

        with st.form("mark_form"):
            entry_list = []
            
            # தலைப்புகள்
            t1, t2, t3, t4 = st.columns([3, 1, 1, 1])
            t1.write("**மாணவர் பெயர்**")
            if "70" in eval_type:
                t2.write("**E (70)**"); t3.write("**P (20)**"); t4.write("**I (10)**")
            else:
                t2.write("**E (90)**"); t3.write("**I (10)**")

            for _, row in df_f.iterrows():
                cols = st.columns([3, 1, 1, 1])
                cols[0].write(row['student_name'])
                
                # மதிப்பெண் பெட்டிகள் - Default மதிப்புகளுடன்
                if "70" in eval_type:
                    t_val = cols[1].text_input("T", key=f"t_{row['emis_no']}")
                    p_default = "20" if fill_practical else ""
                    i_default = "10" if fill_internal else ""
                    p_val = cols[2].text_input("P", value=p_default, key=f"p_{row['emis_no']}")
                    i_val = cols[3].text_input("I", value=i_default, key=f"i_{row['emis_no']}")
                    entry_list.append({"emis_no": row['emis_no'], "T": t_val, "P": p_val, "I": i_val})
                else:
                    ext_val = cols[1].text_input("E", key=f"e_{row['emis_no']}")
                    i_default = "10" if fill_internal else ""
                    int_val = cols[2].text_input("I", value=i_default, key=f"i_{row['emis_no']}")
                    entry_list.append({"emis_no": row['emis_no'], "T": ext_val, "P": "", "I": int_val})

            if st.form_submit_button("🚀 சேமி (Submit)", use_container_width=True):
                for item in entry_list:
                    payload = {
                        "exam_id": sel_exam, "class_name": sel_class, "emis_no": item['emis_no'],
                        f"{col_prefix}_T": item['T'], f"{col_prefix}_P": item['P'], f"{col_prefix}_I": item['I']
                    }
                    requests.patch(f"{MARK_API}/emis_no/{item['emis_no']}", json={"data": payload})
                st.success("மதிப்பெண்கள் வெற்றிகரமாகச் சேமிக்கப்பட்டன!")
    else: st.info("மாணவர்கள் இல்லை.")
except: st.error("பிழை!")
