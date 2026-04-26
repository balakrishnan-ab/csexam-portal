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
    tab1, tab2, tab3 = st.tabs(["👨‍🏫 பாட ஆசிரியர்", "📂 வகுப்பு ஆசிரியர் (Bulk)", "🏢 வகுப்பின் அனைத்துப் பிரிவுகள்"])

    # --- TAB 1: பாட ஆசிரியர் (குறிப்பிட்ட பாடம் மட்டும்) ---
    with tab1:
        c1, c2 = st.columns(2)
        class_list = sorted(list(set([c['class_name'] for c in all_classes])))
        sel_class_t1 = c1.selectbox("வகுப்பு:", ["-- தேர்வு செய்க --"] + class_list, key="t1_class")
        
        if sel_class_t1 != "-- தேர்வு செய்க --":
            class_info = next((c for c in all_classes if c['class_name'] == sel_class_t1), None)
            g_info = next((g for g in all_groups if g['group_name'] == class_info.get('group_name')), None)
            sub_names = [s.strip() for s in g_info['subjects'].split(',')] if g_info else []
            sel_sub = c2.selectbox("பாடம்:", ["-- தேர்வு செய்க --"] + sub_names, key="t1_sub")
            
            if sel_sub != "-- தேர்வு செய்க --":
                sub_data = next((s for s in all_subjects if s['subject_name'] == sel_sub), None)
                sub_code = sub_data['subject_code']
                eval_p = str(sub_data.get('eval_type', '100')).split('+')
                
                students = supabase.table("exam_mapping").select("exam_no, student_name, emis_no").eq("exam_id", exam_id).eq("class_name", sel_class_t1).execute().data
                marks_db = supabase.table("marks").select("*").eq("exam_id", exam_id).eq("subject_id", sub_code).execute().data
                marks_dict = {m['emis_no']: m for m in marks_db}
                
                rows = [{"Exam No": s['exam_no'], "Name": s['student_name'], "EMIS": s['emis_no'],
                         "Abs": marks_dict.get(s['emis_no'], {}).get('is_absent', False),
                         "Theory": marks_dict.get(s['emis_no'], {}).get('theory_mark', 0),
                         "Internal": marks_dict.get(s['emis_no'], {}).get('internal_mark', 0),
                         "Practical": marks_dict.get(s['emis_no'], {}).get('practical_mark', 0)} for s in students]
                
                edited_df = st.data_editor(pd.DataFrame(rows), hide_index=True, use_container_width=True)
                if st.button("🚀 பாட மதிப்பெண் சேமி"):
                    data = [{"exam_id": exam_id, "emis_no": r['EMIS'], "subject_id": sub_code,
                             "theory_mark": 0 if r['Abs'] else r['Theory'], "internal_mark": 0 if r['Abs'] else r['Internal'],
                             "practical_mark": 0 if r['Abs'] else r['Practical'], "is_absent": r['Abs']} for _, r in edited_df.iterrows()]
                    supabase.table("marks").upsert(data, on_conflict="exam_id, emis_no, subject_id").execute()
                    st.success("சேமிக்கப்பட்டது!")

    # --- Bulk Template Generator (Tab 2 & 3 க்கானது) ---
    def generate_bulk_df(target_classes):
        all_dfs = []
        for c_name in target_classes:
            # மாணவர் பட்டியல்
            mapping = supabase.table("exam_mapping").select("emis_no, student_name").eq("exam_id", exam_id).eq("class_name", c_name).execute().data
            df = pd.DataFrame(mapping)
            
            # குரூப் மற்றும் பாடங்கள்
            cls_info = next((c for c in all_classes if c['class_name'] == c_name), None)
            g_info = next((g for g in all_groups if g['group_name'] == cls_info.get('group_name')), None)
            
            # பாட மதிப்பெண்களைத் தேடி எடுக்கும் பட்டியல்
            sub_names = [s.strip() for s in g_info['subjects'].split(',')]
            
            # அனைத்து பாடங்களின் மதிப்பெண்களையும் எடுக்க
            for s in sub_names:
                sub = next((x for x in all_subjects if x['subject_name'] == s), None)
                if sub and sub.get('eval_type') != 'NIL':
                    p = str(sub.get('eval_type', '100')).split('+')
                    sub_code = sub['subject_code']
                    
                    # இந்த தேர்வு மற்றும் பாடத்திற்கு உள்ள மதிப்பெண்களை எடுக்கவும்
                    marks_db = supabase.table("marks").select("emis_no, theory_mark, internal_mark, practical_mark").eq("exam_id", exam_id).eq("subject_id", sub_code).execute().data
                    marks_dict = {m['emis_no']: m for m in marks_db}
                    
                    # DataFrame-ல் மதிப்பெண்களை நிரப்புதல்
                    df[f"Theory_{s}"] = df['emis_no'].apply(lambda x: marks_dict.get(x, {}).get('theory_mark', 0))
                    
                    if len(p) >= 2:
                        df[f"Internal_{s}"] = df['emis_no'].apply(lambda x: marks_dict.get(x, {}).get('internal_mark', 0))
                    if len(p) == 3:
                        df[f"Practical_{s}"] = df['emis_no'].apply(lambda x: marks_dict.get(x, {}).get('practical_mark', 0))
            
            all_dfs.append(df)
        return all_dfs
    # --- TAB 2: வகுப்பு ஆசிரியர் (தனி வகுப்பு) ---
    with tab2:
        sel_class_t2 = st.selectbox("வகுப்பு:", ["-- தேர்வு செய்க --"] + class_list, key="t2_class")
        if sel_class_t2 != "-- தேர்வு செய்க --":
            df_b = generate_bulk_df([sel_class_t2])[0]
            output = BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer: df_b.to_excel(writer, index=False)
            st.download_button("📥 வகுப்பு கோப்பைத் தரவிறக்கு", data=output.getvalue(), file_name=f"Marks_{sel_class_t2}.xlsx")
            st.file_uploader("பதிவேற்றம்:", type=["xlsx"], key="up2")

    # --- TAB 3: அனைத்துப் பிரிவுகள் (Group-wise Sheets) ---
    with tab3:
        grade_val = st.text_input("வகுப்பு எண் (எ.கா: 12):")
        if grade_val:
            relevant = [c['class_name'] for c in all_classes if c['class_name'].startswith(grade_val)]
            output = BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                for c in relevant:
                    generate_bulk_df([c])[0].to_excel(writer, sheet_name=c, index=False)
            st.download_button("📥 அனைத்துப் பிரிவுகளையும் தரவிறக்கு", data=output.getvalue(), file_name=f"Marks_{grade_val}_All.xlsx")
            st.file_uploader("பதிவேற்றம்:", type=["xlsx"], key="up3")
