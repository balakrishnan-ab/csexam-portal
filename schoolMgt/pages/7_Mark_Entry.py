import streamlit as st
import pandas as pd
from supabase import create_client
from io import BytesIO

# --- Supabase இணைப்பு ---
def get_supabase_client():
    if "supabase_instance" not in st.session_state:
        st.session_state.supabase_instance = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
    return st.session_state.supabase_instance

supabase = get_supabase_client()

st.set_page_config(page_title="Mark Entry System", layout="wide")
st.title("📊 மதிப்பெண் பதிவேற்றம் & திருத்தம்")

# --- தரவுகளைப் பெறுதல் ---
exams = supabase.table("exams").select("*").eq("exam_status", "Active").execute().data
all_classes = supabase.table("classes").select("*").execute().data
all_groups = supabase.table("groups").select("*").execute().data
all_subjects = supabase.table("subjects").select("*").execute().data

# --- தேர்வுப் பெட்டிகள் ---
c1, c2, c3 = st.columns(3)
sel_exam_name = c1.selectbox("1. தேர்வு:", ["-- தேர்வு செய்க --"] + [e['exam_name'] for e in exams])

if sel_exam_name != "-- தேர்வு செய்க --":
    exam_id = next(e['id'] for e in exams if e['exam_name'] == sel_exam_name)
    class_names = [c.get('class_n') or c.get('class_name') for c in all_classes]
    sel_class = c2.selectbox("2. வகுப்பு:", ["-- தேர்வு செய்க --"] + sorted(class_names))

    if sel_class != "-- தேர்வு செய்க --":
        # Tabs உருவாக்கம்
        tab1, tab2 = st.tabs(["👨‍🏫 பாட ஆசிரியர்", "📂 வகுப்பு ஆசிரியர் (Bulk Upload)"])

        # --- TAB 1: பாட ஆசிரியர் பகுதி ---
        with tab1:
            class_info = next((c for c in all_classes if (c.get('class_n') == sel_class or c.get('class_name') == sel_class)), None)
            subject_options = {}
            if class_info:
                group_info = next((g for g in all_groups if g['group_name'] == class_info.get('group_name')), None)
                if group_info and group_info.get('subjects'):
                    group_subs = [s.strip() for s in group_info['subjects'].split(',')]
                    for sub_name in group_subs:
                        match = next((s for s in all_subjects if s['subject_name'] == sub_name), None)
                        if match:
                            subject_options[f"{sub_name} ({match['subject_code']})"] = match
            
            sel_display_name = st.selectbox("3. பாடம்:", ["-- தேர்வு செய்க --"] + list(subject_options.keys()))

            if sel_display_name != "-- தேர்வு செய்க --":
                sub_info = subject_options[sel_display_name]
                sub_code = sub_info['subject_code']
                max_t, max_p, max_i = [int(x) for x in sub_info.get('eval_type', '90+0+10').split('+')]

                state_key = f"df_{exam_id}_{sel_class}_{sub_code}"
                if state_key not in st.session_state:
                    students = supabase.table("exam_mapping").select("exam_no, student_name, emis_no").eq("exam_id", exam_id).eq("class_name", sel_class).order("exam_no").execute().data
                    marks_dict = {m['emis_no']: m for m in supabase.table("marks").select("*").eq("exam_id", exam_id).eq("subject_id", sub_code).execute().data}
                    
                    rows = [{"Exam No": s['exam_no'], "Student Name": s['student_name'], "EMIS": s['emis_no'],
                             "Abs": marks_dict.get(s['emis_no'], {}).get('is_absent', False),
                             "Theory": marks_dict.get(s['emis_no'], {}).get('theory_mark', 0),
                             "Internal": marks_dict.get(s['emis_no'], {}).get('internal_mark', 0),
                             "Practical": marks_dict.get(s['emis_no'], {}).get('practical_mark', 0)} for s in students]
                    st.session_state[state_key] = pd.DataFrame(rows)

                with st.form("mark_form"):
                    edited_df = st.data_editor(st.session_state[state_key], hide_index=True, use_container_width=True)
                    if st.form_submit_button("🚀 சேமி"):
                        final_list = [{"exam_id": exam_id, "emis_no": row['EMIS'], "subject_id": sub_code,
                                       "theory_mark": 0 if row['Abs'] else row['Theory'],
                                       "internal_mark": 0 if row['Abs'] else row['Internal'],
                                       "practical_mark": 0 if row['Abs'] else row['Practical'],
                                       "total_mark": 0 if row['Abs'] else (row['Theory'] + row['Internal'] + row['Practical']),
                                       "is_absent": row['Abs']} for _, row in edited_df.iterrows()]
                        supabase.table("marks").upsert(final_list, on_conflict="exam_id, emis_no, subject_id").execute()
                        st.success("சேமிக்கப்பட்டது!")
                        st.rerun()

        # --- TAB 2: வகுப்பு ஆசிரியர் பகுதி (Bulk Upload) ---
        with tab2:
            st.subheader("📥 ஒட்டுமொத்த பதிவேற்றம்")
            mapping = supabase.table("exam_mapping").select("exam_no, emis_no, student_name").eq("exam_id", exam_id).eq("class_name", sel_class).execute().data
            df_template = pd.DataFrame(mapping)
            for sub in all_subjects:
                df_template[f"Theory_{sub['subject_name']}"] = 0
                df_template[f"Internal_{sub['subject_name']}"] = 0
            
            output = BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df_template.to_excel(writer, index=False)
            
            st.download_button("📥 மாணவர் பட்டியலுடன் கோப்பைத் தரவிறக்கு", data=output.getvalue(), file_name=f"Marks_{sel_class}.xlsx")
            
            uploaded_file = st.file_uploader("பூர்த்தி செய்த கோப்பைப் பதிவேற்று", type=["xlsx"])
            if uploaded_file:
                df_up = pd.read_excel(uploaded_file)
                if st.button("🚀 அனைத்து மதிப்பெண்களையும் சேமி"):
                    bulk_list = []
                    for _, row in df_up.iterrows():
                        for col in df_up.columns:
                            if "_" in col:
                                m_type, s_name = col.split("_")
                                s_code = next((s['subject_code'] for s in all_subjects if s['subject_name'] == s_name), None)
                                if s_code:
                                    val = int(row[col])
                                    item = next((i for i in bulk_list if i['emis_no'] == str(row['emis_no']) and i['subject_id'] == s_code), 
                                                {"exam_id": exam_id, "emis_no": str(row['emis_no']), "subject_id": s_code, "theory_mark": 0, "internal_mark": 0, "total_mark": 0})
                                    if m_type == "Theory": item["theory_mark"] = val
                                    elif m_type == "Internal": item["internal_mark"] = val
                                    item["total_mark"] = item["theory_mark"] + item["internal_mark"]
                                    if item not in bulk_list: bulk_list.append(item)
                    supabase.table("marks").upsert(bulk_list, on_conflict="exam_id, emis_no, subject_id").execute()
                    st.success("அனைத்து மதிப்பெண்களும் சேமிக்கப்பட்டன!")
