import streamlit as st
import pandas as pd
from supabase import create_client

# --- Supabase இணைப்பு ---
def get_supabase_client():
    if "supabase_instance" not in st.session_state:
        st.session_state.supabase_instance = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
    return st.session_state.supabase_instance

supabase = get_supabase_client()

st.set_page_config(page_title="Result Analysis", layout="wide")

st.markdown("""
    <style>
    .stDataFrame td { font-weight: bold !important; font-size: 16px !important; }
    .pass-box { padding: 20px; border-radius: 10px; background-color: #d1fae5; color: #065f46; text-align: center; font-size: 24px; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

st.title("📊 வகுப்பு வாரியான தேர்ச்சிப் பகுப்பாய்வு")

# --- 1. தரவுகள் ---
exams_data = supabase.table("exams").select("*").execute().data
classes_data = supabase.table("classes").select("*").execute().data
groups_data = supabase.table("groups").select("*").execute().data
subjects_data = supabase.table("subjects").select("*").execute().data

c1, c2 = st.columns(2)
sel_exam_name = c1.selectbox("1. தேர்வு:", [e['exam_name'] for e in exams_data])
class_list = sorted(list(set([c.get('class_n') or c.get('class_name') for c in classes_data])))
sel_class = c2.selectbox("2. வகுப்பு:", ["-- தேர்வு செய்க --"] + class_list)

if sel_exam_name and sel_class != "-- தேர்வு செய்க --":
    exam_id = next(e['id'] for e in exams_data if e['exam_name'] == sel_exam_name)
    
    # ⚡ அந்த குறிப்பிட்ட வகுப்பின் பாடப்பிரிவை கண்டறிதல்
    class_info = next((c for c in classes_data if (c.get('class_n') == sel_class or c.get('class_name') == sel_class)), None)
    relevant_subjects = []
    if class_info:
        group_info = next((g for g in groups_data if g['group_name'] == class_info.get('group_name')), None)
        if group_info and group_info.get('subjects'):
            g_subs = [s.strip() for s in group_info['subjects'].split(',')]
            relevant_subjects = [s for s in subjects_data if s['subject_name'] in g_subs]

    students = supabase.table("exam_mapping").select("exam_no, student_name, emis_no").eq("exam_id", exam_id).eq("class_name", sel_class).order("exam_no").execute().data
    marks_data = supabase.table("marks").select("*").eq("exam_id", exam_id).execute().data

    if students and relevant_subjects:
        show_detailed = st.toggle("🔍 விரிவான பார்வை (T, P, I பிரித்துக்காட்டு)")

        report_rows = []
        pass_count = 0

        for s in students:
            row = {"Rank": 0, "தேர்வு எண்": s['exam_no'], "மாணவர் பெயர்": s['student_name']}
            total_score = 0
            fail_in_subs = 0
            
            for sub in relevant_subjects:
                s_name, s_code = sub['subject_name'], sub['subject_code']
                m = next((m for m in marks_data if m['emis_no'] == s['emis_no'] and m['subject_id'] == s_code), None)
                
                if m:
                    tot = m.get('total_mark', 0)
                    if not m.get('is_absent'):
                        total_score += tot
                        if tot < 35: fail_in_subs += 1
                    else:
                        tot = "ABS"; fail_in_subs += 1
                    
                    if show_detailed:
                        row[f"{s_name} (Σ)"] = tot
                    else:
                        row[s_name] = tot
                else:
                    row[s_name] = "-"
            
            row["மொத்தம்"] = total_score
            row["Fails"] = fail_in_subs
            if fail_in_subs == 0: pass_count += 1
            report_rows.append(row)

        df = pd.DataFrame(report_rows)
        df = df.sort_values(by="மொத்தம்", ascending=False).reset_index(drop=True)
        df["Rank"] = range(1, 1 + len(df))

        # ⚡ தேர்ச்சி விழுக்காடு காட்டுதல்
        pass_percent = round((pass_count / len(students)) * 100, 1) if students else 0
        st.markdown(f'<div class="pass-box">🎓 {sel_class} தேர்ச்சி விழுக்காடு: {pass_percent}% ({pass_count}/{len(students)})</div>', unsafe_allow_html=True)

        st.divider()
        st.dataframe(df.style.map(lambda v: 'color: red' if v == "ABS" or (isinstance(v, int) and v < 35) else '').set_properties(**{'background-color': '#f8fafc'}, subset=['மொத்தம்']), use_container_width=True)

        # ⚡ பாடவாரி புள்ளிவிவரங்கள்
        st.subheader("📈 பாடவாரி தேர்ச்சி விவரம்")
        stats = []
        for sub in relevant_subjects:
            s_col = f"{sub['subject_name']} (Σ)" if show_detailed else sub['subject_name']
            if s_col in df.columns:
                v = pd.to_numeric(df[s_col], errors='coerce').dropna()
                stats.append({
                    "பாடம்": sub['subject_name'], "சராசரி": round(v.mean(), 1) if not v.empty else 0,
                    "அதிகபட்சம்": int(v.max()) if not v.empty else 0, "தோல்வி": len(v[v < 35])
                })
        st.table(pd.DataFrame(stats))
