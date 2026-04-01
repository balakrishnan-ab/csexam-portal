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

st.title("✍️ மதிப்பெண் உள்ளீடு")

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

if students:
    df = pd.DataFrame(students)
    df_f = df[df['class_name'] == sel_class].sort_values(by=['Gender', 'student_name'], ascending=[True, True])
    
    if not df_f.empty:
        # ⚡ Master Checkboxes (Form-க்கு வெளியே)
        col_m1, col_m2, col_m3 = st.columns(3)
        
        # 'on_change' தேவையில்லை, 'value' மூலமே நேரடியாகக் கட்டுப்படுத்தலாம்
        master_sel = col_m1.checkbox("அனைவரையும் தேர்வு செய்க / நீக்குக", key="master_checkbox")
        master_i = col_m2.checkbox("அனைவருக்கும் Internal (10) வழங்குக")
        master_p = col_m3.checkbox("அனைவருக்கும் Practical (20) வழங்குக") if "70" in eval_type else False

        # 2. மதிப்பெண் படிவம்
        with st.form("marks_entry_form"):
            save_data = []
            
            # தலைப்புகள்
            cols_h = st.columns([0.5, 2, 1, 1, 1]) if "70" in eval_type else st.columns([0.5, 2, 1, 1])
            cols_h[0].write("**தேர்வு**"); cols_h[1].write("**மாணவர் பெயர்**")
            
            for index, row in df_f.iterrows():
                cols = st.columns([0.5, 2, 1, 1, 1]) if "70" in eval_type else st.columns([0.5, 2, 1, 1])
                
                # 🛡️ 'value=master_sel' என்பதால் மேலே டிக் செய்தால் இதுவும் டிக் ஆகும்
                is_sel = cols[0].checkbox(" ", value=master_sel, key=f"check_{row['emis_no']}", label_visibility="collapsed")
                cols[1].write(f"{row['student_name']}")
                
                if "70" in eval_type:
                    t = cols[2].text_input("T", key=f"t_{row['emis_no']}", label_visibility="collapsed")
                    # டிக் இருந்தால் மட்டுமே மதிப்பெண் தானாக விழும்
                    p_val = "20" if (master_p and is_sel) else ""
                    i_val = "10" if (master_i and is_sel) else ""
                    
                    p = cols[3].text_input("P", value=p_val, key=f"p_{row['emis_no']}", label_visibility="collapsed")
                    i = cols[4].text_input("I", value=i_val, key=f"i_{row['emis_no']}", label_visibility="collapsed")
                    
                    if is_sel:
                        save_data.append({"action": "upsert", "exam_id": sel_exam, "emis_no": row['emis_no'], f"{col_prefix}_T": t, f"{col_prefix}_P": p, f"{col_prefix}_I": i})
                else:
                    e = cols[2].text_input("E", key=f"e_{row['emis_no']}", label_visibility="collapsed")
                    i_val = "10" if (master_i and is_sel) else ""
                    i = cols[3].text_input("I", value=i_val, key=f"i_{row['emis_no']}", label_visibility="collapsed")
                    
                    if is_sel:
                        save_data.append({"action": "upsert", "exam_id": sel_exam, "emis_no": row['emis_no'], f"{col_prefix}_T": e, f"{col_prefix}_I": i})

            if st.form_submit_button("🚀 மதிப்பெண்களைச் சேமி", use_container_width=True):
                if not save_data:
                    st.warning("முதலில் மாணவர்களைத் தேர்வு செய்யவும்!")
                else:
                    with st.spinner("சீட்டில் சேமிக்கப்படுகிறது..."):
                        requests.post(f"{BASE_URL}?sheet=Marks", json={"data": save_data}, allow_redirects=True)
                        st.success("வெற்றிகரமாகச் சேமிக்கப்பட்டது!")
                        st.rerun()
