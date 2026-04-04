import streamlit as st
import pandas as pd
from supabase import create_client

# --- Supabase இணைப்பு ---
def get_supabase_client():
    if "supabase_instance" not in st.session_state:
        st.session_state.supabase_instance = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
    return st.session_state.supabase_instance

supabase = get_supabase_client()

st.set_page_config(page_title="Advanced Class Report", layout="wide")

# ⚡ CSS - தடிமனான மற்றும் வண்ண எழுத்துக்கள்
st.markdown("""
    <style>
    .stDataFrame td { font-weight: bold !important; }
    .main-title { font-size: 24px; font-weight: bold; color: #1E3A8A; }
    </style>
    """, unsafe_allow_html=True)

st.title("📂 வகுப்பு வாரி மதிப்பெண் பகுப்பாய்வு & தரவரிசை")

# --- 1. தரவுகள் ---
exams = supabase.table("exams").select("*").execute().data
all_classes = supabase.table("classes").select("*").execute().data
all_groups = supabase.table("groups").select("*").execute().data
all_subjects = supabase.table("subjects").select("*").execute().data

c1, c2 = st.columns(2)
sel_exam_name = c1.selectbox("1. தேர்வு:", [e['exam_name'] for e in exams])
class_list = sorted(list(set([c.get('class_n') or c.get('class_name') for c in all_classes])))
sel_class = c2.selectbox("2. வகுப்பு:", ["-- தேர்வு செய்க --"] + class_list)

if sel_exam_name and sel_class != "-- தேர்வு செய்க --":
    exam_id = next(e['id'] for e in exams if e['exam_name'] == sel_exam_name)
    
    # பாடப்பிரிவு கண்டறிதல்
    class_info = next((c for c in all_classes if (c.get('class_n') == sel_class or c.get('class_name') == sel_class)), None)
    relevant_subjects = []
    if class_info:
        group_info = next((g for g in all_groups if g['group_name'] == class_info.get('group_name')), None)
        if group_info and group_info.get('subjects'):
            group_subs = [s.strip() for s in group_info['subjects'].split(',')]
            relevant_subjects = [s for s in all_subjects if s['subject_name'] in group_subs]

    students = supabase.table("exam_mapping").select("exam_no, student_name, emis_no").eq("exam_id", exam_id).eq("class_name", sel_class).order("exam_no").execute().data
    marks_data = supabase.table("marks").select("*").eq("exam_id", exam_id).execute().data

    if students and relevant_subjects:
        show_detailed = st.toggle("🔍 விரிவான பார்வை (T, P, I பிரித்துக்காட்டு)")

        report_rows = []
        # தடிமனாகக் காட்ட வேண்டிய நெடுவரிசைகளைச் சேமிக்க
        bold_cols = ['மொத்தம்']

        for s in students:
            row = {"தேர்வு எண்": s['exam_no'], "மாணவர் பெயர்": s['student_name']}
            total_score = 0
            fail_count = 0
            
            for sub in relevant_subjects:
                s_name = sub['subject_name']
                s_code = sub['subject_code']
                eval_type = sub.get('eval_type', '90+10')
                has_prac = len(eval_type.split('+')) > 2
                
                m = next((m for m in marks_data if m['emis_no'] == s['emis_no'] and m['subject_id'] == s_code), None)
                
                if m:
                    t, p, i, tot = m.get('theory_mark', 0), m.get('practical_mark', 0), m.get('internal_mark', 0), m.get('total_mark', 0)
                    if not m.get('is_absent'):
                        total_score += tot
                        if tot < 35: fail_count += 1
                    else:
                        t = p = i = tot = "ABS"
                        fail_count += 1
                    
                    if show_detailed:
                        row[f"{s_name} (T)"] = t
                        if has_prac: row[f"{s_name} (P)"] = p
                        row[f"{s_name} (I)"] = i
                        row[f"{s_name} (Σ)"] = tot
                        if f"{s_name} (Σ)" not in bold_cols: bold_cols.append(f"{s_name} (Σ)")
                    else:
                        row[s_name] = tot
                        if s_name not in bold_cols: bold_cols.append(s_name)
                else:
                    row[s_name] = "-"
            
            row["மொத்தம்"] = total_score
            row["தோல்வி பாடங்கள்"] = fail_count
            report_rows.append(row)

        df = pd.DataFrame(report_rows)
        # ⚡ தரவரிசை (Ranking)
        df = df.sort_values(by="மொத்தம்", ascending=False).reset_index(drop=True)
        df.insert(0, 'Rank', range(1, 1 + len(df)))

        # ⚡ நிறம் மற்றும் தடிமனான எழுத்துக்கள் (Styler)
        def style_logic(val):
            try:
                if val == "ABS" or (isinstance(val, (int, float)) and val < 35):
                    return 'color: red; font-weight: bold; font-size: 110%;'
            except: pass
            return ''

        st.divider()
        st.subheader(f"📊 {sel_class} - {sel_exam_name} பட்டியல்")
        
        # 'applymap' பிழையைத் தவிர்க்க 'map' பயன்படுத்தப்பட்டுள்ளது
        styled_df = df.style.map(style_logic).set_properties(**{'background-color': '#f0f2f6', 'font-size': '18px'}, subset=bold_cols)
        st.
