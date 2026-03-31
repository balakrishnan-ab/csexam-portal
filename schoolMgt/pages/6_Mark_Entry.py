import streamlit as st
import requests
import pandas as pd

# 1. உங்கள் புதிய Google Web App URL (கடைசியில் /exec இருப்பதை உறுதி செய்யவும்)
BASE_URL = "https://script.google.com/macros/s/AKfycbwi1fAX0GjXwzVLTFPZY0Tz_IKMbdphRM_uclgrVBILlhOpM0vgJoE1RVVUTUTE13p6-A/exec"

# தரவுகளைப் பெறுவதற்கான பொதுவான பங்க்ஷன்
def get_data(sheet_name):
    try:
        url = f"{BASE_URL}?sheet={sheet_name}"
        # கூகுள் ஸ்கிரிப்ட் என்பதால் follow_redirects=True மிக முக்கியம்
        response = requests.get(url, follow_redirects=True)
        return response.json()
    except:
        return []

st.set_page_config(page_title="Mark Entry", layout="wide")

# CSS - பெட்டிகளை மிக நெருக்கமாகக் கொண்டு வருதல்
st.markdown("""
    <style>
    [data-testid="column"] { flex: 1 1 0% !important; min-width: 0px !important; padding: 0px 1px !important; gap: 0px !important; }
    div[data-testid="stTextInput"] > div > div > input { padding: 4px 1px !important; font-size: 14px !important; text-align: center !important; height: 30px !important; width: 100% !important; }
    .std-name { font-size: 12px !important; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; margin-top: 6px; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

st.title("✍️ மதிப்பெண் உள்ளீடு")

# 2. தரவுகளைப் பெறுதல்
exams_data = get_data("Exams")
classes_data = get_data("Classes")
groups_data = get_data("Groups")
subjects_data = get_data("Subjects")

if not exams_data:
    st.error("API தரவு கிடைக்கவில்லை! URL அல்லது Google Script-ஐச் சரிபார்க்கவும்.")
    st.stop()

exams = [e['exam_name'] for e in exams_data]
class_list = [c['class_name'] for c in classes_data]

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

# 3. ஸ்மார்ட் ஃபில் மற்றும் மார்க் என்ட்ரி
students_data = get_data("Students")
df_f = pd.DataFrame(students_data)
if not df_f.empty:
    df_f = df_f[df_f['class_name'] == sel_class].sort_values(by=['Gender', 'student_name'])

    cf1, cf2 = st.columns(2)
    fill_i = cf1.checkbox("I (10) அனைவருக்கும்")
    fill_p = cf2.checkbox("P (20) அனைவருக்கும்") if "70" in eval_type else False

    with st.form("mark_entry_form"):
        h = st.columns([1.2, 1, 1, 1]) if "70" in eval_type else st.columns([1.2, 1, 1])
        h[0].write("**பெயர்**")
        
        save_list = []
        for _, row in df_f.iterrows():
            c = st.columns([1.2, 1, 1, 1]) if "70" in eval_type else st.columns([1.2, 1, 1])
            c[0].markdown(f"<p class='std-name'>{row['student_name']}</p>", unsafe_allow_html=True)
            
            if "70" in eval_type:
                t = c[1].text_input("T", key=f"t_{row['emis_no']}", label_visibility="collapsed")
                p = c[2].text_input("P", value="20" if fill_p else "", key=f"p_{row['emis_no']}", label_visibility="collapsed")
                i = c[3].text_input("I", value="10" if fill_i else "", key=f"i_{row['emis_no']}", label_visibility="collapsed")
                save_list.append({"exam_id": sel_exam, "class_name": sel_class, "emis_no": row['emis_no'], f"{col_prefix}_T": t, f"{col_prefix}_P": p, f"{col_prefix}_I": i})
            else:
                e = c[1].text_input("E", key=f"e_{row['emis_no']}", label_visibility="collapsed")
                i = c[2].text_input("I", value="10" if fill_i else "", key=f"i_{row['emis_no']}", label_visibility="collapsed")
                save_list.append({"exam_id": sel_exam, "class_name": sel_class, "emis_no": row['emis_no'], f"{col_prefix}_T": e, f"{col_prefix}_P": "", f"{col_prefix}_I": i})

        if st.form_submit_button("🚀 சேமி (Submit)", use_container_width=True):
            for payload in save_list:
                # கூகுள் ஸ்கிரிப்டிற்கு POST முறையில் தரவை அனுப்புதல்
                requests.post(f"{BASE_URL}?sheet=Marks", json={"data": [payload]}, follow_redirects=True)
            st.success("வெற்றிகரமாகச் சேமிக்கப்பட்டது!")
else:
    st.info("மாணவர்கள் இல்லை.")
