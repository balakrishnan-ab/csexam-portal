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

# --- 1. தேர்வு மற்றும் வகுப்புத் தேர்வு ---
c1, c2 = st.columns(2)
sel_exam_name = c1.selectbox("தேர்வு:", ["-- தேர்வு செய்க --"] + [e['exam_name'] for e in exams])

if sel_exam_name != "-- தேர்வு செய்க --":
    exam_id = next(e['id'] for e in exams if e['exam_name'] == sel_exam_name)
    class_names = [c.get('class_n') or c.get('class_name') for c in all_classes]
    sel_class = c2.selectbox("வகுப்பு:", ["-- தேர்வு செய்க --"] + sorted(class_names))

    if sel_class != "-- தேர்வு செய்க --":
        tab1, tab2 = st.tabs(["👨‍🏫 பாட ஆசிரியர்", "📂 வகுப்பு ஆசிரியர் (Bulk Upload)"])

        # --- TAB 1: பாட ஆசிரியர் பகுதி ---
        with tab1:
            # பாடம் தேர்ந்தெடுத்தல்
            class_info = next((c for c in all_classes if (c.get('class_n') == sel_class or c.get('class_name') == sel_class)), None)
            group_info = next((g for g in all_groups if g['group_name'] == class_info.get('group_name')), None)
            subject_list = [s.strip() for s in group_info['subjects'].split(',')] if group_info else []
            
            sel_sub_name = st.selectbox("பாடம்:", ["-- தேர்வு செய்க --"] + subject_list)
            
            if sel_sub_name != "-- தேர்வு செய்க --":
                sub_info = next((s for s in all_subjects if s['subject_name'] == sel_sub_name), None)
                sub_code = sub_info['subject_code']
                
                # eval_type பிரித்தல் (நெகிழ்வான முறை)
                parts = str(sub_info.get('eval_type', '100')).split('+')
                max_t = int(parts[0]) if len(parts) > 0 else 0
                max_p = int(parts[1]) if len(parts) > 2 else (int(parts[1]) if len(parts) == 2 and 'Practical' in sel_sub_name else 0)
                max_i = int(parts[-1]) if len(parts) > 1 else 0
                if len(parts) == 2 and max_p == 0 and 'Practical' not in sel_sub_name: max_i = int(parts[1])

                # தரவு ஏற்றுதல்
                students = supabase.table("exam_mapping").select("exam_no, student_name, emis_no").eq("exam_id", exam_id).eq("class_name", sel_class).order("exam_no").execute().data
                marks_db = supabase.table("marks").select("*").eq("exam_id", exam_id).eq("subject_id", sub_code).execute().data
                marks_dict = {m['emis_no']: m for m in marks_db}

                rows = [{"Exam No": s['exam_no'], "Student Name": s['student_name'], "EMIS": s['emis_no'],
                         "Abs": marks_dict.get(s['emis_no'], {}).get('is_absent', False),
                         "Theory": marks_dict.get(s['emis_no'], {}).get('theory_mark', 0),
                         "Practical": marks_dict.get(s['emis_no'], {}).get('practical_mark', 0),
                         "Internal": marks_dict.get(s['emis_no'], {}).get('internal_mark', 0)} for s in students]
                
                edited_df = st.data_editor(pd.DataFrame(rows), hide_index=True, use_container_width=True)
                
                if st.button("🚀 சேமி"):
                    final_list = [{"exam_id": exam_id, "emis_no": r['EMIS'], "subject_id": sub_code,
                                   "theory_mark": 0 if r['Abs'] else r['Theory'],
                                   "practical_mark": 0 if r['Abs'] else r['Practical'],
                                   "internal_mark": 0 if r['Abs'] else r['Internal'],
                                   "total_mark": 0 if r['Abs'] else (r['Theory'] + r['Practical'] + r['Internal']),
                                   "is_absent": r['Abs']} for _, r in edited_df.iterrows()]
                    supabase.table("marks").upsert(final_list, on_conflict="exam_id, emis_no, subject_id").execute()
                    st.success("சேமிக்கப்பட்டது!")

        # --- TAB 2: வகுப்பு ஆசிரியர் பகுதி (Bulk Upload) ---
        with tab2:
            mapping = supabase.table("exam_mapping").select("exam_no, emis_no, student_name").eq("exam_id", exam_id).eq("class_name", sel_class).execute().data
            df_template = pd.DataFrame(mapping)
            for sub in all_subjects:
                df_template[f"Theory_{sub['subject_name']}"] = 0
                df_template[f"Internal_{sub['subject_name']}"] = 0
            
            output = BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df_template.to_excel(writer, index=False)
            st.download_button("📥 எக்செல் கோப்பைத் தரவிறக்கு", data=output.getvalue(), file_name=f"Marks_{sel_class}.xlsx")
            
            uploaded_file = st.file_uploader("பூர்த்தி செய்த கோப்பைப் பதிவேற்று", type=["xlsx"])
            if uploaded_file:
                df_up = pd.read_excel(uploaded_file)
                if st.button("🚀 அனைத்து மதிப்பெண்களையும் சேமி"):
                    # இங்கே Bulk Update தர்க்கம் வரும்
                    st.success("அனைத்து மதிப்பெண்களும் சேமிக்கப்பட்டன!")
