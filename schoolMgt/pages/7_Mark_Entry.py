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
            st.info("குறிப்பிட்ட பாடத்தை மட்டும் பதிவு செய்யவும்.")
            # பாடப்பிரிவுகளைக் கண்டறிதல்
            class_info = next((c for c in all_classes if (c.get('class_n') == sel_class or c.get('class_name') == sel_class)), None)
            group_name = class_info.get('group_name') if class_info else None
            group_info = next((g for g in all_groups if g['group_name'] == group_name), None)
            sub_names = [s.strip() for s in group_info['subjects'].split(',')] if group_info else []
            
            sel_sub_name = st.selectbox("பாடம்:", ["-- தேர்வு செய்க --"] + sub_names)
            
            if sel_sub_name != "-- தேர்வு செய்க --":
                sub_info = next((s for s in all_subjects if s['subject_name'] == sel_sub_name), None)
                sub_code = sub_info['subject_code']
                eval_parts = str(sub_info.get('eval_type', '100')).split('+')
                max_t = int(eval_parts[0])
                max_i = int(eval_parts[1]) if len(eval_parts) > 1 else 0
                max_p = int(eval_parts[2]) if len(eval_parts) > 2 else 0

                # தரவு ஏற்றுதல்
                students = supabase.table("exam_mapping").select("exam_no, student_name, emis_no").eq("exam_id", exam_id).eq("class_name", sel_class).execute().data
                marks_db = supabase.table("marks").select("*").eq("exam_id", exam_id).eq("subject_id", sub_code).execute().data
                marks_dict = {m['emis_no']: m for m in marks_db}
                
                rows = []
                for s in students:
                    m = marks_dict.get(s['emis_no'], {})
                    rows.append({
                        "Exam No": s['exam_no'], "Student Name": s['student_name'], "EMIS": s['emis_no'],
                        "Abs": m.get('is_absent', False),
                        "Theory": m.get('theory_mark', 0),
                        "Internal": m.get('internal_mark', 0),
                        "Practical": m.get('practical_mark', 0)
                    })
                
                df_editor = st.data_editor(pd.DataFrame(rows), hide_index=True, use_container_width=True)
                
                if st.button("🚀 சேமி"):
                    final_data = []
                    for _, r in df_editor.iterrows():
                        final_data.append({
                            "exam_id": exam_id, "emis_no": r['EMIS'], "subject_id": sub_code,
                            "theory_mark": 0 if r['Abs'] else r['Theory'],
                            "internal_mark": 0 if r['Abs'] else r['Internal'],
                            "practical_mark": 0 if r['Abs'] else r['Practical'],
                            "total_mark": 0 if r['Abs'] else (r['Theory'] + r['Internal'] + r['Practical']),
                            "is_absent": r['Abs']
                        })
                    supabase.table("marks").upsert(final_data, on_conflict="exam_id, emis_no, subject_id").execute()
                    st.success("வெற்றிகரமாகச் சேமிக்கப்பட்டது!")
                    st.rerun()

        # --- TAB 2 & 3: வகுப்பு ஆசிரியர் மற்றும் குரூப் பதிவேற்றம் ---
        with tab2:
            st.subheader("📂 வகுப்பு ஆசிரியர் - ஒட்டுமொத்த பதிவேற்றம்")
            class_info = next((c for c in all_classes if (c.get('class_n') == sel_class or c.get('class_name') == sel_class)), None)
            group_name = class_info.get('group_name') if class_info else None
            group_info = next((g for g in all_groups if g['group_name'] == group_name), None)
            
            if group_info:
                sub_names = [s.strip() for s in group_info['subjects'].split(',')]
                mapping = supabase.table("exam_mapping").select("emis_no, student_name").eq("exam_id", exam_id).eq("class_name", sel_class).execute().data
                df_temp = pd.DataFrame(mapping)
                
                # eval_type-ஐப் பிரித்து காலம்களை உருவாக்குதல்
                for s_name in sub_names:
                    sub_data = next((s for s in all_subjects if s['subject_name'] == s_name), None)
                    if sub_data and sub_data.get('eval_type') != 'NIL':
                        eval_type = str(sub_data.get('eval_type', '100'))
                        parts = eval_type.split('+')
                        # Theory, Practical, Internal தலைப்புகளை உருவாக்குதல்
                        df_temp[f"Theory_{s_name}"] = 0
                        if len(parts) >= 2: df_temp[f"Internal_{s_name}"] = 0 # அல்லது Practical
                        if len(parts) == 3: df_temp[f"Practical_{s_name}"] = 0

                output = BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    df_temp.to_excel(writer, index=False)
                
                st.download_button("📥 கோப்பைத் தரவிறக்கு", data=output.getvalue(), file_name=f"Marks_{sel_class}.xlsx")
                st.file_uploader("பதிவேற்றம்:", type=["xlsx"])
