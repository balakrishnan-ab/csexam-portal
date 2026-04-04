import streamlit as st
import pandas as pd
from supabase import create_client

# --- Supabase இணைப்பு ---
def get_supabase_client():
    if "supabase_instance" not in st.session_state:
        st.session_state.supabase_instance = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
    return st.session_state.supabase_instance

supabase = get_supabase_client()

st.set_page_config(page_title="Gender-wise Analysis", layout="wide")

# ⚡ CSS வடிவமைப்பு
st.markdown("""
    <style>
    .stDataFrame td { font-weight: bold !important; font-size: 14px !important; white-space: pre !important; }
    .main-stat { background-color: #f8fafc; border: 1px solid #e2e8f0; padding: 12px; border-radius: 10px; text-align: center; margin-bottom: 10px; }
    .stat-val { font-size: 20px; font-weight: bold; color: #1e293b; }
    .stat-label { font-size: 12px; color: #64748b; font-weight: bold; }
    .gender-label { font-size: 11px; color: #3b82f6; }
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
    
    # 🔍 ஆண் பெண் பிரித்து காட்டும் சுவிட்ச் (மேலேயே வைக்கப்பட்டுள்ளது)
    st.divider()
    split_gender = st.toggle("🔍 ஆண் பெண் பிரித்து (Female+Male = Total)")

    # மாணவர்கள் மற்றும் பாலினத் தகவலைப் பெறுதல்
    # குறிப்பு: மாணவர் அட்டவணையில் gender புலம் இருப்பதாகக் கொள்கிறேன்
    students = supabase.table("exam_mapping").select("exam_no, student_name, emis_no, gender").eq("exam_id", exam_id).eq("class_name", sel_class).order("exam_no").execute().data
    marks_data = supabase.table("marks").select("*").eq("exam_id", exam_id).execute().data
    
    # பாடப்பிரிவு தகவல்
    class_info = next((c for c in classes_data if (c.get('class_n') == sel_class or c.get('class_name') == sel_class)), None)
    relevant_subjects = []
    if class_info:
        g_info = next((g for g in groups_data if g['group_name'] == class_info.get('group_name')), None)
        if g_info and g_info.get('subjects'):
            g_subs = [s.strip() for s in g_info['subjects'].split(',')]
            relevant_subjects = [s for s in subjects_data if s['subject_name'] in g_subs]

    if students and relevant_subjects:
        report_rows = []
        # புள்ளிவிவரக் கணக்கீடு
        stats = {"total": {"all": 0, "M": 0, "F": 0}, "present": {"all": 0, "M": 0, "F": 0}, "pass": {"all": 0, "M": 0, "F": 0}}

        for s in students:
            gen = s.get('gender', 'M') # Default 'M'
            stats["total"]["all"] += 1
            stats["total"][gen] += 1
            
            row_raw = {"பெயர்": s['student_name'], "gender": gen, "emis_no": s['emis_no']}
            total_m = 0; fails = 0; wrote_any = False
            
            for sub in relevant_subjects:
                m = next((m for m in marks_data if m['emis_no'] == s['emis_no'] and m['subject_id'] == sub['subject_code']), None)
                if m and not m.get('is_absent'):
                    wrote_any = True
                    tot, th, pr = m.get('total_mark', 0), m.get('theory_mark', 0), m.get('practical_mark', 0)
                    is_p = (th >= 15 and pr >= 15 and tot >= 35) if sub.get('has_practical') else (tot >= 35)
                    total_m += tot
                    if not is_p: fails += 1
                    row_raw[sub['subject_name']] = {"tot": tot, "th": th, "pr": pr, "in": m.get('internal_mark', 0), "prac": sub.get('has_practical'), "pass": is_p}
                else:
                    row_raw[sub['subject_name']] = "ABS"
                    fails += 1
            
            if wrote_any:
                stats["present"]["all"] += 1
                stats["present"][gen] += 1
                if fails == 0:
                    stats["pass"]["all"] += 1
                    stats["pass"][gen] += 1

            row_raw["Present"] = wrote_any
            row_raw["Fails"] = fails
            row_raw["மொத்தம்"] = total_m
            report_rows.append(row_raw)

        # --- 📊 1. ஒட்டுமொத்தப் புள்ளிவிவரம் ---
        st.subheader(f"📌 {sel_class} ஒட்டுமொத்தப் புள்ளிவிவரம்")
        m1, m2, m3, m4, m5 = st.columns(5)
        
        def get_val(key):
            if split_gender:
                return f"{stats[key]['all']} <br><span class='gender-label'>({stats[key]['F']}F + {stats[key]['M']}M)</span>"
            return f"{stats[key]['all']}"

        m1.markdown(f'<div class="main-stat"><div class="stat-label">மொத்தம்</div><div class="stat-val">{get_val("total")}</div></div>', unsafe_allow_html=True)
        m2.markdown(f'<div class="main-stat"><div class="stat-label">எழுதியவர்</div><div class="stat-val">{get_val("present")}</div></div>', unsafe_allow_html=True)
        m3.markdown(f'<div class="main-stat"><div class="stat-label">தேர்ச்சி</div><div class="stat-val">{get_val("pass")}</div></div>', unsafe_allow_html=True)
        
        fail_all = stats["present"]["all"] - stats["pass"]["all"]
        fail_f = stats["present"]["F"] - stats["pass"]["F"]
        fail_m = stats["present"]["M"] - stats["pass"]["M"]
        f_val = f"{fail_all} <br><span class='gender-label'>({fail_f}F + {fail_m}M)</span>" if split_gender else f"{fail_all}"
        m4.markdown(f'<div class="main-stat"><div class="stat-label">தோல்வி</div><div class="stat-val">{f_val}</div></div>', unsafe_allow_html=True)
        
        p_per = round((stats["pass"]["all"]/stats["present"]["all"])*100, 1) if stats["present"]["all"] > 0 else 0
        m5.markdown(f'<div class="main-stat"><div class="stat-label">தேர்ச்சி %</div><div class="stat-val" style="color:#16a34a">{p_per}%</div></div>', unsafe_allow_html=True)

        # --- 📈 2. பாடவாரி பகுப்பாய்வு ---
        st.divider()
        st.subheader("📈 பாடவாரி விரிவான பகுப்பாய்வு")
        subj_stats = []
        for sub in relevant_subjects:
            s_name = sub['subject_name']
            total_app = 0; total_pas = 0
            f_app = 0; f_pas = 0; m_app = 0; m_pas = 0
            all_marks = []

            for r in report_rows:
                val = r.get(s_name)
                if isinstance(val, dict):
                    all_marks.append(val['tot'])
                    total_app += 1
                    if val['pass']: total_pas += 1
                    if r['gender'] == 'F':
                        f_app += 1
                        if val['pass']: f_pas += 1
                    else:
                        m_app += 1
                        if val['pass']: m_pas += 1
            
            if total_app > 0:
                row_stat = {"பாடம்": s_name}
                if split_gender:
                    row_stat["எழுதியவர்"] = f"{total_app} ({f_app}F+{m_app}M)"
                    row_stat["தேர்ச்சி"] = f"{total_pas} ({f_pas}F+{m_pas}M)"
                else:
                    row_stat["எழுதியவர்"] = total_app
                    row_stat["தேர்ச்சி"] = total_pas
                
                row_stat["சராசரி"] = round(sum(all_marks)/len(all_marks), 1)
                row_stat["அதிகபட்சம்"] = max(all_marks)
                subj_stats.append(row_stat)
        
        st.table(pd.DataFrame(subj_stats))

        # --- 📋 3. மதிப்பெண் பட்டியல் ---
        st.divider()
        st.subheader("📋 முழுமையான மதிப்பெண் பட்டியல்")
        show_breakup = st.toggle("🔍 அகமதிப்பீடு மற்றும் செய்முறை மதிப்பெண்களைக் காட்டு (T+I+P)")
        
        # (முந்தைய Rank மற்றும் Highlight லாஜிக் அப்படியே தொடரும்...)
        # ... [இங்கு ஏற்கனவே உள்ள DataFrame மற்றும் Styling லாஜிக் வரும்] ...
