import streamlit as st
import pandas as pd
from supabase import create_client

# --- Supabase இணைப்பு ---
def get_supabase_client():
    if "supabase_instance" not in st.session_state:
        st.session_state.supabase_instance = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
    return st.session_state.supabase_instance

supabase = get_supabase_client()

st.set_page_config(page_title="Detailed Class Report", layout="wide")

# ⚡ அட்டவணைத் தலைப்புகளை அழகாக்க CSS
st.markdown("""
    <style>
    .stDataFrame { font-size: 14px !important; }
    thead tr th { background-color: #f0f2f6 !important; color: black !important; font-weight: bold !important; }
    </style>
    """, unsafe_allow_html=True)

st.title("📂 விரிவான வகுப்பு வாரி மதிப்பெண் அறிக்கை")

# --- 1. தரவுகள் ---
exams = supabase.table("exams").select("*").execute().data
all_classes = supabase.table("classes").select("*").execute().data
all_groups = supabase.table("groups").select("*").execute().data
all_subjects = supabase.table("subjects").select("*").execute().data

# --- 2. வடிகட்டிகள் ---
c1, c2 = st.columns(2)
sel_exam_name = c1.selectbox("1. தேர்வு:", [e['exam_name'] for e in exams])
class_list = sorted(list(set([c.get('class_n') or c.get('class_name') for c in all_classes])))
sel_class = c2.selectbox("2. வகுப்பு:", ["-- தேர்வு செய்க --"] + class_list)

if sel_exam_name and sel_class != "-- தேர்வு செய்க --":
    exam_id = next(e['id'] for e in exams if e['exam_name'] == sel_exam_name)
    
    # வகுப்பிற்குரிய பாடங்களை எடுத்தல்
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
        show_detailed = st.toggle("🔍 விரிவான பார்வை (Theory, Practical, Internal பிரித்துக்காட்டு)")

        final_rows = []
        for s in students:
            row = {"தேர்வு எண்": s['exam_no'], "மாணவர் பெயர்": s['student_name']}
            total_score = 0
            
            for sub in relevant_subjects:
                s_name = sub['subject_name']
                s_code = sub['subject_code']
                eval_type = sub.get('eval_type', '90+10')
                has_prac = len(eval_type.split('+')) > 2 # செய்முறை உள்ளதா எனச் சரிபார்த்தல்
                
                m = next((m for m in marks_data if m['emis_no'] == s['emis_no'] and m['subject_id'] == s_code), None)
                
                if m:
                    if m.get('is_absent'):
                        t, p, i, tot = "ABS", "ABS", "ABS", "ABS"
                    else:
                        t, p, i, tot = m.get('theory_mark', 0), m.get('practical_mark', 0), m.get('internal_mark', 0), m.get('total_mark', 0)
                        total_score += tot
                    
                    if show_detailed:
                        row[f"{s_name} (T)"] = t
                        if has_prac: row[f"{s_name} (P)"] = p
                        row[f"{s_name} (I)"] = i
                        row[f"{s_name} (Σ)"] = tot
                    else:
                        row[s_name] = tot
                else:
                    if show_detailed:
                        row[f"{s_name} (T)"], row[f"{s_name} (I)"], row[f"{s_name} (Σ)"] = "-", "-", "-"
                        if has_prac: row[f"{s_name} (P)"] = "-"
                    else:
                        row[s_name] = "-"
            
            row["மொத்தம்"] = total_score
            final_rows.append(row)

        df = pd.DataFrame(final_rows)
        df = df.sort_values(by="மொத்தம்", ascending=False).reset_index(drop=True)
        df.index += 1
        df.index.name = "Rank"

        st.divider()
        st.subheader(f"📊 {sel_class} - {sel_exam_name} விரிவான அறிக்கை")
        st.dataframe(df, use_container_width=True)

        # Excel டவுன்லோட்
        csv = df.to_csv(index=True).encode('utf-8-sig')
        st.download_button("📥 எக்செல் தரவிறக்கம்", data=csv, file_name=f"{sel_class}_Detailed_Report.csv", mime="text/csv")
