import streamlit as st
import pandas as pd
from supabase import create_client

# --- Supabase இணைப்பு ---
def get_supabase_client():
    if "supabase_instance" not in st.session_state:
        st.session_state.supabase_instance = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
    return st.session_state.supabase_instance

supabase = get_supabase_client()

st.set_page_config(page_title="Refined Class Analysis", layout="wide")

# ⚡ CSS - ஸ்டைலிங்
st.markdown("""
    <style>
    .stDataFrame td { font-weight: bold !important; font-size: 15px !important; }
    .main-stat { background-color: #f8fafc; border: 1px solid #e2e8f0; padding: 10px; border-radius: 10px; text-align: center; min-height: 100px; }
    .stat-val { font-size: 20px; font-weight: bold; color: #1e293b; line-height: 1.2; }
    .stat-label { font-size: 13px; color: #64748b; font-weight: bold; margin-bottom: 5px; }
    .gender-sub { font-size: 12px; color: #3b82f6; font-weight: bold; display: block; margin-top: 3px; }
    .info-box { padding: 8px; border-radius: 5px; margin-bottom: 5px; border-left: 4px solid #3b82f6; background-color: #f1f5f9; font-size: 14px; }
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
    
    # 🔍 Toggle Switch
    st.divider()
    split_gender = st.toggle("🔍 ஆண் பெண் பிரித்து (Female + Male = Total)")

    matching_sections = [c for c in all_classes_raw if str(c).startswith(sel_base_class)]
    all_students = []
    union_subs = []

    for section in matching_sections:
        c_info = next((c for c in classes_data if (c.get('class_n') == section or c.get('class_name') == section)), None)
        if c_info:
            g_info = next((g for g in groups_data if g['group_name'] == c_info.get('group_name')), None)
            if g_info and g_info.get('subjects'):
                g_list = [s.strip() for s in g_info['subjects'].split(',')]
                for gs in g_list:
                    if gs not in union_subs: union_subs.append(gs)
                
                # EMIS மூலம் மாணவர் பாலினத் தகவலை எடுக்க மாணவர்கள் அட்டவணையுடன் இணைக்கிறோம்
                studs = supabase.table("exam_mapping").select("exam_no, student_name, emis_no, gender").eq("exam_id", exam_id).eq("class_name", section).execute().data
                if studs:
                    for s in studs:
                        s['section'] = section
                        all_students.append(s)

    marks_data = supabase.table("marks").select("*").eq("exam_id", exam_id).execute().data
    relevant_subjects = [s for s in subjects_data if s['subject_name'] in union_subs]

    if all_students:
        report_rows = []
        stats = {"total": {"A": 0, "M": 0, "F": 0}, "present": {"A": 0, "M": 0, "F": 0}, "pass": {"A": 0, "M": 0, "F": 0}}
        all_present_marks = {"A": [], "M": [], "F": []}
        centum_winners, full_absents = [], []

        for s in all_students:
            # பாலினத்தைச் சுத்தம் செய்தல்
            raw_gen = str(s.get('gender', 'Male')).strip().upper()
            gen = 'F' if raw_gen.startswith('F') else 'M'
            
            stats["total"]["A"] += 1
            stats["total"][gen] += 1
            
            row = {"பிரிவு": s['section'], "பெயர்": s['student_name'], "Gender": gen}
            total = 0; fails = 0; wrote_any = False
            
            for sub in relevant_subjects:
                m = next((m for m in marks_data if m['emis_no'] == s['emis_no'] and m['subject_id'] == sub['subject_code']), None)
                if m:
                    tot, th, pr = m.get('total_mark', 0), m.get('theory_mark', 0), m.get('practical_mark', 0)
                    if not m.get('is_absent'):
                        wrote_any = True
                        total += tot
                        # தேர்ச்சி விதி (Theory 15 + Practical 15 logic)
                        is_p = (th >= 15 and pr >= 15 and tot >= 35) if sub.get('has_practical') else (tot >= 35)
                        if not is_p: fails += 1
                        if tot == 100: centum_winners.append({"பெயர்": s['student_name'], "பாடம்": sub['subject_name'], "பிரிவு": s['section']})
                        row[sub['subject_name']] = tot
                    else:
                        row[sub['subject_name']] = "ABS"; fails += 1
                else: row[sub['subject_name']] = "-"

            if wrote_any:
                stats["present"]["A"] += 1
                stats["present"][gen] += 1
                all_present_marks["A"].append(total)
                all_present_marks[gen].append(total)
                if fails == 0:
                    stats["pass"]["A"] += 1
                    stats["pass"][gen] += 1
            else:
                full_absents.append(s)

            row.update({"எழுதியவர்": wrote_any, "மொத்தம்": total, "Fails": fails})
            report_rows.append(row)

        df = pd.DataFrame(report_rows)

        # ⚡ Dashboard Logic
        st.subheader(f"📌 {sel_base_class}-ஆம் வகுப்பு ஒட்டுமொத்தப் புள்ளிவிவரம்")
        cols = st.columns(6)
        labels = ["மொத்தம்", "எழுதியவர்", "தேர்ச்சி", "தோல்வி", "தேர்ச்சி %", "வகுப்பு சராசரி"]
        
        def get_stat_html(label, key, is_avg=False):
            if is_avg:
                avg_a = round(sum(all_present_marks["A"])/len(all_present_marks["A"]), 1) if all_present_marks["A"] else 0
                if split_gender:
                    avg_f = round(sum(all_present_marks["F"])/len(all_present_marks["F"]), 1) if all_present_marks["F"] else 0
                    avg_m = round(sum(all_present_marks["M"])/len(all_present_marks["M"]), 1) if all_present_marks["M"] else 0
                    return f'<div class="main-stat"><div class="stat-label">{label}</div><div class="stat-val">{avg_a}<span class="gender-sub">({avg_f}F | {avg_m}M)</span></div></div>'
                return f'<div class="main-stat"><div class="stat-label">{label}</div><div class="stat-val">{avg_a}</div></div>'
            
            if key == "fail":
                all_v, f_v, m_v = stats["present"]["A"]-stats["pass"]["A"], stats["present"]["F"]-stats["pass"]["F"], stats["present"]["M"]-stats["pass"]["M"]
            elif key == "per":
                all_v = f"{round((stats['pass']['A']/stats['present']['A'])*100, 1)}%" if stats['present']['A'] > 0 else "0%"
                f_v = f"{round((stats['pass']['F']/stats['present']['F'])*100, 1)}%" if stats['present']['F'] > 0 else "0%"
                m_v = f"{round((stats['pass']['M']/stats['present']['M'])*100, 1)}%" if stats['present']['M'] > 0 else "0%"
            else:
                all_v, f_v, m_v = stats[key]["A"], stats[key]["F"], stats[key]["M"]

            gender_txt = f'<span class="gender-sub">({f_v}F | {m_v}M)</span>' if split_gender else ""
            return f'<div class="main-stat"><div class="stat-label">{label}</div><div class="stat-val">{all_v}{gender_txt}</div></div>'

        cols[0].markdown(get_stat_html(labels[0], "total"), unsafe_allow_html=True)
        cols[1].markdown(get_stat_html(labels[1], "present"), unsafe_allow_html=True)
        cols[2].markdown(get_stat_html(labels[2], "pass"), unsafe_allow_html=True)
        cols[3].markdown(get_stat_html(labels[3], "fail"), unsafe_allow_html=True)
        cols[4].markdown(get_stat_html(labels[4], "per"), unsafe_allow_html=True)
        cols[5].markdown(get_stat_html(labels[5], "", is_avg=True), unsafe_allow_html=True)

        # ⚡ பாடவாரி பகுப்பாய்வு
        st.divider()
        st.subheader("📈 பாடவாரி விரிவான பகுப்பாய்வு")
        subj_stats = []
        for sub in relevant_subjects:
            sn = sub['subject_name']
            if sn in df.columns:
                v_all = pd.to_numeric(df[sn], errors='coerce').dropna()
                if not v_all.empty:
                    row_s = {"Subject": sn}
                    # பாலினம் பிரித்து கணக்கிடுதல்
                    f_marks = pd.to_numeric(df[df['Gender']=='F'][sn], errors='coerce').dropna()
                    m_marks = pd.to_numeric(df[df['Gender']=='M'][sn], errors='coerce').dropna()
                    
                    def get_subj_split(all_v, f_v, m_v, is_pass=False):
                        if is_pass:
                            a_p, f_p, m_p = len(all_v[all_v>=35]), len(f_v[f_v>=35]), len(m_v[m_v>=35])
                            return f"{a_p} ({f_p}F|{m_p}M)" if split_gender else a_p
                        return f"{len(all_v)} ({len(f_v)}F|{len(m_v)}M)" if split_gender else len(all_v)

                    row_s["App"] = get_subj_split(v_all, f_marks, m_marks)
                    row_s["Pass"] = get_subj_split(v_all, f_marks, m_marks, is_pass=True)
                    row_s["Pass %"] = f"{round((len(v_all[v_all>=35])/len(v_all))*100,1)}%"
                    row_s["Max"] = int(v_all.max())
                    row_s["Min"] = int(v_all.min())
                    row_s["Avg"] = round(v_all.mean(), 1)
                    subj_stats.append(row_s)
        st.table(pd.DataFrame(subj_stats))

        # (மற்ற பகுதிகள் - 100/100, வராதவர்கள் மற்றும் பட்டியல் அப்படியே தொடரும்)
        st.divider()
        st.subheader("📋 முழுமையான மதிப்பெண் பட்டியல்")
        df_final = df.sort_values(by=["Fails", "மொத்தம்"], ascending=[True, False]).reset_index(drop=True)
        ranks = []; rv = 1
        for idx, r in df_final.iterrows():
            if r["Fails"] == 0 and r["எழுதியவர்"]: ranks.append(str(rv)); rv += 1
            else: ranks.append("-")
        df_final.insert(0, "Rank", ranks)
        st.dataframe(df_final.drop(columns=['Gender','எழுதியவர்']).style.map(lambda v: 'color: red' if v == "ABS" or (isinstance(v, int) and v < 35) else '').set_properties(**{'background-color': '#f8fafc'}, subset=['மொத்தம்']), use_container_width=True)
