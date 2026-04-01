import streamlit as st
import requests
import pandas as pd

BASE_URL = "https://script.google.com/macros/s/AKfycbzgqCZ6f-kwO46eZPWb_Tr7gz-JdLQSSOL8kVLzRbhPIrinmdQrGiNjNHYIYANNPO8xYg/exec"

st.set_page_config(page_title="Mark Entry", layout="wide")

@st.cache_data(ttl=60)
def fetch_all():
    try:
        e = requests.get(f"{BASE_URL}?sheet=Exams", allow_redirects=True).json()
        c = requests.get(f"{BASE_URL}?sheet=Classes", allow_redirects=True).json()
        g = requests.get(f"{BASE_URL}?sheet=Groups", allow_redirects=True).json()
        s = requests.get(f"{BASE_URL}?sheet=Subjects", allow_redirects=True).json()
        st_list = requests.get(f"{BASE_URL}?sheet=Students", allow_redirects=True).json()
        return e, c, g, s, st_list
    except: return [], [], [], [], []

# ---------------------------------------------------------
# ⚡ மின்னல் வேக டிக் (Tick) லாஜிக் - Callback Function
# ---------------------------------------------------------
def update_all_ticks():
    # மாஸ்டர் செக்பாக்ஸின் மதிப்பை எடுத்து அனைத்து மாணவர் செக்பாக்ஸ்களுக்கும் கடத்துதல்
    val = st.session_state.master_tick
    for key in st.session_state.keys():
        if key.startswith("chk_"):
            st.session_state[key] = val

st.title("✍️ மதிப்பெண் உள்ளீடு")

exams, classes, groups, subjects, students = fetch_all()
if not exams or not classes: st.stop()

c1, c2 = st.columns(2)
sel_exam = c1.selectbox("தேர்வு", [e['exam_name'] for e in exams])
sel_class = c2.selectbox("வகுப்பு", [c['class_name'] for c in classes])

target_group = next((c['group_name'] for c in classes if c['class_name'] == sel_class), "")
group_info = next((g for g in groups if g['group_name'] == target_group), None)

if group_info:
    sub_list = [s.strip() for s in str(group_info['subjects']).split(',')]
    sel_sub = st.selectbox("பாடம்", sub_list)
    sub_idx = sub_list.index(sel_sub) + 1
    col_prefix = f"Sub{sub_idx}"
    sub_info = next((s for s in subjects if s['subject_name'] == sel_sub), {"eval_type": "90 + 10"})
    eval_type = sub_info['eval_type']
else: st.stop()

st.divider()

if students:
    df = pd.DataFrame(students)
    df_f = df[df['class_name'] == sel_class].sort_values(by=['Gender', 'student_name'], ascending=[True, True])
    
    if not df_f.empty:
        # 1. மாஸ்டர் செக்பாக்ஸ்கள் (Form-க்கு வெளியே)
        m1, m2, m3 = st.columns(3)
        
        # 'on_change' இருப்பதால் இதை கிளிக் செய்த உடனே 'update_all_ticks' இயங்கும்
        is_all = m1.checkbox("அனைவரையும் தேர்வு செய்க / நீக்குக", key="master_tick", on_change=update_all_ticks)
        is_int = m2.checkbox("அனைவருக்கும் Internal (10) வழங்குக", key="master_int")
        is_prac = m3.checkbox("அனைவருக்கும் Practical (20) வழங்குக", key="master_prac") if "70" in eval_type else False

        # 2. மதிப்பெண் படிவம்
        with st.form("marks_final_form"):
            save_data = []
            h = st.columns([0.5, 2, 1, 1, 1]) if "70" in eval_type else st.columns([0.5, 2, 1, 1])
            h[0].write("**தேர்வு**"); h[1].write("**மாணவர் பெயர்**")
            
            for index, row in df_f.iterrows():
                cols = st.columns([0.5, 2, 1, 1, 1]) if "70" in eval_type else st.columns([0.5, 2, 1, 1])
                
                # 'key' மூலம் செஷன் ஸ்டேட்டில் இருந்து மதிப்பை நேரடியாகப் பெறுகிறது
                s_key = f"chk_{row['emis_no']}"
                student_sel = cols[0].checkbox(" ", key=s_key, label_visibility="collapsed")
                cols[1].write(f"**{row['student_name']}**")
                
                if "70" in eval_type:
                    t = cols[2].text_input("Theory", key=f"t_{row['emis_no']}", label_visibility="collapsed")
                    p_val = "20" if (is_prac and student_sel) else ""
                    i_val = "10" if (is_int and student_sel) else ""
                    p = cols[3].text_input("Prac", value=p_val, key=f"p_{row['emis_no']}", label_visibility="collapsed")
                    i = cols[4].text_input("Int", value=i_val, key=f"i_{row['emis_no']}", label_visibility="collapsed")
                    if student_sel:
                        save_data.append({"action":"upsert","exam_id":sel_exam,"emis_no":row['emis_no'],f"{col_prefix}_T":t,f"{col_prefix}_P":p,f"{col_prefix}_I":i})
                else:
                    e = cols[2].text_input("Exam", key=f"e_{row['emis_no']}", label_visibility="collapsed")
                    i_val = "10" if (is_int and student_sel) else ""
                    i = cols[3].text_input("Int", value=i_val, key=f"i_{row['emis_no']}", label_visibility="collapsed")
                    if student_sel:
                        save_data.append({"action":"upsert","exam_id":sel_exam,"emis_no":row['emis_no'],f"{col_prefix}_T":e,f"{col_prefix}_I":i})

            if st.form_submit_button("🚀 மதிப்பெண்களைச் சேமி", use_container_width=True):
                if save_data:
                    requests.post(f"{BASE_URL}?sheet=Marks", json={"data": save_data}, allow_redirects=True)
                    st.success("வெற்றிகரமாகச் சேமிக்கப்பட்டது!")
                    st.rerun()
