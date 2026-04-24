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

# --- தேர்வு ---
sel_exam_name = st.selectbox("தேர்வைத் தேர்ந்தெடுக்கவும்:", ["-- தேர்வு செய்க --"] + [e['exam_name'] for e in exams])

if sel_exam_name != "-- தேர்வு செய்க --":
    exam_id = next(e['id'] for e in exams if e['exam_name'] == sel_exam_name)
    class_list = sorted(list(set([c.get('class_n') or c.get('class_name') for c in all_classes])))
    sel_class = st.selectbox("வகுப்பைத் தேர்ந்தெடுக்கவும்:", ["-- தேர்வு செய்க --"] + class_list)

    if sel_class != "-- தேர்வு செய்க --":
        tab1, tab2, tab3 = st.tabs(["👨‍🏫 பாட ஆசிரியர்", "📂 வகுப்பு ஆசிரியர் (Bulk)", "🏢 வகுப்பின் அனைத்துப் பிரிவுகள்"])

        # --- TAB 1: பாட ஆசிரியர் ---
        with tab1:
            class_info = next((c for c in all_classes if (c.get('class_n') == sel_class or c.get('class_name') == sel_class)), None)
            group_name = class_info.get('group_name') if class_info else None
            group_info = next((g for g in all_groups if g['group_name'] == group_name), None)
            sub_names = [s.strip() for s in group_info['subjects'].split(',')] if group_info else []
            
            sel_sub_name = st.selectbox("பாடம்:", ["-- தேர்வு செய்க --"] + sub_names)
            
            if sel_sub_name != "-- தேர்வு செய்க --":
                sub_info = next((s for s in all_subjects if s['subject_name'] == sel_sub_name), None)
                sub_code = sub_info['subject_code']
                eval_parts = str(sub_info.get('eval_type', '100')).split('+')
                
                students = supabase.table("exam_mapping").select("exam_no, student_name, emis_no").eq("exam_id", exam_id).eq("class_name", sel_class).execute().data
                marks_db = supabase.table("marks").select("*").eq("exam_id", exam_id).eq("subject_id", sub_code).execute().data
                marks_dict = {m['emis_no']: m for m in marks_db}
                
                rows = [{"Exam No": s['exam_no'], "Student Name": s['student_name'], "EMIS": s['emis_no'],
                         "Abs": marks_dict.get(s['emis_no'], {}).get('is_absent', False),
                         "Theory": marks_dict.get(s['emis_no'], {}).get('theory_mark', 0),
                         "Internal": marks_dict.get(s['emis_no'], {}).get('internal_mark', 0),
                         "Practical": marks_dict.get(s['emis_no'], {}).get('practical_mark', 0)} for s in students]
                
                edited_df = st.data_editor(pd.DataFrame(rows), hide_index=True, use_container_width=True)
                if st.button("🚀 பாட மதிப்பெண் சேமி"):
                    final_data = [{"exam_id": exam_id, "emis_no": r['EMIS'], "subject_id": sub_code,
                                   "theory_mark": 0 if r['Abs'] else r['Theory'],
                                   "internal_mark": 0 if r['Abs'] else r['Internal'],
                                   "practical_mark": 0 if r['Abs'] else r['Practical'],
                                   "total_mark": 0 if r['Abs'] else (r['Theory'] + r['Internal'] + r['Practical']),
                                   "is_absent": r['Abs']} for _, r in edited_df.iterrows()]
                    supabase.table("marks").upsert(final_data, on_conflict="exam_id, emis_no, subject_id").execute()
                    st.success("சேமிக்கப்பட்டது!")

        # --- TAB 2 & 3: Bulk Upload Logic ---
        def process_bulk_upload(target_classes):
            for cls in target_classes:
                mapping = supabase.table("exam_mapping").select("emis_no, student_name").eq("exam_id", exam_id).eq("class_name", cls['class_n']).execute().data
                df_temp = pd.DataFrame(mapping)
                g_info = next((g for g in all_groups if g['group_name'] == cls['group_name']), None)
                sub_names = g_info['subjects'].split(',') if g_info else []
                
                for s_name in sub_names:
                    s_name = s_name.strip()
                    sub_data = next((s for s in all_subjects if s['subject_name'] == s_name), None)
                    if sub_data and sub_data.get('eval_type') != 'NIL':
                        df_temp[f"Theory_{s_name}"] = 0
                        if len(str(sub_data.get('eval_type')).split('+')) >= 2: df_temp[f"Internal_{s_name}"] = 0
                        if len(str(sub_data.get('eval_type')).split('+')) == 3: df_temp[f"Practical_{s_name}"] = 0
                return df_temp

        with tab2:
            st.subheader("📂 வகுப்பு ஆசிரியர் பகுதி")
            df_b = process_bulk_upload([class_info])
            output = BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer: df_b.to_excel(writer, index=False)
            st.download_button("📥 வகுப்பு கோப்பைத் தரவிறக்கு", data=output.getvalue(), file_name=f"Marks_{sel_class}.xlsx")
            
        with tab3:
            st.subheader("🏢 வகுப்பின் அனைத்துப் பிரிவுகள்")
            grade_val = st.text_input("வகுப்பு எண் (எ.கா: 12):")
            if grade_val:
                relevant = [c for c in all_classes if c['class_n'].startswith(grade_val)]
                df_all = process_bulk_upload(relevant)
                output = BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer: df_all.to_excel(writer, index=False)
                st.download_button("📥 அனைத்து குரூப் கோப்பைப் பெற", data=output.getvalue(), file_name=f"Marks_{grade_val}_All.xlsx")
