import streamlit as st
import pandas as pd
from supabase import create_client

# --- Supabase இணைப்பு ---
def get_supabase_client():
    if "supabase_instance" not in st.session_state:
        st.session_state.supabase_instance = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
    return st.session_state.supabase_instance

supabase = get_supabase_client()

st.set_page_config(page_title="Section-wise Analysis", layout="wide")

# ⚡ CSS வடிவமைப்பு
st.markdown("""
    <style>
    .stDataFrame td { font-weight: bold !important; font-size: 14px !important; white-space: pre !important; }
    .main-stat { background-color: #f8fafc; border: 1px solid #e2e8f0; padding: 15px; border-radius: 10px; text-align: center; }
    .stat-val { font-size: 22px; font-weight: bold; color: #1e293b; }
    .stat-label { font-size: 13px; color: #64748b; font-weight: bold; }
    .info-card { background-color: #f1f5f9; padding: 8px; border-radius: 5px; margin-bottom: 5px; border-left: 4px solid #3b82f6; font-size: 13px; }
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
    class_info = next((c for c in classes_data if (c.get('class_n') == sel_class or c.get('class_name') == sel_class)), None)
    
    relevant_subjects = []
    if class_info:
        g_info = next((g for g in groups_data if g['group_name'] == class_info.get('group_name')), None)
        if g_info and g_info.get('subjects'):
            g_subs = [s.strip() for s in g_info['subjects'].split(',')]
            relevant_subjects = [s for s in subjects_data if s['subject_name'] in g_subs]

    students = supabase.table("exam_mapping").select("exam_no, student_name, emis_no").eq("exam_id", exam_id).eq("class_name", sel_class).order("exam_no").execute().data
    marks_data = supabase.table("marks").select("*").eq("exam_id", exam_id).execute().data

    if students and relevant_subjects:
        # ⚡ 1. Dashboard (முதலில் தோன்றும்)
        st.subheader(f"📌 {sel_class} ஒட்டுமொத்தப் புள்ளிவிவரம்")
        
        report_rows = []
        centum_winners = []
        full_absents = []
        present_count = 0
        pass_count = 0

        # டேட்டாவை முதலில் தயார் செய்தல் (Dashboard-க்காக)
        for s in students:
            row_data = {"பெயர்": s['student_name'], "emis_no": s['emis_no']}
            total = 0; fails = 0; fail_subs = []
            wrote_any = False
            
            for sub in relevant_subjects:
                m = next((m for m in marks_data if m['emis_no'] == s['emis_no'] and m['subject_id'] == sub['subject_code']), None)
                if m:
                    if not m.get('is_absent'):
                        wrote_any = True
                        tot = m.get('total_mark', 0)
                        total += tot
                        if tot < 35: fails += 1; fail_subs.append(sub['subject_name'])
                        if tot == 100: centum_winners.append(f"{s['student_name']} - {sub['subject_name']}")
                    else:
                        fails += 1; fail_subs.append(sub['subject_name'])
                
            if wrote_any:
                present_count += 1
                if fails == 0: pass_count += 1
            else:
                full_absents.append(s['student_name'])
            
            row_data["Present"] = wrote_any
            row_data["மொத்தம்"] = total
            row_data["Fails"] = fails
            row_data["தோல்வி விவரம்"] = f"({', '.join(fail_subs)})" if fail_subs else ""
            report_rows.append(row_data)

        # Dashboard UI
        m1, m2, m3, m4, m5 = st.columns(5)
        m1.markdown(f'<div class="main-stat"><div class="stat-label">மொத்தம்</div><div class="stat-val">{len(students)}</div></div>', unsafe_allow_html=True)
        m2.markdown(f'<div class="main-stat"><div class="stat-label">எழுதியவர்</div><div class="stat-val">{present_count}</div></div>', unsafe_allow_html=True)
        m3.markdown(f'<div class="main-stat"><div class="stat-label">தேர்ச்சி</div><div class="stat-val">{pass_count}</div></div>', unsafe_allow_html=True)
        m4.markdown(f'<div class="main-stat"><div class="stat-label">தோல்வி</div><div class="stat-val">{present_count - pass_count}</div></div>', unsafe_allow_html=True)
        p_per = round((pass_count/present_count)*100, 1) if present_count > 0 else 0
        m5.markdown(f'<div class="main-stat"><div class="stat-label">தேர்ச்சி %</div><div class="stat-val" style="color:#16a34a">{p_per}%</div></div>', unsafe_allow_html=True)

        # ⚡ 2. Expanders
        st.markdown("---")
        e1, e2 = st.columns(2)
        with e1:
            with st.expander(f"🏆 100/100 எடுத்தவர்கள்: {len(centum_winners)} பேர்"):
                for cw in centum_winners: st.markdown(f'<div class="info-card">🥇 {cw}</div>', unsafe_allow_html=True)
        with e2:
            with st.expander(f"🚶 தேர்வுக்கே வராதவர்கள்: {len(full_absents)} பேர்"):
                for fa in full_absents: st.markdown(f'<div class="info-card">❌ {fa}</div>', unsafe_allow_html=True)

        # ⚡ 3. பாடவாரி பகுப்பாய்வு
        st.divider()
        st.subheader("📈 பாடவாரி விரிவான பகுப்பாய்வு")
        # (இங்கு பாடவாரி அட்டவணை வரும் - 9_Classwise போன்றே)
        subj_stats = []
        for sub in relevant_subjects:
            s_code = sub['subject_code']
            v_marks = [m.get('total_mark', 0) for m in marks_data if m['subject_id'] == s_code and not m.get('is_absent')]
            if v_marks:
                v = pd.Series(v_marks)
                subj_stats.append({
                    "பாடம்": sub['subject_name'], "எழுதியவர்": len(v), "தேர்ச்சி": len(v[v >= 35]),
                    "சராசரி": round(v.mean(),1), "அதிகபட்சம்": int(v.max()), "குறைந்தபட்சம்": int(v.min())
                })
        st.table(pd.DataFrame(subj_stats))

        # ⚡ 4. Toggle Switch (இங்கே கேட்கப்பட்டது போல தள்ளி வைக்கப்பட்டுள்ளது)
        st.divider()
        st.subheader("📋 முழுமையான மதிப்பெண் பட்டியல்")
        show_breakup = st.toggle("🔍 அகமதிப்பீடு மற்றும் செய்முறை மதிப்பெண்களைக் காட்டு (Theory/Internal/Practical)")

        # மதிப்பெண் பட்டியலைத் தயார் செய்தல் (Toggle-க்கு ஏற்ப)
        final_list = []
        for s in report_rows:
            row = {"பெயர்": s['பெயர்'], "மொத்தம்": s['மொத்தம்'], "Fails": s['Fails'], "தோல்வி விவரம்": s['தோல்வி விவரம்'], "Present": s['Present']}
            for sub in relevant_subjects:
                m = next((m for m in marks_data if m['emis_no'] == s['emis_no'] and m['subject_id'] == sub['subject_code']), None)
                if m:
                    if not m.get('is_absent'):
                        tot = m.get('total_mark', 0)
                        if show_breakup:
                            th, i, p = m.get('theory_mark',0), m.get('internal_mark',0), m.get('practical_mark',0)
                            row[sub['subject_name']] = f"{tot}\n({th}+{i}+{p})" if sub.get('has_practical') else f"{tot}\n({th}+{i})"
                        else:
                            row[sub['subject_name']] = tot
                    else: row[sub['subject_name']] = "ABS"
                else: row[sub['subject_name']] = "-"
            final_list.append(row)

        df_final = pd.DataFrame(final_list).sort_values(by=["Fails", "மொத்தம்"], ascending=[True, False]).reset_index(drop=True)
        
        # Smart Rank
        ranks = []; r_val = 1
        for idx, row in df_final.iterrows():
            if row["Fails"] == 0 and row["Present"]:
                ranks.append(str(r_val)); r_val += 1
            else: ranks.append("-")
        df_final.insert(0, "Rank", ranks)

        # காண்பிக்க வேண்டிய வரிசைகள்
        cols = ["Rank", "பெயர்"] + [s['subject_name'] for s in relevant_subjects] + ["மொத்தம்", "தோல்வி விவரம்"]
        st.dataframe(df_final[cols].style.map(lambda v: 'color: red' if "ABS" in str(v) or (isinstance(v, int) and v < 35) else '')
                     .set_properties(**{'background-color': '#f8fafc'}, subset=['மொத்தம்']), use_container_width=True, hide_index=True)
