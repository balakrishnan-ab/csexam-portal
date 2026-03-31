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

# CSS - மொபைலில் கச்சிதமாகத் தெரிய
st.markdown("""
    <style>
    .mark-row { border-bottom: 1px solid #f0f2f6; padding: 5px 0px; align-items: center; }
    .stTextInput input { padding: 5px; text-align: center; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

st.title("✍️ மதிப்பெண் உள்ளீடு")

# 1. தரவுகளைப் பெறுதல்
try:
    exams_res = requests.get(EXAM_API).json()
    exams = [e['exam_name'] for e in exams_res] if isinstance(exams_res, list) else []
    classes_data = requests.get(CLASS_API).json()
    groups_data = requests.get(GROUP_API).json()
    subjects_data = requests.get(SUB_API).json()
    class_list = [c['class_name'] for c in classes_data]
except:
    st.error("தரவு பிழை! API-ஐச் சரிபார்க்கவும்.")
    st.stop()

# 2. தேர்வு மற்றும் வகுப்புத் தெரிவு
col_a, col_b = st.columns(2)
sel_exam = col_a.selectbox("தேர்வு", exams)
sel_class = col_b.selectbox("வகுப்பு", class_list)

# பாடப்பிரிவு மற்றும் பாடங்களைக் கண்டறிதல்
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
else: 
    st.warning("இந்தப் பிரிவிற்கு பாடங்கள் ஒதுக்கப்படவில்லை!")
    st.stop()

st.divider()

# 3. ஸ்மார்ட் மார்க் உள்ளீடு
try:
    students_res = requests.get(STUDENT_API).json()
    df_f = pd.DataFrame(students_res)
    df_f = df_f[df_f['class_name'] == sel_class].sort_values(by=['Gender', 'student_name'])

    if not df_f.empty:
        st.subheader(f"📋 {sel_sub} ({eval_type})")
        
        # 'Select All' வசதி
        c_fill1, c_fill2 = st.columns(2)
        fill_internal = c_fill1.checkbox("அனைவருக்கும் Internal (10) நிரப்பு")
        fill_practical = False
        if "70" in eval_type:
            fill_practical = c_fill2.checkbox("அனைவருக்கும் Practical (20) நிரப்பு")

        with st.form("mark_form"):
            # அட்டவணைத் தலைப்பு
            if "70" in eval_type:
                h_name, h_t, h_p, h_i = st.columns([3, 1, 1, 1])
                h_name.write("**மாணவர் பெயர்**")
                h_t.write("**E(70)**"); h_p.write("**P(20)**"); h_i.write("**I(10)**")
            else:
                h_name, h_e, h_i = st.columns([3, 1, 1])
                h_name.write("**மாணவர் பெயர்**")
                h_e.write("**E(90)**"); h_i.write("**I(10)**")
            
            st.markdown("---")
            
            entry_list = []
            for _, row in df_f.iterrows():
                # ஒரே வரிசையில் (Horizontal) அமைத்தல்
                if "70" in eval_type:
                    c_n, c_t, c_p, c_i = st.columns([3, 1, 1, 1])
                    c_n.write(f"**{row['student_name']}**")
                    t_val = c_t.text_input("T", key=f"t_{row['emis_no']}", label_visibility="collapsed")
                    p_val = c_p.text_input("P", value="20" if fill_practical else "", key=f"p_{row['emis_no']}", label_visibility="collapsed")
                    i_val = c_i.text_input("I", value="10" if fill_internal else "", key=f"i_{row['emis_no']}", label_visibility="collapsed")
                    entry_list.append({"emis_no": row['emis_no'], "T": t_val, "P": p_val, "I": i_val})
                else:
                    c_n, c_e, c_i = st.columns([3, 1, 1])
                    c_n.write(f"**{row['student_name']}**")
                    e_val = c_e.text_input("E", key=f"e_{row['emis_no']}", label_visibility="collapsed")
                    i_val = c_i.text_input("I", value="10" if fill_internal else "", key=f"i_{row['emis_no']}", label_visibility="collapsed")
                    entry_list.append({"emis_no": row['emis_no'], "T": e_val, "P": "", "I": i_val})

            if st.form_submit_button("🚀 சேமி (Submit)", use_container_width=True):
                for item in entry_list:
                    payload = {
                        "exam_id": sel_exam, "class_name": sel_class, "emis_no": item['emis_no'],
                        f"{col_prefix}_T": item['T'], f"{col_prefix}_P": item['P'], f"{col_prefix}_I": item['I']
                    }
                    # ஒரு மாணவருக்கு ஒரு Row இருக்கிறதா எனப் பார்த்து Patch அல்லது Post செய்யும்
                    requests.patch(f"{MARK_API}/emis_no/{item['emis_no']}", json={"data": payload})
                st.success("மதிப்பெண்கள் வெற்றிகரமாகச் சேமிக்கப்பட்டன!")
    else: st.info("மாணவர்கள் இல்லை.")
except: st.error("பிழை! API இணைப்பைச் சரிபார்க்கவும்.")
