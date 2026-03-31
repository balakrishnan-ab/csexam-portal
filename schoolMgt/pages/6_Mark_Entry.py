import streamlit as st
import requests
import pandas as pd

# API URLs - உங்கள் URL சரியாக இருக்கிறதா என ஒருமுறை உறுதி செய்யவும்
STUDENT_API = "https://sheetdb.io/api/v1/sb3mxuvdynqos?sheet=Students"
EXAM_API = "https://sheetdb.io/api/v1/sb3mxuvdynqos?sheet=Exams"
CLASS_API = "https://sheetdb.io/api/v1/sb3mxuvdynqos?sheet=Classes"
GROUP_API = "https://sheetdb.io/api/v1/sb3mxuvdynqos?sheet=Groups"
SUB_API = "https://sheetdb.io/api/v1/sb3mxuvdynqos?sheet=Subjects"
MARK_API = "https://sheetdb.io/api/v1/sb3mxuvdynqos?sheet=Marks"

st.set_page_config(page_title="Mark Entry", layout="wide")

# CSS - கச்சிதமான தோற்றம்
st.markdown("""
    <style>
    [data-testid="column"] { flex: 1 1 0% !important; min-width: 0px !important; padding: 0px 1px !important; gap: 0px !important; }
    div[data-testid="stTextInput"] > div > div > input { padding: 4px 1px !important; font-size: 14px !important; text-align: center !important; height: 30px !important; width: 100% !important; }
    .std-name { font-size: 12px !important; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; margin-top: 6px; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

st.title("✍️ மதிப்பெண் உள்ளீடு")

# 1. தரவுகளைப் பெற்றுச் சரிபார்த்தல்
try:
    exams_res = requests.get(EXAM_API)
    if exams_res.status_code != 200:
        st.error(f"Exams API பிழை! கூகுள் சீட்டில் 'Exams' தாள் இருக்கிறதா எனப் பார்க்கவும். (Code: {exams_res.status_code})")
        st.stop()
    
    exams_data = exams_res.json()
    exams = [e['exam_name'] for e in exams_data] if isinstance(exams_data, list) else []
    
    classes_data = requests.get(CLASS_API).json()
    groups_data = requests.get(GROUP_API).json()
    subjects_data = requests.get(SUB_API).json()
    class_list = [c['class_name'] for c in classes_data]

    # --- மற்ற பகுதிகள் முன்பு இருந்தது போலவே ---
    col_a, col_b = st.columns(2)
    sel_exam = col_a.selectbox("தேர்வு", exams)
    sel_class = col_b.selectbox("வகுப்பு", class_list)

    target_group = next((c['group_name'] for c in classes_data if c['class_name'] == sel_class), "")
    group_info = next((g for g in groups_data if g['group_name'] == target_group), None)

    if group_info:
        assigned_subjects = [s.strip() for s in group_info['subjects'].split(',')]
        sel_sub = st.selectbox("பாடம்", assigned_subjects)
        sub_idx = assigned_subjects.index(sel_sub) + 1
        col_prefix = f"Sub{sub_idx}"
        eval_type = "90 + 10" if sub_idx <= 2 else next((s['eval_type'] for s in subjects_data if s['subject_name'] == sel_sub), "90 + 10")
    else:
        st.warning("பாடம் ஒதுக்கப்படவில்லை.")
        st.stop()

    st.divider()

    # 2. மாணவர் பட்டியலைப் பெற்று மார்க் போடுதல்
    students_data = requests.get(STUDENT_API).json()
    df_f = pd.DataFrame(students_data)
    df_f = df_f[df_f['class_name'] == sel_class].sort_values(by=['Gender', 'student_name'])

    if not df_f.empty:
        # Checkbox Logic
        cf1, cf2 = st.columns(2)
        fill_i = cf1.checkbox("Internal (10) அனைவருக்கும்")
        fill_p = cf2.checkbox("Practical (20) அனைவருக்கும்") if "70" in eval_type else False

        with st.form("mark_entry_form"):
            h = st.columns([1.2, 1, 1, 1]) if "70" in eval_type else st.columns([1.2, 1, 1])
            h[0].write("**பெயர்**")
            # ... தலைப்புகள் ...
            
            save_list = []
            for _, row in df_f.iterrows():
                c = st.columns([1.2, 1, 1, 1]) if "70" in eval_type else st.columns([1.2, 1, 1])
                c[0].markdown(f"<p class='std-name'>{row['student_name']}</p>", unsafe_allow_html=True)
                
                if "70" in eval_type:
                    t = c[1].text_input("T", key=f"t_{row['emis_no']}", label_visibility="collapsed")
                    p = c[2].text_input("P", value="20" if fill_p else "", key=f"p_{row['emis_no']}", label_visibility="collapsed")
                    i = c[3].text_input("I", value="10" if fill_i else "", key=f"i_{row['emis_no']}", label_visibility="collapsed")
                    save_list.append({"emis_no": row['emis_no'], "T": t, "P": p, "I": i})
                else:
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
    else:
        st.info("மாணவர்கள் இல்லை.")

except Exception as e:
    st.error(f"பிழை விவரம்: {e}")
