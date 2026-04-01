import streamlit as st
import requests
import pandas as pd

# கூகுள் ஸ்கிரிப்ட் URL
BASE_URL = "https://script.google.com/macros/s/AKfycbzgqCZ6f-kwO46eZPWb_Tr7gz-JdLQSSOL8kVLzRbhPIrinmdQrGiNjNHYIYANNPO8xYg/exec"

st.set_page_config(page_title="Mark Entry", layout="wide")

# ⚡ வேகமான தரவு சேமிப்பு
@st.cache_data(ttl=60)
def fetch_all_data():
    try:
        e = requests.get(f"{BASE_URL}?sheet=Exams", allow_redirects=True).json()
        c = requests.get(f"{BASE_URL}?sheet=Classes", allow_redirects=True).json()
        g = requests.get(f"{BASE_URL}?sheet=Groups", allow_redirects=True).json()
        s = requests.get(f"{BASE_URL}?sheet=Subjects", allow_redirects=True).json()
        st_list = requests.get(f"{BASE_URL}?sheet=Students", allow_redirects=True).json()
        return e, c, g, s, st_list
    except:
        return [], [], [], [], []

st.title("✍️ மதிப்பெண் உள்ளீடு (Mark Entry)")

exams, classes, groups, subjects, students = fetch_all_data()

if not exams or not classes:
    st.warning("முதலில் தேர்வுகள் மற்றும் வகுப்புகளை உருவாக்கவும்.")
    st.stop()

# 1. தேர்வு மற்றும் வகுப்புத் தேர்வு
c1, c2 = st.columns(2)
sel_exam = c1.selectbox("தேர்வைத் தேர்ந்தெடுக்கவும்:", [e['exam_name'] for e in exams])
sel_class = c2.selectbox("வகுப்பைத் தேர்ந்தெடுக்கவும்:", [c['class_name'] for c in classes])

target_group = next((c['group_name'] for c in classes if c['class_name'] == sel_class), "")
group_info = next((g for g in groups if g['group_name'] == target_group), None)

if group_info:
    assigned_subjects = [s.strip() for s in str(group_info['subjects']).split(',')]
    sel_sub = st.selectbox("பாடத்தைத் தேர்ந்தெடுக்கவும்:", assigned_subjects)
    sub_idx = assigned_subjects.index(sel_sub) + 1
    col_prefix = f"Sub{sub_idx}"
    sub_info = next((s for s in subjects if s['subject_name'] == sel_sub), {"eval_type": "90 + 10"})
    eval_type = sub_info['eval_type']
else:
    st.error("இந்த வகுப்புக்கு பாடப்பிரிவு ஒதுக்கப்படவில்லை!")
    st.stop()

st.divider()

# 2. மாணவர் பட்டியல் மற்றும் மதிப்பெண் படிவம்
if students:
    df = pd.DataFrame(students)
    df_filtered = df[df['class_name'] == sel_class].sort_values(by=['Gender', 'student_name'], ascending=[True, True])
    
    if not df_filtered.empty:
        # ⚡ விரைவாக மதிப்பெண் இட Checkbox வசதி
        f1, f2 = st.columns(2)
        # Checkbox கிளிக் செய்ததும் மதிப்பெண்களை உடனே காட்ட on_change பயன்படுத்தலாம் அல்லது நேரடியாக value-வில் கொடுக்கலாம்
        auto_i = f1.checkbox("அனைவருக்கும் 'Internal' (10) வழங்குக")
        auto_p = f2.checkbox("அனைவருக்கும் 'Practical' (20) வழங்குக") if "70" in eval_type else False

        with st.form("marks_entry_form"):
            save_data = []
            st.markdown("---")
            h = st.columns([2, 1, 1, 1]) if "70" in eval_type else st.columns([2, 1, 1])
            h[0].write("**மாணவர் பெயர்**")
            if "70" in eval_type:
                h[1].write("**Theory (70)**")
                h[2].write("**Prac (20)**")
                h[3].write("**Int (10)**")
            else:
                h[1].write("**Exam (90)**")
                h[2].write("**Int (10)**")

            # ஒவ்வொரு மாணவருக்கும் உள்ளீடு பெட்டிகள்
            for _, row in df_filtered.iterrows():
                cols = st.columns([2, 1, 1, 1]) if "70" in eval_type else st.columns([2, 1, 1])
                cols[0].write(f"**{row['student_name']}**")
                
                # 'value' பகுதியில் checkbox நிலையைப் பொறுத்து மதிப்பெண் தானாக அமையும்
                if "70" in eval_type:
                    t = cols[1].text_input("T", key=f"t_{row['emis_no']}", label_visibility="collapsed")
                    p = cols[2].text_input("P", value="20" if auto_p else "", key=f"p_{row['emis_no']}", label_visibility="collapsed")
                    i = cols[3].text_input("I", value="10" if auto_i else "", key=f"i_{row['emis_no']}", label_visibility="collapsed")
                    save_data.append({"exam_id": sel_exam, "emis_no": row['emis_no'], f"{col_prefix}_T": t, f"{col_prefix}_P": p, f"{col_prefix}_I": i})
                else:
                    e = cols[1].text_input("E", key=f"e_{row['emis_no']}", label_visibility="collapsed")
                    i = cols[2].text_input("I", value="10" if auto_i else "", key=f"i_{row['emis_no']}", label_visibility="collapsed")
                    save_data.append({"exam_id": sel_exam, "emis_no": row['emis_no'], f"{col_prefix}_T": e, f"{col_prefix}_I": i})

            st.write("")
            if st.form_submit_button("🚀 அனைத்து மதிப்பெண்களையும் சேமி", use_container_width=True):
                with st.spinner("சேமிக்கப்படுகிறது..."):
                    # காலி மதிப்பெண்களைத் தவிர்த்துவிட்டுச் சேமித்தல்
                    for data in save_data:
                        requests.post(f"{BASE_URL}?sheet=Marks", json={"data": [data]}, allow_redirects=True)
                    st.success("வெற்றிகரமாகச் சேமிக்கப்பட்டது!")
                    st.balloons()
    else:
        st.info("இந்த வகுப்பில் மாணவர்கள் இல்லை.")
else:
    st.info("மாணவர்கள் பட்டியல் காலியாக உள்ளது.")
