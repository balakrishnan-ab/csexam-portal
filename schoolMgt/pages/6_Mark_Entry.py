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

# CSS - பெயருக்கு 30% மற்றும் பெட்டிகளுக்கு 15% அளவில் சுருக்குதல்
st.markdown("""
    <style>
    /* காலம்களை மிக நெருக்கமாக மாற்றுதல் */
    [data-testid="column"] {
        flex: 1 1 0% !important;
        min-width: 0px !important;
        padding: 0px 1px !important;
    }
    /* இன்புட் பாக்ஸ் அளவை 15% இடத்திற்குள் சுருக்குதல் */
    div[data-testid="stTextInput"] > div > div > input {
        padding: 4px 1px !important;
        font-size: 14px !important;
        text-align: center !important;
        height: 30px !important;
        width: 100% !important;
    }
    /* மாணவர் பெயர் ஸ்டைல் - 30% இடத்திற்குள் */
    .std-name {
        font-size: 12px !important;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        margin-top: 6px;
        color: #333;
        font-weight: bold;
    }
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
    st.error("API தரவுகளைப் பெறுவதில் பிழை!")
    st.stop()

col_a, col_b = st.columns(2)
sel_exam = col_a.selectbox("தேர்வு", exams)
sel_class = col_b.selectbox("வகுப்பு", class_list)

# பாடப்பிரிவு கண்டறிதல்
target_group = next((c['group_name'] for c in classes_data if c['class_name'] == sel_class), "")
group_info = next((g for g in groups_data if g['group_name'] == target_group), None)

if group_info:
    assigned_subjects = [s.strip() for s in group_info['subjects'].split(',')]
    sel_sub = st.selectbox("பாடம்", assigned_subjects)
    sub_idx = assigned_subjects.index(sel_sub) + 1
    col_prefix = f"Sub{sub_idx}"
    eval_type = "90 + 10" if sub_idx <= 2 else next((s['eval_type'] for s in subjects_data if s['subject_name'] == sel_sub), "90 + 10")
else: st.stop()

st.divider()

# 2. ஸ்மார்ட் ஃபில் (Smart Fill)
cf1, cf2 = st.columns(2)
fill_i = cf1.checkbox("I (10) அனைவருக்கும்")
fill_p = cf2.checkbox("P (20) அனைவருக்கும்") if "70" in eval_type else False

# 3. காம்பாக்ட் மார்க் என்ட்ரி (30% - 15% - 15% - 15% விகிதம்)
try:
    students_res = requests.get(STUDENT_API).json()
    df_f = pd.DataFrame(students_res)
    df_f = df_f[df_f['class_name'] == sel_class].sort_values(by=['Gender', 'student_name'])

    if not df_f.empty:
        with st.form("ultra_compact_form"):
            # விகிதம் [2, 1, 1, 1] - பெயர் 2 பங்கு, மற்றவை 1 பங்கு (தோராயமாக 30% - 15% - 15% - 15%)
            if "70" in eval_type:
                h = st.columns([2, 1, 1, 1])
                h[0].write("**பெயர்**"); h[1].write("**E70**"); h[2].write("**P20**"); h[3].write("**I10**")
            else:
                h = st.columns([2, 1, 1])
                h[0].write("**பெயர்**"); h[1].write("**E90**"); h[2].write("**I10**")
            
            st.markdown("---")
            
            save_list = []
            for _, row in df_f.iterrows():
                if "70" in eval_type:
                    c = st.columns([2, 1, 1, 1])
                    c[0].markdown(f"<p class='std-name'>{row['student_name']}</p>", unsafe_allow_html=True)
                    t = c[1].text_input("T", key=f"t_{row['emis_no']}", label_visibility="collapsed")
                    p = c[2].text_input("P", value="20" if fill_p else "", key=f"p_{row['emis_no']}", label_visibility="collapsed")
                    i = c[3].text_input("I", value="10" if fill_i else "", key=f"i_{row['emis_no']}", label_visibility="collapsed")
                    save_list.append({"emis_no": row['emis_no'], "T": t, "P": p, "I": i})
                else:
                    c = st.columns([2, 1, 1])
                    c[0].markdown(f"<p class='std-name'>{row['student_name']}</p>", unsafe_allow_html=True)
                    e = c[1].text_input("E", key=f"e_{row['emis_no']}", label_visibility="collapsed")
                    i = c[2].text_input("I", value="10" if fill_i else "", key=f"i_{row['emis_no']}", label_visibility="collapsed")
                    save_list.append({"emis_no": row['emis_no'], "T": e, "P": "", "I": i})

            if st.form_submit_button("🚀 சேமி (Submit)", use_container_width=True):
                for item in save_list:
                    payload = {
                        "exam_id": sel_exam, "class_name": sel_class, "emis_no": item['emis_no'],
                        f"{col_prefix}_T": item['T'], f"{col_prefix}_P": item['P'], f"{col_prefix}_I": item['I']
                    }
                    requests.patch(f"{MARK_API}/emis_no/{item['emis_no']}", json={"data": payload})
                st.success("வெற்றிகரமாகச் சேமிக்கப்பட்டது!")
    else: st.info("மாணவர்கள் இல்லை.")
except: st.error("பிழை!")
