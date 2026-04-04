import streamlit as st
import pandas as pd
from supabase import create_client

# --- Supabase இணைப்பு ---
def get_supabase_client():
    if "supabase_instance" not in st.session_state:
        st.session_state.supabase_instance = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
    return st.session_state.supabase_instance

supabase = get_supabase_client()

st.set_page_config(page_title="Detailed Result Analysis", layout="wide")

# ⚡ CSS வடிவமைப்பு
st.markdown("""
    <style>
    .report-title { color: #1e40af; font-weight: bold; text-align: center; margin-bottom: 20px; }
    .stat-box { background-color: #f8fafc; border: 1px solid #e2e8f0; padding: 15px; border-radius: 10px; text-align: center; }
    .pass-text { color: #15803d; font-weight: bold; font-size: 20px; }
    .fail-text { color: #b91c1c; font-weight: bold; font-size: 20px; }
    </style>
    """, unsafe_allow_html=True)

st.title("📊 பள்ளித் தேர்ச்சிப் பகுப்பாய்வு அறிக்கை (Abstract)")

# --- 1. தேர்வுகள் மற்றும் வகுப்புகள் ---
exams_data = supabase.table("exams").select("*").execute().data
classes_data = supabase.table("classes").select("*").execute().data
groups_data = supabase.table("groups").select("*").execute().data
subjects_data = supabase.table("subjects").select("*").execute().data

c1, c2 = st.columns(2)
sel_exam_name = c1.selectbox("1. தேர்வு:", [e['exam_name'] for e in exams_data])

all_classes_raw = [c.get('class_n') or c.get('class_name') for c in classes_data]
base_classes = sorted(list(set([str(c).split('-')[0].strip() for c in all_classes_raw if c])), key=lambda x: int(x) if x.isdigit() else x)
sel_base_class = c2.selectbox("2. வகுப்பு (அனைத்துப் பிரிவுகளும்):", ["-- தேர்வு செய்க --"] + base_classes)

if sel_exam_name and sel_base_class != "-- தேர்வு செய்க --":
    exam_id = next(e['id'] for e in exams_data if e['exam_name'] == sel_exam_name)
    matching_sections = [c for c in all_classes_raw if str(c).startswith(sel_base_class)]
    
    all_students = []
    union_subs = []

    for section in matching_sections:
        class_info = next((c for c in classes_data if (c.get('class_n') == section or c.get('class_name') == section)), None)
        if class_info:
            g_name = class_info.get('group_name')
            group_info = next((g for g in groups_data if g['group_name'] == g_name), None)
            if group_info and group_info.get('subjects'):
                g_subs = [s.strip() for s in group_info['subjects'].split(',')]
                for gs in g_subs:
                    if gs not in union_subs: union_subs.append(gs)
                
                studs = supabase.table("exam_mapping").select("student_name, emis_no").eq("exam_id", exam_id).eq("class_name", section).execute().data
                if studs:
                    for s in studs:
                        s['section'] = section
                        all_students.append(s)

    marks_data = supabase.table("marks").select("*").eq("exam_id", exam_id).execute().data
    relevant_subjects = [s for s in subjects_data if s['subject_name'] in union_subs]

    if all_students:
        # --- 2. ஒட்டுமொத்த புள்ளிவிவரம் (Overall Abstract) ---
        total_strength = len(all_students)
        student_results = []
        pass_count = 0
        absent_count = 0

        for s in all_students:
            is_fail = False
            is_fully_absent = True
            
            for sub in relevant_subjects:
                m = next((m for m in marks_data if m['emis_no'] == s['emis_no'] and m['subject_id'] == sub['subject_code']), None)
                if m:
                    if m.get('is_absent'): is_fail = True
                    elif m.get('total_mark', 0) < 35: is_fail = True
                    if not m.get('is_absent'): is_fully_absent = False
            
            if is_fully_absent: absent_count += 1
            if not is_fail and not is_fully_absent: pass_count += 1
            student_results.append(not is_fail)

        appeared = total_strength - absent_count
        failed_count = appeared - pass_count
        pass_percentage = round((pass_count / appeared * 100), 2) if appeared > 0 else 0

        st.subheader(f"📑 {sel_base_class} - ஒட்டுமொத்தத் தேர்ச்சி அறிக்கை")
        col1, col2, col3, col4, col5 = st.columns(5)
        col1.metric("மொத்த மாணவர்கள்", total_strength)
        col2.metric("தேர்வு எழுதியோர்", appeared)
        col3.metric("தேர்ச்சி", pass_count)
        col4.metric("தோல்வி", failed_count)
        col5.metric("தேர்ச்சி %", f"{pass_percentage}%")

        # --- 3. பாடவாரி புள்ளிவிவரம் (Subject-wise Abstract) ---
        st.divider()
        st.subheader("📖 பாடவாரி தேர்ச்சி விவரம்")
        subject_stats = []

        for sub in relevant_subjects:
            s_name = sub['subject_name']
            s_code = sub['subject_code']
            
            sub_marks = [m for m in marks_data if m['subject_id'] == s_code and m['emis_no'] in [st['emis_no'] for st in all_students]]
            
            s_appeared = len([m for m in sub_marks if not m.get('is_absent')])
            s_pass = len([m for m in sub_marks if not m.get('is_absent') and m.get('total_mark', 0) >= 35])
            s_fail = s_appeared - s_pass
            s_perc = round((s_pass / s_appeared * 100), 2) if s_appeared > 0 else 0
            
            subject_stats.append({
                "பாடம்": s_name,
                "எழுதியவர்கள்": s_appeared,
                "தேர்ச்சி": s_pass,
                "தோல்வி": s_fail,
                "தேர்ச்சி %": f"{s_perc}%"
            })
        
        st.table(pd.DataFrame(subject_stats))

        # --- 4. மாணவர் வாரியான விரிவான பட்டியல் ---
        st.divider()
        st.subheader("📋 மாணவர் வாரியான விரிவான பட்டியல்")
        # (முந்தைய Rank & Total Logic இங்கே தொடரும்...)
        report_data = []
        for s in all_students:
            row = {"பிரிவு": s['section'], "பெயர்": s['student_name']}
            t_score = 0
            f_count = 0
            for sub in relevant_subjects:
                m = next((m for m in marks_data if m['emis_no'] == s['emis_no'] and m['subject_id'] == sub['subject_code']), None)
                val = m.get('total_mark', 0) if m and not m.get('is_absent') else ("ABS" if m and m.get('is_absent') else "-")
                row[sub['subject_name']] = val
                if isinstance(val, int): 
                    t_score += val
                    if val < 35: f_count += 1
                elif val == "ABS": f_count += 1
            row["மொத்தம்"] = t_score
            row["தோல்வி"] = f_count
            report_data.append(row)

        df = pd.DataFrame(report_data).sort_values(by=["தோல்வி", "மொத்தம்"], ascending=[True, False])
        
        # Rank கணக்கீடு (தேர்ச்சி பெற்றவர்களுக்கு மட்டும்)
        ranks = []
        r = 1
        for f in df["தோல்வி"]:
            if f == 0: ranks.append(str(r)); r += 1
            else: ranks.append("-")
        df.insert(0, "Rank", ranks)
        
        st.dataframe(df, use_container_width=True)
