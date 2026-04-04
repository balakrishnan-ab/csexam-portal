import streamlit as st
import pandas as pd
from supabase import create_client

# --- Supabase இணைப்பு ---
def get_supabase_client():
    if "supabase_instance" not in st.session_state:
        st.session_state.supabase_instance = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
    return st.session_state.supabase_instance

supabase = get_supabase_client()

st.set_page_config(page_title="Detailed Student Analysis", layout="wide")

# ⚡ CSS வடிவமைப்பு
st.markdown("""
    <style>
    .stDataFrame td { font-weight: bold !important; font-size: 14px !important; white-space: pre !important; }
    .main-stat { background-color: #f8fafc; border: 1px solid #e2e8f0; padding: 10px; border-radius: 10px; text-align: center; margin-bottom: 10px; min-height: 100px; }
    .stat-val { font-size: 22px; font-weight: bold; color: #1e293b; line-height: 1.1; }
    .gender-sub { font-size: 13px; color: #3b82f6; font-weight: bold; display: block; margin-top: 2px; }
    .stat-label { font-size: 13px; color: #64748b; font-weight: bold; margin-bottom: 5px; }
    .info-card { padding: 8px; border-radius: 5px; margin-bottom: 5px; border-left: 4px solid #10b981; background-color: #f0fdf4; font-size: 14px; }
    .fail-card { border-left-color: #f59e0b; background-color: #fffbeb; }
    .critical-card { border-left-color: #ef4444; background-color: #fef2f2; }
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
        class_total_list = []
        centum_list = []
        absent_list = []
        # தோல்வி வகைப்பாட்டிற்கான டிக்ஸனரி
        fail_categories = {1: [], 2: [], 3: [], 4: [], 5: [], "All": []}

        for s in students:
            raw_gen = str(s.get('gender', 'Male')).strip().upper()
            gen = 'F' if raw_gen.startswith('F') else 'M'
            stats["total"]["all"] += 1; stats["total"][gen] += 1
            
            row_raw = {"பெயர்": s['student_name'], "gender": gen, "emis_no": s['emis_no']}
            total_m, fails, wrote_any, fail_subs = 0, 0, False, []
            
            for sub in relevant_subjects:
                m = next((m for m in marks_data if m['emis_no'] == s['emis_no'] and m['subject_id'] == sub['subject_code']), None)
                if m and not m.get('is_absent'):
                    wrote_any = True
                    tot, th, pr = m.get('total_mark', 0), m.get('theory_mark', 0), m.get('practical_mark', 0)
                    is_p = (th >= 15 and pr >= 15 and tot >= 35) if sub.get('has_practical') else (tot >= 35)
                    total_m += tot
                    if not is_p: 
                        fails += 1
                        fail_subs.append(sub['subject_name'])
                    if tot == 100: centum_list.append(f"{s['student_name']} ({sub['subject_name']})")
                    row_raw[sub['subject_name']] = {"tot": tot, "th": th, "pr": pr, "prac": sub.get('has_practical'), "pass": is_p}
                else:
                    row_raw[sub['subject_name']] = "ABS"
                    fails += 1
                    fail_subs.append(sub['subject_name'])
            
            if wrote_any:
                stats["present"]["all"] += 1; stats["present"][gen] += 1
                class_total_list.append(total_m)
                if fails == 0: 
                    stats["pass"]["all"] += 1; stats["pass"][gen] += 1
                else:
                    # தோல்விப் பட்டியலை வகைப்படுத்துதல்
                    student_fail_info = f"{s['student_name']} ({', '.join(fail_subs)})"
                    if fails >= len(relevant_subjects): fail_categories["All"].append(student_fail_info)
                    elif fails in fail_categories: fail_categories[fails].append(student_fail_info)
            else:
                absent_list.append(s['student_name'])

            row_raw.update({"Present": wrote_any, "Fails": fails, "மொத்தம்": total_m, "தோல்வி விவரம்": f"({', '.join(fail_subs)})" if fail_subs else ""})
            report_rows.append(row_raw)

        # --- Dashboard ---
        st.subheader(f"📌 {sel_class} ஒட்டுமொத்தப் புள்ளிவிவரம்")
        m = st.columns(6)
        titles = ["Total", "Present", "Pass", "Fail", "Pass %", "Class Avg"]
        for i, key in enumerate(["total", "present", "pass"]):
            val_all = stats[key]['all']
            gender_line = f"<span class='gender-sub'>({stats[key]['F']}F + {stats[key]['M']}M)</span>" if split_gender else ""
            m[i].markdown(f'<div class="main-stat"><div class="stat-label">{titles[i]}</div><div class="stat-val">{val_all}{gender_line}</div></div>', unsafe_allow_html=True)
        
        f_all = stats["present"]["all"] - stats["pass"]["all"]
        f_line = f"<span class='gender-sub'>({stats['present']['F']-stats['pass']['F']}F + {stats['present']['M']-stats['pass']['M']}M)</span>" if split_gender else ""
        m[3].markdown(f'<div class="main-stat"><div class="stat-label">Fail</div><div class="stat-val">{f_all}{f_line}</div></div>', unsafe_allow_html=True)
        
        p_per = round((stats["pass"]["all"]/stats["present"]["all"])*100, 1) if stats["present"]["all"] > 0 else 0
        m[4].markdown(f'<div class="main-stat"><div class="stat-label">Pass %</div><div class="stat-val" style="color:#16a34a">{p_per}%</div></div>', unsafe_allow_html=True)
        m[5].markdown(f'<div class="main-stat"><div class="stat-label">Class Avg</div><div class="stat-val" style="color:#3b82f6">{round(sum(class_total_list)/len(class_total_list),1) if class_total_list else 0}</div></div>', unsafe_allow_html=True)

        # --- Expanders (Centum, Absents, and Fail Categories) ---
        st.divider()
        st.subheader("📋 விரிவான மாணவர் பட்டியல்கள் (Expander)")
        col_e1, col_e2 = st.columns(2)
        
        with col_e1:
            with st.expander(f"🏆 100/100 எடுத்தவர்கள்: {len(centum_list)} பேர்"):
                for item in centum_list: st.markdown(f'<div class="info-card">🥇 {item}</div>', unsafe_allow_html=True)
            
            for n in [1, 2, 3]:
                with st.expander(f"❌ {n} பாடத்தில் தோல்வி: {len(fail_categories[n])} பேர்"):
                    for item in fail_categories[n]: st.markdown(f'<div class="info-card fail-card">⚠️ {item}</div>', unsafe_allow_html=True)

        with col_e2:
            with st.expander(f"🚶 தேர்வுக்கே வராதவர்கள்: {len(absent_list)} பேர்"):
                for item in absent_list: st.markdown(f'<div class="info-card critical-card">❌ {item}</div>', unsafe_allow_html=True)
            
            for n in [4, 5, "All"]:
                label = f"{n} பாடத்தில் தோல்வி" if n != "All" else "அனைத்துப் பாடங்களிலும் தோல்வி"
                with st.expander(f"🔴 {label}: {len(fail_categories[n])} பேர்"):
                    for item in fail_categories[n]: st.markdown(f'<div class="info-card critical-card">🚩 {item}</div>', unsafe_allow_html=True)

        # --- 📈 பாடவாரி விரிவான பகுப்பாய்வு ---
        st.divider()
        st.subheader("📈 பாடவாரி விரிவான பகுப்பாய்வு")
        subj_stats = []
        for sub in relevant_subjects:
            sn = sub['subject_name']
            t_app, t_pas, marks_list, only_this = 0, 0, [], 0
            for r in report_rows:
                v = r.get(sn)
                if isinstance(v, dict):
                    t_app += 1; marks_list.append(v['tot'])
                    if v['pass']: t_pas += 1
                    else:
                        if r['Fails'] == 1: only_this += 1
            if t_app > 0:
                subj_stats.append({"Subject": sn, "App": t_app, "Pass": t_pas, "Fail": t_app-t_pas, "Pass %": f"{round((t_pas/t_app)*100,1)}%", 
                                   "Max": max(marks_list), "Min": min(marks_list), "Avg": round(sum(marks_list)/len(marks_list),1), "Only This": only_this})
        st.dataframe(pd.DataFrame(subj_stats), use_container_width=True, hide_index=True)

        # --- 📋 முழுமையான மதிப்பெண் பட்டியல் ---
        st.divider()
        st.subheader("📋 முழுமையான மதிப்பெண் பட்டியல்")
        final_list = []
        for r in report_rows:
            d_row = {"பெயர்": r['பெயர்'], "மொத்தம்": r['மொத்தம்'], "Fails": r['Fails'], "தோல்வி விவரம்": r['தோல்வி விவரம்'], "Present": r['Present']}
            for sub in relevant_subjects:
                v = r.get(sub['subject_name'])
                d_row[sub['subject_name']] = v['tot'] if isinstance(v, dict) else v
            final_list.append(d_row)

        df = pd.DataFrame(final_list).sort_values(by=["Fails", "மொத்தம்"], ascending=[True, False]).reset_index(drop=True)
        ranks = []
        rv = 1
        for idx, row in df.iterrows():
            if row["Fails"] == 0 and row["Present"]: ranks.append(str(rv)); rv += 1
            else: ranks.append("-")
        df.insert(0, "Rank", ranks)

        st.dataframe(df[["Rank", "பெயர்"] + [s['subject_name'] for s in relevant_subjects] + ["மொத்தம்", "தோல்வி விவரம்"]].style.apply(lambda x: ['color: red' if (isinstance(v, int) and v < 35) or v == "ABS" else '' for v in x], axis=1), use_container_width=True, hide_index=True)
