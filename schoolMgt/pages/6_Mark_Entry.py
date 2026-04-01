import streamlit as st
import requests
import pandas as pd

BASE_URL = "https://script.google.com/macros/s/AKfycbzgqCZ6f-kwO46eZPWb_Tr7gz-JdLQSSOL8kVLzRbhPIrinmdQrGiNjNHYIYANNPO8xYg/exec"

st.set_page_config(page_title="Fast Mark Entry", layout="wide")

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

st.title("✍️ மதிப்பெண் உள்ளீடு (Fast Update)")

exams, classes, groups, subjects, students = fetch_all()
if not exams or not classes: st.stop()

# 1. தேர்வு மற்றும் வகுப்புத் தேர்வு
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

# 2. மாணவர் பட்டியல்
if students:
    df = pd.DataFrame(students)
    df_f = df[df['class_name'] == sel_class].sort_values(by=['Gender', 'student_name'], ascending=[True, True])
    
    if not df_f.empty:
        # ⚡ Form-க்கு வெளியே உள்ள பட்டன்கள் (உடனடி மாற்றத்திற்கு)
        st.subheader("⚡ விரைவுச் செயல்பாடு")
        b1, b2, b3 = st.columns(3)
        
        # 'அனைத்தையும் தேர்வு செய்' என்பதை பட்டனாக மாற்றியுள்ளேன்
        if b1.button("✅ அனைவரையும் தேர்வு செய் / டிக் போடு"):
            for _, row in df_f.iterrows():
                st.session_state[f"sel_{row['emis_no']}"] = True
            st.rerun()

        if b2.button("🔟 அனைவருக்கும் Internal (10) இடுக"):
            for _, row in df_f.iterrows():
                st.session_state[f"i_{row['emis_no']}"] = "10"
            st.rerun()
            
        if "70" in eval_type and b3.button("🎨 அனைவருக்கும் Practical (20) இடுக"):
            for _, row in df_f.iterrows():
                st.session_state[f"p_{row['emis_no']}"] = "20"
            st.rerun()

        # 3. மதிப்பெண் உள்ளீடு செய்யும் படிவம் (Form)
        with st.form("marks_entry_final"):
            save_data = []
            # தலைப்புகள்
            h = st.columns([0.5, 2, 1, 1, 1]) if "70" in eval_type else st.columns([0.5, 2, 1, 1])
            h[0].write("தேர்வு"); h[1].write("மாணவர் பெயர்")
            
            for _, row in df_f.iterrows():
                cols = st.columns([0.5, 2, 1, 1, 1]) if "70" in eval_type else st.columns([0.5, 2, 1, 1])
                
                # Session State-ல் இருந்து மதிப்பெண்களை எடுத்தல்
                is_sel = cols[0].checkbox(" ", key=f"sel_{row['emis_no']}", label_visibility="collapsed")
                cols[1].write(f"**{row['student_name']}**")
                
                if "70" in eval_type:
                    t = cols[2].text_input("T", key=f"t_{row['emis_no']}", label_visibility="collapsed")
                    p = cols[3].text_input("P", key=f"p_{row['emis_no']}", label_visibility="collapsed")
                    i = cols[4].text_input("I", key=f"i_{row['emis_no']}", label_visibility="collapsed")
                    if is_sel:
                        save_data.append({"action": "upsert", "exam_id": sel_exam, "emis_no": row['emis_no'], f"{col_prefix}_T": t, f"{col_prefix}_P": p, f"{col_prefix}_I": i})
                else:
                    e = cols[2].text_input("E", key=f"e_{row['emis_no']}", label_visibility="collapsed")
                    i = cols[3].text_input("I", key=f"i_{row['emis_no']}", label_visibility="collapsed")
                    if is_sel:
                        save_data.append({"action": "upsert", "exam_id": sel_exam, "emis_no": row['emis_no'], f"{col_prefix}_T": e, f"{col_prefix}_I": i})

            if st.form_submit_button("🚀 மதிப்பெண்களைச் சேமி", use_container_width=True):
                if not save_data:
                    st.warning("முதலில் மாணவர்களைத் தேர்வு (Tick) செய்யவும்!")
                else:
                    with st.spinner("சீட்டில் சேமிக்கப்படுகிறது..."):
                        requests.post(f"{BASE_URL}?sheet=Marks", json={"data": save_data}, allow_redirects=True)
                        st.success("வெற்றிகரமாகச் சேமிக்கப்பட்டது!")
                        st.rerun()
