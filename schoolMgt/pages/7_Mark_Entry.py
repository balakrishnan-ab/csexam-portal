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
    class_list = sorted(list(set([c['class_name'] for c in all_classes])))
    sel_class = st.selectbox("வகுப்பைத் தேர்ந்தெடுக்கவும்:", ["-- தேர்வு செய்க --"] + class_list)

    if sel_class != "-- தேர்வு செய்க --":
        tab1, tab2, tab3 = st.tabs(["👨‍🏫 பாட ஆசிரியர்", "📂 வகுப்பு ஆசிரியர் (Bulk)", "🏢 வகுப்பின் அனைத்துப் பிரிவுகள்"])

        # --- TAB 1: பாட ஆசிரியர் தர்க்கம் ---
        with tab1:
            class_info = next((c for c in all_classes if c['class_name'] == sel_class), None)
            g_info = next((g for g in all_groups if g['group_name'] == class_info.get('group_name')), None)
            sub_names = [s.strip() for s in g_info['subjects'].split(',')] if g_info else []
            sel_sub = st.selectbox("பாடம்:", ["-- தேர்வு செய்க --"] + sub_names)
            
            if sel_sub != "-- தேர்வு செய்க --":
                sub_data = next((s for s in all_subjects if s['subject_name'] == sel_sub), None)
                sub_code = sub_data['subject_code']
                
                students = supabase.table("exam_mapping").select("exam_no, student_name, emis_no").eq("exam_id", exam_id).eq("class_name", sel_class).execute().data
                marks_db = supabase.table("marks").select("*").eq("exam_id", exam_id).eq("subject_id", sub_code).execute().data
                marks_dict = {m['emis_no']: m for m in marks_db}
                
                df_editor = st.data_editor(pd.DataFrame([
                    {"Exam No": s['exam_no'], "Name": s['student_name'], "EMIS": s['emis_no'],
                     "Abs": marks_dict.get(s['emis_no'], {}).get('is_absent', False),
                     "Theory": marks_dict.get(s['emis_no'], {}).get('theory_mark', 0),
                     "Internal": marks_dict.get(s['emis_no'], {}).get('internal_mark', 0),
                     "Practical": marks_dict.get(s['emis_no'], {}).get('practical_mark', 0)} for s in students
                ]), hide_index=True)
                
                if st.button("🚀 பாட மதிப்பெண் சேமி"):
                    data = [{"exam_id": exam_id, "emis_no": r['EMIS'], "subject_id": sub_code,
                             "theory_mark": 0 if r['Abs'] else r['Theory'], "internal_mark": 0 if r['Abs'] else r['Internal'],
                             "practical_mark": 0 if r['Abs'] else r['Practical'], "is_absent": r['Abs']} for _, r in df_editor.iterrows()]
                    supabase.table("marks").upsert(data, on_conflict="exam_id, emis_no, subject_id").execute()
                    st.success("சேமிக்கப்பட்டது!")

        # --- Bulk Function (Tab 2 & 3 க்கானது) ---
        def get_bulk_template(target_classes):
            all_dfs = []
            for c_name in target_classes:
                mapping = supabase.table("exam_mapping").select("emis_no, student_name").eq("exam_id", exam_id).eq("class_name", c_name).execute().data
                df = pd.DataFrame(mapping)
                cls_info = next((c for c in all_classes if c['class_name'] == c_name), None)
                g_info = next((g for g in all_groups if g['group_name'] == cls_info.get('group_name')), None)
                for s in [s.strip() for s in g_info['subjects'].split(',')]:
                    sub = next((x for x in all_subjects if x['subject_name'] == s), None)
                    if sub and sub.get('eval_type') != 'NIL':
                        eval_p = str(sub.get('eval_type', '100')).split('+')
                        df[f"Theory_{s}"] = 0
                        if len(eval_p) >= 2: df[f"Internal_{s}"] = 0
                        if len(eval_p) == 3: df[f"Practical_{s}"] = 0
                all_dfs.append(df)
            return pd.concat(all_dfs, ignore_index=True) if all_dfs else pd.DataFrame()

        with tab2:
            df_b = get_bulk_template([sel_class])
            output = BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer: df_b.to_excel(writer, index=False)
            st.download_button("📥 வகுப்பு கோப்பைத் தரவிறக்கு", data=output.getvalue(), file_name=f"Marks_{sel_class}.xlsx")
            
        with tab3:
            grade_val = st.text_input("வகுப்பு எண் (எ.கா: 12):")
            if grade_val:
                relevant = [c['class_name'] for c in all_classes if c['class_name'].startswith(grade_val)]
                df_a = get_bulk_template(relevant)
                output = BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer: df_a.to_excel(writer, index=False)
                st.download_button("📥 அனைத்து பிரிவு கோப்பைப் பெற", data=output.getvalue(), file_name=f"Marks_{grade_val}_All.xlsx")
