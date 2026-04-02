import streamlit as st
import sys
import os

import streamlit as st
BASE_URL = st.secrets["BASE_URL"]

# இப்போது Constants கோப்பை அழைக்கிறோம்
from Constants import BASE_URL
# ... மீதி உள்ள பழைய குறியீடுகள் அப்படியே இருக்கட்டும் ...from Constants import BASE_URL 

# ... மீதி உள்ள பழைய குறியீடுகள் அப்படியே இருக்கட்டும் ... பக்கத்தின் கட்டமைப்பு
st.set_page_config(page_title="School Management System", layout="wide")
st.set_page_config(page_title="Mark Entry", layout="wide")


# ⚡ தரவுகளைப் பெறுதல்
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
# ⚡ மின்னல் வேக டிக் மற்றும் மதிப்பெண் லாஜிக் (Instant Sync)
# ---------------------------------------------------------
def sync_all():
    # 1. 'அனைவரையும் தேர்வு செய்' நிலையை எடுத்தல்
    master_val = st.session_state.master_tick
    for key in st.session_state.keys():
        if key.startswith("chk_"):
            st.session_state[key] = master_val
            
    # 2. 10 அல்லது 20 மதிப்பெண் நிலையை எடுத்தல்
    m_int = st.session_state.master_int
    m_prac = st.session_state.get('master_prac', False)
    
    for key in st.session_state.keys():
        if master_val: # டிக் இருந்தால் மட்டுமே மதிப்பெண் நிரப்பப்படும்
            if key.startswith("i_") and m_int:
                st.session_state[key] = "10"
            elif key.startswith("p_") and m_prac:
                st.session_state[key] = "20"
        else: # டிக் எடுத்தால் மதிப்பெண்களைத் துடைத்தல்
            if key.startswith("i_") or key.startswith("p_"):
                st.session_state[key] = ""

st.title("✍️ மதிப்பெண் உள்ளீடு")

exams, classes, groups, subjects, students = fetch_all()
if not exams or not classes: 
    st.info("முதலில் மற்ற விவரங்களைச் சேர்க்கவும்.")
    st.stop()

# 1. தேர்வு, வகுப்பு மற்றும் பாடத் தேர்வு
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
else: 
    st.error("பாடப்பிரிவு விவரங்கள் கண்டறியப்படவில்லை.")
    st.stop()

st.divider()

if students:
    df = pd.DataFrame(students)
    df_f = df[df['class_name'] == sel_class].sort_values(by=['Gender', 'student_name'], ascending=[True, True])
    
    if not df_f.empty:
        # 🛡️ மாஸ்டர் கண்ட்ரோல்கள்
        m1, m2, m3 = st.columns(3)
        m1.checkbox("அனைவரையும் தேர்வு செய்க / நீக்குக", key="master_tick", on_change=sync_all)
        m2.checkbox("Internal (10) வழங்குக", key="master_int", on_change=sync_all)
        if "70" in eval_type:
            m3.checkbox("Practical (20) வழங்குக", key="master_prac", on_change=sync_all)

        # 2. மதிப்பெண் படிவம்
        with st.form("final_marks_form"):
            save_data = []
            h = st.columns([0.5, 2, 1, 1, 1]) if "70" in eval_type else st.columns([0.5, 2, 1, 1])
            h[0].write("**தேர்வு**"); h[1].write("**மாணவர் பெயர்**")
            
            for _, row in df_f.iterrows():
                cols = st.columns([0.5, 2, 1, 1, 1]) if "70" in eval_type else st.columns([0.5, 2, 1, 1])
                
                # 'key' மூலம் டிக் நிலை மேலாண்மை
                s_sel = cols[0].checkbox(" ", key=f"chk_{row['emis_no']}", label_visibility="collapsed")
                cols[1].write(f"**{row['student_name']}**")
                
                if "70" in eval_type:
                    t = cols[2].text_input("Theory", key=f"t_{row['emis_no']}", label_visibility="collapsed")
                    p = cols[3].text_input("Prac", key=f"p_{row['emis_no']}", label_visibility="collapsed")
                    i = cols[4].text_input("Int", key=f"i_{row['emis_no']}", label_visibility="collapsed")
                    if s_sel:
                        save_data.append({"exam_id": sel_exam, "emis_no": row['emis_no'], f"{col_prefix}_T": t, f"{col_prefix}_P": p, f"{col_prefix}_I": i})
                else:
                    e = cols[2].text_input("Exam", key=f"e_{row['emis_no']}", label_visibility="collapsed")
                    i = cols[3].text_input("Int", key=f"i_{row['emis_no']}", label_visibility="collapsed")
                    if s_sel:
                        save_data.append({"exam_id": sel_exam, "emis_no": row['emis_no'], f"{col_prefix}_T": e, f"{col_prefix}_I": i})

            st.write("")
            if st.form_submit_button("🚀 மதிப்பெண்களைச் சேமி (Smart Update)", use_container_width=True):
                if save_data:
                    with st.spinner("சீட்டில் சேமிக்கப்படுகிறது..."):
                        requests.post(f"{BASE_URL}?sheet=Marks", json={"data": save_data}, allow_redirects=True)
                        st.success("வெற்றிகரமாக அப்டேட் செய்யப்பட்டது!")
                        st.rerun()
                else:
                    st.warning("முதலில் மாணவர்களைத் தேர்வு செய்யவும்!")
else:
    st.info("இந்த வகுப்பில் மாணவர்கள் இல்லை.")
