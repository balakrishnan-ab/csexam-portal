import streamlit as st
import requests
import pandas as pd

BASE_URL = "https://script.google.com/macros/s/AKfycbzgqCZ6f-kwO46eZPWb_Tr7gz-JdLQSSOL8kVLzRbhPIrinmdQrGiNjNHYIYANNPO8xYg/exec"

st.set_page_config(page_title="Mark Entry", layout="wide")

@st.cache_data(ttl=60)
def fetch_all_data():
    try:
        e = requests.get(f"{BASE_URL}?sheet=Exams", allow_redirects=True).json()
        c = requests.get(f"{BASE_URL}?sheet=Classes", allow_redirects=True).json()
        g = requests.get(f"{BASE_URL}?sheet=Groups", allow_redirects=True).json()
        s = requests.get(f"{BASE_URL}?sheet=Subjects", allow_redirects=True).json()
        st_list = requests.get(f"{BASE_URL}?sheet=Students", allow_redirects=True).json()
        return e, c, g, s, st_list
    except: return [], [], [], [], []

st.title("✍️ மதிப்பெண் உள்ளீடு")

exams, classes, groups, subjects, students = fetch_all_data()

if not exams or not classes:
    st.stop()

c1, c2 = st.columns(2)
sel_exam = c1.selectbox("தேர்வு", [e['exam_name'] for e in exams])
sel_class = c2.selectbox("வகுப்பு", [c['class_name'] for c in classes])

target_group = next((c['group_name'] for c in classes if c['class_name'] == sel_class), "")
group_info = next((g for g in groups if g['group_name'] == target_group), None)

if group_info:
    assigned_subjects = [s.strip() for s in str(group_info['subjects']).split(',')]
    sel_sub = st.selectbox("பாடம்", assigned_subjects)
    sub_idx = assigned_subjects.index(sel_sub) + 1
    col_prefix = f"Sub{sub_idx}"
    sub_info = next((s for s in subjects if s['subject_name'] == sel_sub), {"eval_type": "90 + 10"})
    eval_type = sub_info['eval_type']
else: st.stop()

st.divider()

if students:
    df = pd.DataFrame(students)
    df_filtered = df[df['class_name'] == sel_class].sort_values(by=['Gender', 'student_name'], ascending=[True, True])
    
    if not df_filtered.empty:
        # ⚡ முக்கிய மாற்றம்: இவை Form-க்கு வெளியே இருக்க வேண்டும்
        f1, f2 = st.columns(2)
        auto_i = f1.checkbox("அனைவருக்கும் 'Internal' (10) வழங்குக")
        auto_p = f2.checkbox("அனைவருக்கும் 'Practical' (20) வழங்குக") if "70" in eval_type else False

        # Form தொடங்குகிறது
        with st.form("marks_entry_form"):
            save_data = []
            
            # தலைப்புகள்
            h = st.columns([2, 1, 1, 1]) if "70" in eval_type else st.columns([2, 1, 1])
            h[0].write("**மாணவர் பெயர்**")
            if "70" in eval_type:
                h[1].write("**Theory (70)**")
                h[2].write("**Prac (20)**")
                h[3].write("**Int (10)**")
            else:
                h[1].write("**Exam (90)**")
                h[2].write("**Int (10)**")

            for _, row in df_filtered.iterrows():
                cols = st.columns([2, 1, 1, 1]) if "70" in eval_type else st.columns([2, 1, 1])
                cols[0].write(f"{row['student_name']}")
                
                # value பகுதியில் auto_i மற்றும் auto_p சரியாகப் பொருத்தப்பட்டுள்ளது
                if "70" in eval_type:
                    t_val = st.session_state.get(f"t_{row['emis_no']}", "")
                    t = cols[1].text_input("T", value=t_val, key=f"t_{row['emis_no']}", label_visibility="collapsed")
                    p = cols[2].text_input("P", value="20" if auto_p else "", key=f"p_{row['emis_no']}", label_visibility="collapsed")
                    i = cols[3].text_input("I", value="10" if auto_i else "", key=f"i_{row['emis_no']}", label_visibility="collapsed")
                    save_data.append({"exam_id": sel_exam, "emis_no": row['emis_no'], f"{col_prefix}_T": t, f"{col_prefix}_P": p, f"{col_prefix}_I": i})
                else:
                    e_val = st.session_state.get(f"e_{row['emis_no']}", "")
                    e = cols[1].text_input("E", value=e_val, key=f"e_{row['emis_no']}", label_visibility="collapsed")
                    i = cols[2].text_input("I", value="10" if auto_i else "", key=f"i_{row['emis_no']}", label_visibility="collapsed")
                    save_data.append({"exam_id": sel_exam, "emis_no": row['emis_no'], f"{col_prefix}_T": e, f"{col_prefix}_I": i})

            if st.form_submit_button("🚀 சேமி (Submit)", use_container_width=True):
                for data in save_data:
                    requests.post(f"{BASE_URL}?sheet=Marks", json={"data": [data]}, allow_redirects=True)
                st.success("வெற்றிகரமாகச் சேமிக்கப்பட்டது!")
                st.balloons()
