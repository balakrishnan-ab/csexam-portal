import streamlit as st
import pandas as pd
from supabase import create_client
from io import BytesIO

# --- Supabase Connection ---
def get_supabase_client():
    if "supabase_instance" not in st.session_state:
        st.session_state.supabase_instance = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
    return st.session_state.supabase_instance

supabase = get_supabase_client()

st.set_page_config(page_title="Mark Entry System", layout="wide")
st.title("📊 மதிப்பெண் பதிவேற்றம் & திருத்தம்")

# தரவுகளைப் பெறுதல்
exams = supabase.table("exams").select("*").eq("exam_status", "Active").execute().data
all_classes = supabase.table("classes").select("*").execute().data
all_groups = supabase.table("groups").select("*").execute().data
all_subjects = supabase.table("subjects").select("*").execute().data

sel_exam_name = st.selectbox("தேர்வைத் தேர்ந்தெடுக்கவும்:", ["-- தேர்வு செய்க --"] + [e['exam_name'] for e in exams])

if sel_exam_name != "-- தேர்வு செய்க --":
    exam_id = next(e['id'] for e in exams if e['exam_name'] == sel_exam_name)
    
    # --- மதிப்பெண்களை எடுத்து நிரப்பும் மேம்படுத்தப்பட்ட பங்க்ஷன் ---
    def generate_bulk_df(c_name):
        # 1. மாணவர் பட்டியல்
        mapping = supabase.table("exam_mapping").select("emis_no, student_name").eq("exam_id", exam_id).eq("class_name", c_name).execute().data
        df = pd.DataFrame(mapping)
        
        # 2. பாடங்களைக் கண்டறிதல்
        cls_info = next((c for c in all_classes if c['class_name'] == c_name), None)
        g_info = next((g for g in all_groups if g['group_name'] == cls_info.get('group_name')), None)
        sub_list = [s.strip() for s in g_info['subjects'].split(',')]
        
        # 3. ஒவ்வொரு பாடத்திற்கும் மதிப்பெண்களை நிரப்புதல்
        for s in sub_list:
            sub = next((x for x in all_subjects if x['subject_name'] == s), None)
            if sub and sub.get('eval_type') != 'NIL':
                p = str(sub.get('eval_type', '100')).split('+')
                sub_code = sub['subject_code']
                
                # தரவுத்தளத்தில் ஏற்கனவே உள்ள மதிப்பெண்களை எடுத்தல்
                marks_db = supabase.table("marks").select("emis_no, theory_mark, internal_mark, practical_mark").eq("exam_id", exam_id).eq("subject_id", sub_code).execute().data
                marks_dict = {m['emis_no']: m for m in marks_db}
                
                # மதிப்பெண்களை DataFrame-ல் சேர்த்தல்
                df[f"Theory_{s}"] = df['emis_no'].apply(lambda x: marks_dict.get(x, {}).get('theory_mark', 0))
                if len(p) >= 2: df[f"Internal_{s}"] = df['emis_no'].apply(lambda x: marks_dict.get(x, {}).get('internal_mark', 0))
                if len(p) == 3: df[f"Practical_{s}"] = df['emis_no'].apply(lambda x: marks_dict.get(x, {}).get('practical_mark', 0))
        return df

    # --- TAB 3: அனைத்துப் பிரிவுகள் (Group-wise Sheets) ---
    _, _, tab3 = st.tabs(["👨‍🏫 பாட ஆசிரியர்", "📂 வகுப்பு ஆசிரியர்", "🏢 வகுப்பின் அனைத்துப் பிரிவுகள்"])
    
    with tab3:
        grade_val = st.text_input("வகுப்பு எண் (எ.கா: 12):")
        if grade_val:
            relevant = sorted([c['class_name'] for c in all_classes if c['class_name'].startswith(grade_val)])
            output = BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                for c in relevant:
                    # ஏற்கனவே உள்ள மதிப்பெண்களுடன் கூடிய DataFrame
                    df_c = generate_bulk_df(c)
                    df_c.to_excel(writer, sheet_name=c, index=False)
            
            st.download_button(
                label="📥 அனைத்துப் பிரிவுகளையும் மதிப்பெண்களுடன் தரவிறக்கு", 
                data=output.getvalue(), 
                file_name=f"Marks_{grade_val}_All.xlsx"
            )
            st.info("குறிப்பு: பதிவிறக்கம் செய்யப்படும் கோப்பில் ஏற்கனவே உள்ள மதிப்பெண்கள் இடம்பெறும். அதைத் திருத்திப் பதிவேற்றலாம்.")
