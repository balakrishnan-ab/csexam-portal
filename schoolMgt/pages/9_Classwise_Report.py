import streamlit as st
import pandas as pd
from supabase import create_client

# --- Supabase இணைப்பு ---
def get_supabase_client():
    if "supabase_instance" not in st.session_state:
        st.session_state.supabase_instance = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
    return st.session_state.supabase_instance

supabase = get_supabase_client()

st.set_page_config(page_title="Complete Class Analysis", layout="wide")

# ⚡ CSS - ஸ்டைலிங்
st.markdown("""
    <style>
    .stDataFrame td { font-weight: bold !important; font-size: 14px !important; white-space: pre !important; }
    .main-stat { background-color: #f8fafc; border: 1px solid #e2e8f0; padding: 10px; border-radius: 10px; text-align: center; min-height: 100px; }
    .stat-val { font-size: 20px; font-weight: bold; color: #1e293b; line-height: 1.2; }
    .stat-label { font-size: 13px; color: #64748b; font-weight: bold; margin-bottom: 5px; }
    .gender-sub { font-size: 12px; color: #3b82f6; font-weight: bold; display: block; margin-top: 3px; }
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
all_classes_raw = [c.get('class_n') or c.get('class_name') for c in classes_data]
base_classes = sorted(list(set([str(c).split('-')[0].strip() for c in all_classes_raw if c])), key=lambda x: int(x) if x.isdigit() else x)
sel_base_class = c2.selectbox("2. வகுப்பு:", ["-- தேர்வு செய்க --"] + base_classes)

if sel_exam_name and sel_base_class != "-- தேர்வு செய்க --":
    exam_id = next(e['id'] for e in exams_data if e['exam_name'] == sel_exam_name)
    
    st.divider()
    split_gender = st.toggle("🔍 ஆண் பெண் பிரித்து (Female + Male = Total)")

    matching_sections = sorted([c for c in all_classes_raw if str(c).startswith(sel_base_class)])
    all_students, union_subs = [], []

    for section in matching_sections:
        c_info = next((c for c in classes_data if (c.get('class_n') == section or c.get('class_name') == section)), None)
        if c_info:
            g_info = next((g for g in groups_data if g['group_name'] == c_info.get('group_name')), None)
            if g_info and g_info.get('subjects'):
                g_list = [s.strip() for s in g_info['subjects'].split(',')]
                for gs in g_list:
                    if gs not in union_subs: union_subs.append(gs)
                studs = supabase.table("exam_mapping").select("exam_no, student_name, emis_no, gender").eq("exam_id", exam_id).eq("class_name", section).execute().data
                if studs:
                    for s in studs:
                        s['section'] = section
                        all_students.append(s)

    marks_data = supabase.table("marks").select("*").eq("exam_id", exam_id).execute().data
    relevant_subjects = [s for s in subjects_data if s['subject_name'] in union_subs]

    if all_students:
        report_rows, centum_list, absent_list = [], [], []
        stats = {"total": {"A": 0, "M": 0, "F": 0}, "present": {"A": 0, "M": 0, "F": 0}, "pass": {"A": 0, "M": 0, "F": 0}}
        all_present_marks = {"A": [], "M": [], "F": []}
        fail_cats = {1: [], 2: [], 3: [], 4: [], 5: [], "All": []}

        for s in all_students:
            raw_gen = str(s.get('gender', 'Male')).strip().upper()
            gen = 'F' if raw_gen.startswith('F') else 'M'
            stats["total"]["A"] += 1; stats["total"][gen] += 1
            
            row_raw = {"பிரிவு": s['section'], "பெயர்": s['student_name'], "gender": gen, "emis_no": s['emis_no']}
            total_m, fails, wrote_any, fail_subs = 0, 0, False, []
            
            for sub in relevant_subjects:
                m = next((m for m in marks_data if m['emis_no'] == s['emis_no'] and m['subject_id'] == sub['subject_code']), None)
                if m and not m.get('is_absent'):
                    wrote_any = True
                    tot, th, pr, in_m = m.get('total_mark',0), m.get('theory_mark',0), m.get('practical_mark',0), m.get('internal_mark',0)
                    is_p = (th >= 15 and pr >= 15 and tot >= 35) if sub.get('has_practical') else (tot >= 35)
                    total_m += tot
                    if not is_p: fails += 1; fail_subs.append(sub['subject_name'])
                    if tot == 100: centum_list.append(f"{s['student_name']} ({s['section']} - {sub['subject_name']})")
                    row_raw[sub['subject_name']] = {"tot": tot, "th": th, "pr": pr, "in": in_m, "prac": sub.get('has_practical'), "pass": is_p}
                else:
                    row_raw[sub['subject_name']] = "ABS"
                    if m and m.get('is_absent'): fails += 1; fail_subs.append(sub['subject_name'])

            if wrote_any:
                stats["present"]["A"] += 1; stats["present"][gen] += 1
                all_present_marks["A"].append(total_m); all_present_marks[gen].append(total_m)
                if fails == 0: stats["pass"]["A"] += 1; stats["pass"][gen] += 1
                else:
                    s_fail_txt = f"{s['student_name']} ({s['section']} - {', '.join(fail_subs)})"
                    if fails >= len(relevant_subjects): fail_cats["All"].append(s_fail_txt)
                    elif fails in fail_cats: fail_cats[fails].append(s_fail_txt)
            else: absent_list.append(f"{s['student_name']} ({s['section']})")

            row_raw.update({"Present": wrote_any, "மொத்தம்": total_m, "Fails": fails, "தோல்வி விவரம்": f"({', '.join(fail_subs)})" if fail_subs else ""})
            report_rows.append(row_raw)

        # --- Dashboard ---
        st.subheader(f"📌 {sel_base_class}-ஆம் வகுப்பு ஒட்டுமொத்தப் புள்ளிவிவரம்")
        m = st.columns(6)
        lbls = ["மொத்தம்", "எழுதியவர்", "தேர்ச்சி", "தோல்வி", "தேர்ச்சி %", "வகுப்பு சராசரி"]
        for i, key in enumerate(["total", "present", "pass"]):
            val = stats[key]["A"]
            gen_txt = f"<span class='gender-sub'>({stats[key]['F']}F | {stats[key]['M']}M)</span>" if split_gender else ""
            m[i].markdown(f'<div class="main-stat"><div class="stat-label">{lbls[i]}</div><div class="stat-val">{val}{gen_txt}</div></div>', unsafe_allow_html=True)
        
        f_all = stats["present"]["A"] - stats["pass"]["A"]
        f_gen = f"<span class='gender-sub'>({stats['present']['F']-stats['pass']['F']}F | {stats['present']['M']-stats['pass']['M']}M)</span>" if split_gender else ""
        m[3].markdown(f'<div class="main-stat"><div class="stat-label">தோல்வி</div><div class="stat-val">{f_all}{f_gen}</div></div>', unsafe_allow_html=True)
        p_per = round((stats["pass"]["A"]/stats["present"]["A"])*100, 1) if stats["present"]["A"] > 0 else 0
        m[4].markdown(f'<div class="main-stat"><div class="stat-label">தேர்ச்சி %</div><div class="stat-val" style="color:#16a34a">{p_per}%</div></div>', unsafe_allow_html=True)
        c_avg = round(sum(all_present_marks["A"])/len(all_present_marks["A"]), 1) if all_present_marks["A"] else 0
        m[5].markdown(f'<div class="main-stat"><div class="stat-label">வகுப்பு சராசரி</div><div class="stat-val" style="color:#3b82f6">{c_avg}</div></div>', unsafe_allow_html=True)

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
                    elif r['Fails'] == 1: only_this += 1
            if t_app > 0:
                subj_stats.append({"Subject": sn, "App": t_app, "Pass": t_pas, "Fail": t_app-t_pas, "Pass %": f"{round((t_pas/t_app)*100,1)}%", 
                                   "Max": max(marks_list), "Min": min(marks_list), "Avg": round(sum(marks_list)/len(marks_list),1), "Only This": only_this})
        st.dataframe(pd.DataFrame(subj_stats), use_container_width=True, hide_index=True)

        # --- 📋 முழுமையான மதிப்பெண் பட்டியல் ---
        st.divider()
        st.subheader("📋 முழுமையான மதிப்பெண் பட்டியல்")
        show_breakup = st.toggle("🔍 அகமதிப்பீடு மற்றும் செய்முறை மதிப்பெண்களைக் காட்டு (Theory/Internal/Practical)")
        
        final_list = []
        for r in report_rows:
            d_row = {"பிரிவு": r['பிரிவு'], "பெயர்": r['பெயர்'], "மொத்தம்": r['மொத்தம்'], "Fails": r['Fails'], "தோல்வி விவரம்": r['தோல்வி விவரம்'], "Present": r['Present']}
            for sub in relevant_subjects:
                v = r.get(sub['subject_name'])
                if isinstance(v, dict):
                    if show_breakup:
                        d_row[sub['subject_name']] = f"{v['tot']}\n({v['th']}+{v['in']}+{v['pr']})" if v['prac'] else f"{v['tot']}\n({v['th']}+{v['in']})"
                    else: d_row[sub['subject_name']] = v['tot']
                else: d_row[sub['subject_name']] = v
            final_list.append(d_row)

        df = pd.DataFrame(final_list).sort_values(by=["Fails", "மொத்தம்"], ascending=[True, False]).reset_index(drop=True)
        ranks = []; rv = 1
        for idx, row in df.iterrows():
            if row["Fails"] == 0 and row["Present"]: ranks.append(str(rv)); rv += 1
            else: ranks.append("-")
        df.insert(0, "Rank", ranks)
        
        def style_f(row):
            styles = ['' for _ in row.index]
            for i, col in enumerate(row.index):
                val = row[col]
                if col in [s['subject_name'] for s in relevant_subjects]:
                    if val == "ABS": styles[i] = 'color: red'
                    elif isinstance(val, str) and '\n' in val:
                        p = val.split('\n')[1].strip('()').split('+')
                        th_v, pr_v = int(p[0]), (int(p[2]) if len(p)>2 else 35)
                        if th_v < 15 or pr_v < 15 or int(val.split('\n')[0]) < 35: styles[i] = 'color: red'
                    elif isinstance(val, (int, float)) and val < 35: styles[i] = 'color: red'
            return styles

        st.dataframe(df[["Rank", "பிரிவு", "பெயர்"] + [s['subject_name'] for s in relevant_subjects] + ["மொத்தம்", "தோல்வி விவரம்"]].style.apply(style_f, axis=1)
                     .set_properties(**{'background-color': '#f8fafc'}, subset=['மொத்தம்']), use_container_width=True, hide_index=True)

        # --- 📉 தோல்விப் பட்டியல் மற்றும் வராதோர் விவரம் ---
        st.divider()
        st.subheader("📉 தோல்வி மற்றும் வருகை விவரங்கள்")
        b1, b2 = st.columns(2)
        with b1:
            if centum_list:
                with st.expander(f"🏆 100/100 எடுத்தவர்கள்: {len(centum_list)} பேர்"):
                    for item in centum_list: st.markdown(f'<div class="info-card">🥇 {item}</div>', unsafe_allow_html=True)
            for n in [1, 2, 3]:
                if len(fail_cats[n]) > 0:
                    with st.expander(f"❌ {n} பாடத்தில் தோல்வி: {len(fail_cats[n])} பேர்"):
                        for item in fail_cats[n]: st.markdown(f'<div class="info-card fail-card">⚠️ {item}</div>', unsafe_allow_html=True)
        with b2:
            if absent_list:
                with st.expander(f"🚶 தேர்வுக்கே வராதவர்கள்: {len(absent_list)} பேர்"):
                    for item in absent_list: st.markdown(f'<div class="info-card critical-card">❌ {item}</div>', unsafe_allow_html=True)
            for n in [4, 5, "All"]:
                if len(fail_cats[n]) > 0:
                    label = f"{n} பாடத்தில் தோல்வி" if n != "All" else "அனைத்துப் பாடங்களிலும் தோல்வி"
                    with st.expander(f"🔴 {label}: {len(fail_cats[n])} பேர்"):
                        for item in fail_cats[n]: st.markdown(f'<div class="info-card critical-card">🚩 {item}</div>', unsafe_allow_html=True)
