import streamlit as st
import pandas as pd
from supabase import create_client

# --- Supabase இணைப்பு ---
def get_supabase_client():
    if "supabase_instance" not in st.session_state:
        st.session_state.supabase_instance = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
    return st.session_state.supabase_instance

supabase = get_supabase_client()

st.set_page_config(page_title="Final Gender-wise Analysis", layout="wide")

# ⚡ CSS வடிவமைப்பு
st.markdown("""
    <style>
    .stDataFrame td { font-weight: bold !important; font-size: 14px !important; white-space: pre !important; }
    .main-stat { background-color: #f8fafc; border: 1px solid #e2e8f0; padding: 10px; border-radius: 10px; text-align: center; min-height: 100px; }
    .stat-val { font-size: 20px; font-weight: bold; color: #1e293b; line-height: 1.2; }
    .stat-label { font-size: 13px; color: #64748b; font-weight: bold; margin-bottom: 5px; }
    .gender-sub { font-size: 12px; color: #3b82f6; font-weight: bold; display: block; margin-top: 3px; }
    .info-card { padding: 8px; border-radius: 5px; margin-bottom: 5px; border-left: 4px solid #10b981; background-color: #f0fdf4; font-size: 14px; }
    </style>
    """, unsafe_allow_html=True)

st.title("📊 வகுப்பு வாரி விரிவான தேர்ச்சிப் பகுப்பாய்வு")

