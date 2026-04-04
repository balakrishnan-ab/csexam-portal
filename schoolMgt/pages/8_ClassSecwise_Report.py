import streamlit as st
import pandas as pd
from supabase import create_client

# --- Supabase இணைப்பு ---
def get_supabase_client():
    if "supabase_instance" not in st.session_state:
        st.session_state.supabase_instance = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
    return st.session_state.supabase_instance

supabase = get_supabase_client()

st.set_page_config(page_title="School Analysis Report", layout="wide")

# ⚡ CSS வடிவமைப்பு
st.markdown("""
    <style>
    .stDataFrame td { font-weight: bold !important; font-size: 14px !important; white-space: pre !important; }
    .main-stat { background-color: #f8fafc; border: 1px solid #e2e8f0; padding: 10px; border-radius: 10px; text-align: center; margin-bottom: 10px; }
    .stat-val { font-size: 22px; font-weight: bold; color: #1e293b; line-height: 1.1; }
    .gender-sub { font-size: 13px; color: #3b82f6; font-weight: bold; display: block; margin-top: 2px; }
    .stat-label { font-size: 13px; color: #64748b; font-weight: bold; }
    .info-card { padding: 8px; border-radius: 5px; margin-bottom: 5px; border-left: 4px solid #10b981; background-color: #f0fdf4; font-size: 14px; }
    .abs-card { border-left-color: #ef4444; background-color: #fef2f2; }
    </style>
    """, unsafe_allow_html=True)

st.title("📊 வகுப்பு வாரி விரிவான தேர்ச்சிப் பகுப்பாய்வு")

# --- தரவுகள் பெறுதல் ---
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
    
    st.divider()
    split_gender = st.toggle("🔍 ஆண் பெண் பிரித்து (Female + Male = Total)")

    students = supabase.table("exam_mapping").select("exam_no, student_name, emis_no, gender").eq("exam_id", exam_id).eq("class_name", sel_class).order("exam_no").execute().data
    marks_data = supabase.table("marks").select("*").eq("exam_id", exam_id).execute().data
    
    class_info = next((c for c in classes_data if (c.get('class_n') == sel_class or c.get('class_name') == sel_class)), None)
    relevant_subjects = []
    if class_info:
        g_info = next((g for g in groups_data if g['group_name'] == class_info.get('group_name')), None)
        if g_info and g_info.get('subjects'):
            g_subs = [s.strip() for s in g_info['subjects'].split(',')]
            relevant_subjects = [s for s in subjects_data if s['subject_name'] in g_subs]

    if students and relevant_subjects:
        stats = {"total": {"all": 0, "M": 0, "F": 0}, "present": {"all": 0, "M": 0, "F": 0}, "pass": {"all": 0, "M": 0, "F": 0}}
        report_rows = []
        centum_list = []
        absent_list = []

        for s in students:
            raw_gen = str(s.get('gender', 'Male')).strip().upper()
            gen = 'F' if raw_gen.startswith('F') else 'M'
            stats["total"]["all"] += 1; stats["total"][gen] += 1
            
            row_raw = {"பெயர்": s['student_name'], "gender": gen, "exam_no": s['exam_no']}
            total_m, fails, wrote_any, fail_subs = 0, 0, False, []
            
            for sub in relevant_subjects:
                m = next((m for m in marks_data if m['emis_no'] == s['emis_no'] and m['subject_id'] == sub['subject_code']), None)
                if m and not m.get('is_absent'):
                    wrote_any = True
                    tot, th, pr, in_m = m.get('total_mark', 0), m.get('theory_mark', 0), m.get('practical_mark', 0), m.get('internal_mark', 0)
                    
                    # ✅ பெரியசாமி போன்ற மாணவர்களுக்கான தேர்ச்சி விதி (Theory >= 15)
                    is_p = (th >= 15 and pr >= 15 and tot >= 35) if sub.get('has_practical') else (tot >= 35)
                    
                    total_m += tot
                    if not is_p: fails += 1; fail_subs.append(sub['subject_name'])
                    if tot == 100: centum_list.append(f"{s['student_name']} ({sub['subject_name']})")
                    row_raw[sub['subject_name']] = {"tot": tot, "th": th, "pr": pr, "in": in_m, "prac": sub.get('has_practical'), "pass": is_p}
                else:
                    row_raw[sub['subject_name']] = "ABS"; fails += 1; fail_subs.append(sub['subject_name'])
            
            if wrote_any:
                stats["present"]["all"] += 1; stats["present"][gen] += 1
                if fails == 0: stats["pass"]["all"] += 1; stats["pass"][gen] += 1
            else:
                absent_list.append(s['student_name'])

            row_raw.update({"Present": wrote_any, "Fails": fails, "மொத்தம்": total_m, "தோல்வி விவரம்": f"({', '.join(fail_subs)})" if fail_subs else ""})
            report_rows.append(row_raw)

        # --- Dashboard (Gender in 2nd line) ---
        st.subheader(f"📌 {sel_class} ஒட்டுமொத்தப் புள்ளிவிவரம்")
        m = st.columns(5)
        titles = ["மொத்தம்", "எழுதியவர்", "தேர்ச்சி", "தோல்வி", "தேர்ச்சி %"]
        
        for i, key in enumerate(["total", "present", "pass"]):
            val_all = stats[key]['all']
            gender_line = f"<span class='gender-sub'>({stats[key]['F']}F + {stats[key]['M']}M)</span>" if split_gender else ""
            m[i].markdown(f'<div class="main-stat"><div class="stat-label">{titles[i]}</div><div class="stat-val">{val_all}{gender_line}
