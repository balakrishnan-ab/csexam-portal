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
# --- TAB 1: பாட ஆசிரியர் ---
with tab1:
    st.info("குறிப்பிட்ட பாடத்தை மட்டும் பதிவு செய்யவும்.")
    
    # முதலில் பாடங்களை எடுக்க வேண்டும்
    class_info = next((c for c in all_classes if c['class_name'] == sel_class), None)
    group_name = class_info.get('group_name') if class_info else None
    group_info = next((g for g in all_groups if g['group_name'] == group_name), None)
    sub_names = [s.strip() for s in group_info['subjects'].split(',')] if group_info else []
    
    # sel_sub-ஐ இங்கேதான் நாம் வரையறுக்கிறோம்
    sel_sub = st.selectbox("பாடம்:", ["-- தேர்வு செய்க --"] + sub_names)
    
    # இப்போது இதைப் பயன்படுத்தினால் பிழை வராது
    if sel_sub != "-- தேர்வு செய்க --":
        # உங்கள் பாட ஆசிரியர் தர்க்கம் இங்கே தொடரும்...
        sub_info = next((s for s in all_subjects if s['subject_name'] == sel_sub), None)
                sub_code = sub_data['subject_code']
                
                # eval_type-ஐப் பிரித்தல்
                eval_parts = str(sub_data.get('eval_type', '100')).split('+')
                max_t = int(eval_parts[0])
                has_internal = len(eval_parts) >= 2
                has_practical = len(eval_parts) == 3
                max_i = int(eval_parts[1]) if has_internal else 0
                max_p = int(eval_parts[2]) if has_practical else (int(eval_parts[1]) if len(eval_parts)==2 and 'Practical' in sel_sub else 0)

                # --- Auto-fill பட்டன்கள் ---
                col1, col2, col3 = st.columns(3)
                if has_internal:
                    if col1.button(f"அனைவருக்கும் Internal ({max_i}) வழங்குக"):
                        st.session_state['fill_int'] = max_i
                if has_practical:
                    if col2.button(f"அனைவருக்கும் Practical ({max_p}) வழங்குக"):
                        st.session_state['fill_prac'] = max_p

                # தரவு ஏற்றுதல் மற்றும் எடிட்டர்
                students = supabase.table("exam_mapping").select("exam_no, student_name, emis_no").eq("exam_id", exam_id).eq("class_name", sel_class).execute().data
                # ... (marks_dict பெறுதல்) ...
                
                rows = []
                for s in students:
                    m = marks_dict.get(s['emis_no'], {})
                    rows.append({
                        "Exam No": s['exam_no'], "Name": s['student_name'], "EMIS": s['emis_no'],
                        "Abs": m.get('is_absent', False),
                        "Theory": m.get('theory_mark', 0),
                        "Internal": st.session_state.get('fill_int', m.get('internal_mark', 0)) if has_internal else 0,
                        "Practical": st.session_state.get('fill_prac', m.get('practical_mark', 0)) if has_practical else 0
                    })
                
                df_editor = st.data_editor(pd.DataFrame(rows), hide_index=True, use_container_width=True)
                
                if st.button("🚀 பாட மதிப்பெண் சேமி"):
                    # சேமிக்கும் தர்க்கம்...
                    # சேமித்த பின் session_state-ஐ சுத்தம் செய்யவும்
                    if 'fill_int' in st.session_state: del st.session_state['fill_int']
                    if 'fill_prac' in st.session_state: del st.session_state['fill_prac']
                    st.rerun()

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
            st.subheader("🏢 வகுப்பின் அனைத்துப் பிரிவுகள்")
            grade_val = st.text_input("வகுப்பு எண் (எ.கா: 12):")
            if grade_val:
                relevant = [c['class_name'] for c in all_classes if c['class_name'].startswith(grade_val)]
                
                output = BytesIO()
                # ExcelWriter-ஐப் பயன்படுத்தி ஒவ்வொரு வகுப்பிற்கும் ஒரு Sheet உருவாக்குதல்
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    for c_name in relevant:
                        # அந்த வகுப்பிற்குரிய தரவை மட்டும் எடுத்தல்
                        df_c = get_bulk_template([c_name]) 
                        # வகுப்பு பெயரை Sheet பெயராக வைத்தல்
                        df_c.to_excel(writer, sheet_name=c_name, index=False)
                
                st.download_button(
                    "📥 அனைத்து வகுப்புகளும் கொண்ட கோப்பைப் பெற (Separate Sheets)", 
                    data=output.getvalue(), 
                    file_name=f"Marks_{grade_val}_All_Sections.xlsx"
                )
