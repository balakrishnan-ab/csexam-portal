import streamlit as st
import pandas as pd
from supabase import create_client

# --- Supabase இணைப்பு ---
def get_supabase_client():
    if "supabase_instance" not in st.session_state:
        st.session_state.supabase_instance = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
    return st.session_state.supabase_instance

supabase = get_supabase_client()

st.set_page_config(page_title="Evaluation Type Based Analysis", layout="wide")

# ⚡ CSS - ஸ்டைலிங்
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
    sub_info_map = {s['subject_name']: s for s in subjects_data}

    if all_students:
        report_rows, centum_list, absent_list = [], [], []
        st_count = {"total": {"A": 0, "M": 0, "F": 0}, "present": {"A": 0, "M": 0, "F": 0}, "pass": {"A": 0, "M": 0, "F": 0}}
        all_marks_list = {"A": [], "M": [], "F": []}
        fail_cats = {1: [], 2: [], 3: [], 4: [], 5: [], "All": []}
        
        # பாடவாரி தரவுகளை சேமிக்க (Subject Analysis Storage)
        subject_stats = {sn: {"app": 0, "pass": 0, "fail": 0, "marks": [], "only_this": 0} for sn in union_subs}

        for s in all_students:
            raw_gen = str(s.get('gender', 'Male')).strip().upper()
            gen = 'F' if raw_gen.startswith('F') else 'M'
            st_count["total"]["A"] += 1; st_count["total"][gen] += 1
            
            row_raw = {"பிரிவு": s['section'], "பெயர்": s['student_name'], "gender": gen}
            total_m, fails, wrote_any, fail_subs = 0, 0, False, []
            my_subs = s['my_subjects']

            for sn in union_subs:
                if sn not in my_subs:
                    row_raw[sn] = "-"; continue
                
                s_obj = sub_info_map.get(sn)
                if not s_obj: continue
                
                m = next((m for m in marks_data if m['emis_no'] == s['emis_no'] and m['subject_id'] == s_obj['subject_code']), None)
                if m and not m.get('is_absent'):
                    wrote_any = True
                    tot, th, pr = m.get('total_mark', 0), m.get('theory_mark', 0), m.get('practical_mark', 0)
                    
                    # தேர்ச்சி விதிமுறை
                    eval_type_str = str(s_obj.get('eval_type', '90+10'))
                    is_subj_pass = True
                    if '70' in eval_type_str:
                        if th < 15 or pr < 15 or tot < 35: is_subj_pass = False
                    else:
                        if tot < 35: is_subj_pass = False
                    
                    # பாடவாரி கணக்கீடு
                    subject_stats[sn]["app"] += 1
                    subject_stats[sn]["marks"].append(tot)
                    if is_subj_pass: subject_stats[sn]["pass"] += 1
                    else: 
                        subject_stats[sn]["fail"] += 1
                        fail_subs.append(sn)
                        fails += 1
                    
                    total_m += tot
                    if tot == 100: centum_list.append(f"{s['student_name']} ({s['section']} - {sn})")
                    row_raw[sn] = {"tot": tot, "pass": is_subj_pass, "th": th, "pr": pr}
                else:
                    row_raw[sn] = "ABS"; fails += 1; fail_subs.append(sn)
                    subject_stats[sn]["app"] += 1 # ABS-உம் எழுதியவராக சில இடங்களில் கருதப்படும், இல்லையெனில் இதைத் தவிர்க்கலாம்
                    subject_stats[sn]["fail"] += 1

            if wrote_any:
                st_count["present"]["A"] += 1; st_count["present"][gen] += 1
                all_marks_list["A"].append(total_m); all_marks_list[gen].append(total_m)
                if fails == 0:
                    st_count["pass"]["A"] += 1; st_count["pass"][gen] += 1
                else:
                    txt = f"{s['student_name']} ({s['section']} - {', '.join(fail_subs)})"
                    if fails == 1: subject_stats[fail_subs[0]]["only_this"] += 1
                    if fails >= len(my_subs): fail_cats["All"].append(txt)
                    elif fails in [1,2,3,4,5]: fail_cats[fails].append(txt)
            else: 
                absent_list.append(f"{s['student_name']} ({s['section']})")

            row_raw.update({"மொத்தம்": total_m, "Fails": fails, "தோல்வி விவரம்": f"({', '.join(fail_subs)})" if fail_subs else ""})
            report_rows.append(row_raw)

        # --- 📊 3. Dashboard ---
        st.subheader(f"📌 {sel_base_class}-ஆம் வகுப்பு ஒட்டுமொத்தப் புள்ளிவிவரம்")
        m_dash = st.columns(6)
        titles = ["Total", "Present", "Pass", "Fail", "Pass %", "Class Avg"]
        
        for i, k in enumerate(["total", "present", "pass"]):
            val = st_count[k]["A"]
            gen_txt = f"<span class='gender-sub'>({st_count[k]['F']}F | {st_count[k]['M']}M)</span>" if split_gender else ""
            m_dash[i].markdown(f'<div class="main-stat"><div class="stat-label">{titles[i]}</div><div class="stat-val">{val}{gen_txt}</div></div>', unsafe_allow_html=True)
        
        f_a = st_count["present"]["A"] - st_count["pass"]["A"]
        f_gen = f"<span class='gender-sub'>({st_count['present']['F']-st_count['pass']['F']}F | {st_count['present']['M']-st_count['pass']['M']}M)</span>" if split_gender else ""
        m_dash[3].markdown(f'<div class="main-stat"><div class="stat-label">Fail</div><div class="stat-val">{f_a}{f_gen}</div></div>', unsafe_allow_html=True)
        
        p_a = round((st_count["pass"]["A"]/st_count["present"]["A"])*100, 1) if st_count["present"]["A"]>0 else 0
        p_gen = f"<span class='gender-sub'>({round((st_count['pass']['F']/st_count['present']['F'])*100,1) if st_count['present']['F']>0 else 0}% | {round((st_count['pass']['M']/st_count['present']['M'])*100,1) if st_count['present']['M']>0 else 0}%)</span>" if split_gender else ""
        m_dash[4].markdown(f'<div class="main-stat"><div class="stat-label">Pass %</div><div class="stat-val" style="color:#16a34a">{p_a}%{p_gen}</div></div>', unsafe_allow_html=True)
        
        avg_a = round(sum(all_marks_list["A"])/len(all_marks_list["A"]), 1) if all_marks_list["A"] else 0
        m_dash[5].markdown(f'<div class="main-stat"><div class="stat-label">Class Avg</div><div class="stat-val" style="color:#3b82f6">{avg_a}</div></div>', unsafe_allow_html=True)

        st.divider()
        with st.expander(f"🏆 100/100 எடுத்தவர்கள்: {len(centum_list)} பேர்"):
            for itm in centum_list: st.markdown(f'<div class="info-card">🥇 {itm}</div>', unsafe_allow_html=True)

        # --- 📈 4. பாடவாரி விரிவான பகுப்பாய்வு (புதிய பகுதி) ---
        st.subheader("📈 பாடவாரி விரிவான பகுப்பாய்வு")
        sub_anal_list = []
        for sn in union_subs:
            stats = subject_stats[sn]
            avg_sub = round(sum(stats["marks"])/len(stats["marks"]),1) if stats["marks"] else 0
            pass_p = round((stats["pass"]/stats["app"])*100,1) if stats["app"]>0 else 0
            sub_anal_list.append({
                "Subject": sn, "App": stats["app"], "Pass": stats["pass"], "Fail": stats["fail"],
                "Pass %": f"{pass_p}%", "Max": max(stats["marks"]) if stats["marks"] else 0,
                "Min": min(stats["marks"]) if stats["marks"] else 0, "Avg": avg_sub, "Only This": stats["only_this"]
            })
        st.table(pd.DataFrame(sub_anal_list))

        # --- 📉 5. முழுமையான மதிப்பெண் பட்டியல் ---
        st.divider()
        st.subheader("📋 முழுமையான மதிப்பெண் பட்டியல்")
        show_t_p = st.toggle("🔍 தியரி மற்றும் செய்முறை மதிப்பெண்களைக் காட்டு (T+P)", value=True)
        
        final_list = []
        for r in report_rows:
            d_row = {"பிரிவு": r['பிரிவு'], "பெயர்": r['பெயர்'], "மொத்தம்": r['மொத்தம்'], "Fails": r['Fails'], "தோல்வி விவரம்": r['தோல்வி விவரம்']}
            for sn in union_subs:
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

        def color_fails(val):
            if val == 'ABS' or val == '-': return 'color: red'
            if isinstance(val, str) and '\n' in val:
                try:
                    score = int(val.split('\n')[0])
                    if score < 35: return 'color: red'
                except: pass
            if isinstance(val, (int, float)) and val < 35: return 'color: red'
            return ''

        st.dataframe(df_f.style.map(color_fails), use_container_width=True, hide_index=True)