# --- 1. தரவுகள் பெறுதல் ---
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
    split_gender = st.toggle("🔍 ஆண் பெண் பிரித்து (Female + Male = Total)", value=True)

    matching_sections = sorted([c for c in all_classes_raw if str(c).startswith(sel_base_class)])
    all_students, union_subs = [], []
    
    for section in matching_sections:
        c_info = next((c for c in classes_data if (c.get('class_n') == section or c.get('class_name') == section)), None)
        if c_info:
            g_info = next((g for g in groups_data if g['group_name'] == c_info.get('group_name')), None)
            if g_info and g_info.get('subjects'):
                g_list = [s.strip() for s in g_info['subjects'].split(',')]
                studs = supabase.table("exam_mapping").select("exam_no, student_name, emis_no, gender").eq("exam_id", exam_id).eq("class_name", section).execute().data
                if studs:
                    for s in studs:
                        s['section'] = section; s['my_subjects'] = g_list
                        all_students.append(s)
                for gs in g_list:
                    if gs not in union_subs: union_subs.append(gs)

    marks_data = supabase.table("marks").select("*").eq("exam_id", exam_id).execute().data
    relevant_subjects = [s for s in subjects_data if s['subject_name'] in union_subs]

    if all_students:
        report_rows, centum_list, absent_list = [], [], []
        # புள்ளிவிவரக் கணக்கீடு
        st_count = {
            "total": {"A": 0, "M": 0, "F": 0},
            "present": {"A": 0, "M": 0, "F": 0},
            "pass": {"A": 0, "M": 0, "F": 0}
        }
        all_marks_list = {"A": [], "M": [], "F": []}
        fail_cats = {1: [], 2: [], 3: [], 4: [], 5: [], "All": []}

        for s in all_students:
            raw_gen = str(s.get('gender', 'Male')).strip().upper()
            gen = 'F' if raw_gen.startswith('F') else 'M'
            st_count["total"]["A"] += 1; st_count["total"][gen] += 1
            
            row_raw = {"பிரிவு": s['section'], "பெயர்": s['student_name'], "gender": gen}
            total_m, fails, wrote_any, fail_subs = 0, 0, False, []
            my_subs = s['my_subjects']

            for sub in relevant_subjects:
                sn = sub['subject_name']
                if sn not in my_subs:
                    row_raw[sn] = "-"; continue
                
                m = next((m for m in marks_data if m['emis_no'] == s['emis_no'] and m['subject_id'] == sub['subject_code']), None)
                if m and not m.get('is_absent'):
                    wrote_any = True
                    tot, th, pr = m.get('total_mark',0), m.get('theory_mark',0), m.get('practical_mark',0)
                    
                    # ✅ தேர்ச்சி விதிமுறை: Theory >= 15 & Practical >= 15 & Total >= 35
                    is_p = (th >= 15 and pr >= 15 and tot >= 35) if sub.get('has_practical') else (tot >= 35)
                    total_m += tot
                    if not is_p: 
                        fails += 1; fail_subs.append(sn)
                    if tot == 100: centum_list.append(f"{s['student_name']} ({s['section']} - {sn})")
                    row_raw[sn] = {"tot": tot, "pass": is_p, "th": th, "pr": pr}
                else:
                    row_raw[sn] = "ABS"; fails += 1; fail_subs.append(sn)

            if wrote_any:
                st_count["present"]["A"] += 1; st_count["present"][gen] += 1
                all_marks_list["A"].append(total_m); all_marks_list[gen].append(total_m)
                if fails == 0:
                    st_count["pass"]["A"] += 1; st_count["pass"][gen] += 1
                else:
                    txt = f"{s['student_name']} ({s['section']} - {', '.join(fail_subs)})"
                    if fails >= len(my_subs): fail_cats["All"].append(txt)
                    elif fails in [1,2,3,4,5]: fail_cats[fails].append(txt)
            else: absent_list.append(f"{s['student_name']} ({s['section']})")

            row_raw.update({"மொத்தம்": total_m, "Fails": fails, "தோல்வி விவரம்": f"({', '.join(fail_subs)})" if fail_subs else ""})
            report_rows.append(row_raw)

        # --- 📊 Dashboard (பாலின விவரங்களுடன்) ---
        st.subheader(f"📌 {sel_base_class}-ஆம் வகுப்பு ஒட்டுமொத்தப் புள்ளிவிவரம்")
        m_dash = st.columns(6)
        
        # Total, Present, Pass
        keys = ["total", "present", "pass"]
        titles = ["Total Students", "Exam Present", "Passed Students"]
        for i, k in enumerate(keys):
            val = st_count[k]["A"]
            gen_txt = f"<span class='gender-sub'>({st_count[k]['F']}F | {st_count[k]['M']}M)</span>" if split_gender else ""
            m_dash[i].markdown(f'<div class="main-stat"><div class="stat-label">{titles[i]}</div><div class="stat-val">{val}{gen_txt}</div></div>', unsafe_allow_html=True)
        
        # Fail Calculation
        fail_a = st_count["present"]["A"] - st_count["pass"]["A"]
        fail_f = st_count["present"]["F"] - st_count["pass"]["F"]
        fail_m = st_count["present"]["M"] - st_count["pass"]["M"]
        f_gen = f"<span class='gender-sub'>({fail_f}F | {fail_m}M)</span>" if split_gender else ""
        m_dash[3].markdown(f'<div class="main-stat"><div class="stat-label">Failed Students</div><div class="stat-val">{fail_a}{f_gen}</div></div>', unsafe_allow_html=True)
        
        # Pass Percentage
        p_a = round((st_count["pass"]["A"]/st_count["present"]["A"])*100, 1) if st_count["present"]["A"]>0 else 0
        p_f = round((st_count["pass"]["F"]/st_count["present"]["F"])*100, 1) if st_count["present"]["F"]>0 else 0
        p_m = round((st_count["pass"]["M"]/st_count["present"]["M"])*100, 1) if st_count["present"]["M"]>0 else 0
        p_gen = f"<span class='gender-sub'>({p_f}%F | {p_m}%M)</span>" if split_gender else ""
        m_dash[4].markdown(f'<div class="main-stat"><div class="stat-label">Pass Percentage</div><div class="stat-val" style="color:#16a34a">{p_a}%{p_gen}</div></div>', unsafe_allow_html=True)
        
        # Class Average
        avg_a = round(sum(all_marks_list["A"])/len(all_marks_list["A"]), 1) if all_marks_list["A"] else 0
        avg_f = round(sum(all_marks_list["F"])/len(all_marks_list["F"]), 1) if all_marks_list["F"] else 0
        avg_m = round(sum(all_marks_list["M"])/len(all_marks_list["M"]), 1) if all_marks_list["M"] else 0
        avg_gen = f"<span class='gender-sub'>({avg_f}F | {avg_m}M)</span>" if split_gender else ""
        m_dash[5].markdown(f'<div class="main-stat"><div class="stat-label">Class Average</div><div class="stat-val" style="color:#3b82f6">{avg_a}{avg_gen}</div></div>', unsafe_allow_html=True)

        # --- 🏆 Centum & Absents ---
        st.divider()
        e_c1, e_c2 = st.columns(2)
        with e_c1:
            with st.expander(f"🏆 100/100 எடுத்தவர்கள்: {len(centum_list)} பேர்"):
                for itm in centum_list: st.markdown(f'<div class="info-card">🥇 {itm}</div>', unsafe_allow_html=True)
        with e_c2:
            with st.expander(f"🚶 தேர்வுக்கே வராதவர்கள்: {len(absent_list)} பேர்"):
                for itm in absent_list: st.markdown(f'<div class="info-card" style="border-left-color:#ef4444; background-color:#fef2f2;">❌ {itm}</div>', unsafe_allow_html=True)

        # --- 📈 பாடவாரி ஆய்வு ---
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
                                   "Max": max(marks_list), "Avg": round(sum(marks_list)/len(marks_list),1), "Only This": only_this})
        st.dataframe(pd.DataFrame(subj_stats), use_container_width=True, hide_index=True)

        # --- 📋 முழுமையான மதிப்பெண் பட்டியல் ---
        st.divider()
        st.subheader("📋 முழுமையான மதிப்பெண் பட்டியல்")
        show_t_p = st.toggle("🔍 தியரி மற்றும் செய்முறை மதிப்பெண்களைக் காட்டு (T+P)", value=True)
        
        final_list = []
        for r in report_rows:
            d_row = {"பிரிவு": r['பிரிவு'], "பெயர்": r['பெயர்'], "மொத்தம்": r['மொத்தம்'], "Fails": r['Fails'], "தோல்வி விவரம்": r['தோல்வி விவரம்']}
            for sub in relevant_subjects:
                sn = sub['subject_name']
                v = r.get(sn)
                if isinstance(v, dict):
                    d_row[sn] = f"{v['tot']}\n({v['th']}+{v['pr']})" if show_t_p else v['tot']
                else: d_row[sn] = v
            final_list.append(d_row)
        
        df_f = pd.DataFrame(final_list).sort_values(by=["Fails", "மொத்தம்"], ascending=[True, False]).reset_index(drop=True)
        ranks, rv = [], 1
        for idx, row in df_f.iterrows():
            if int(row["Fails"]) == 0: ranks.append(str(rv)); rv += 1
            else: ranks.append("-")
        df_f.insert(0, "Rank", ranks)

        st.dataframe(df_f.style.apply(lambda x: ['color: red' if 'ABS' in str(v) or (isinstance(v, int) and v < 35) or (isinstance(v, str) and '\n' in v and int(v.split('\n')[0])<35) else '' for v in x], axis=1), use_container_width=True, hide_index=True)

        # --- 📉 தோல்விப் பட்டியல் ---
        st.divider()
        st.subheader("📉 தோல்வி அடைந்த மாணவர்களின் விவரம்")
        b1, b2 = st.columns(2)
        with b1:
            for n in [1, 2, 3]:
                if fail_cats[n]:
                    with st.expander(f"❌ {n} பாடத்தில் தோல்வி: {len(fail_cats[n])} பேர்"):
                        for itm in fail_cats[n]: st.markdown(f'<div class="info-card" style="border-left-color:#f59e0b; background-color:#fffbeb;">⚠️ {itm}</div>', unsafe_allow_html=True)
        with b2:
            for n in [4, 5, "All"]:
                if fail_cats[n]:
                    label = f"{n} பாடத்தில் தோல்வி" if n != "All" else "அனைத்துப் பாடங்களிலும் தோல்வி"
                    with st.expander(f"🔴 {label}: {len(fail_cats[n])} பேர்"):
                        for itm in fail_cats[n]: st.markdown(f'<div class="info-card" style="border-left-color:#ef4444; background-color:#fef2f2;">🚩 {itm}</div>', unsafe_allow_html=True)
