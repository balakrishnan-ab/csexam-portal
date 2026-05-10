import streamlit as st
import pandas as pd
from supabase import create_client
from utils import add_school_header 

# --- 1. பக்க அமைப்பு ---
st.set_page_config(page_title="Class-wise Overall Analysis", layout="wide")
add_school_header()

# --- 2. Supabase இணைப்பு ---
def get_supabase_client():
    if "supabase_instance" not in st.session_state:
        st.session_state.supabase_instance = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
    return st.session_state.supabase_instance

supabase = get_supabase_client()

# --- 3. CSS ஸ்டைலிங் ---
st.markdown("""
    <style>
    .stDataFrame td { font-weight: bold !important; font-size: 13px !important; white-space: pre !important; }
    .metric-container { display: flex; flex-wrap: wrap; gap: 10px; justify-content: space-between; width: 100%; margin-bottom: 20px; }
    .metric-card { background-color: #f8fafc; border: 1px solid #e2e8f0; padding: 12px 8px; border-radius: 10px; text-align: center; flex: 1 1 calc(15% - 10px); min-width: 110px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    .stat-val { font-size: 22px; font-weight: bold; color: #1e293b; line-height: 1.2; }
    .stat-label { font-size: 11px; color: #64748b; font-weight: bold; text-transform: uppercase; }
    .gender-sub { font-size: 10px; color: #3b82f6; font-weight: bold; display: block; margin-top: 2px; }
    .responsive-subtitle { font-size: 20px; font-weight: bold; color: #334155; border-bottom: 2px solid #e2e8f0; margin: 15px 0 10px 0; }
    .info-card { padding: 10px; border-radius: 6px; margin-bottom: 8px; border-left: 4px solid #10b981; background-color: #f0fdf4; font-size: 14px; font-weight: bold; }
    .topper-card { padding: 8px; border-radius: 5px; margin-bottom: 5px; background-color: #fffbeb; border-left: 4px solid #f59e0b; font-size: 13px; }
    </style>
    """, unsafe_allow_html=True)

# --- 4. தரவுகளைப் பெறுதல் ---
exams_data = supabase.table("exams").select("*").execute().data
classes_data = supabase.table("classes").select("*").execute().data
groups_data = supabase.table("groups").select("*").execute().data
subjects_data = supabase.table("subjects").select("*").execute().data

# Subject Code Mapping (வரிசைப்படுத்த உதவும்)
sub_info_map = {s['subject_name']: s for s in subjects_data}

# --- 5. தேர்வு மற்றும் வகுப்புத் தெரிவு ---
col1, col2 = st.columns(2)
sel_exam_name = col1.selectbox("1. தேர்வு (Exam):", [e['exam_name'] for e in exams_data])
exam_id = next((e['id'] for e in exams_data if e['exam_name'] == sel_exam_name), None)

if exam_id:
    mapped_data = supabase.table("exam_mapping").select("class_name").eq("exam_id", exam_id).execute().data
    if mapped_data:
        mapped_classes = sorted(list(set([str(m['class_name']).split('-')[0].strip() for m in mapped_data if m['class_name']])), key=lambda x: int(x) if x.isdigit() else x)
        sel_class_main = col2.selectbox("2. வகுப்பு (Class):", ["-- தேர்வு செய்க --"] + mapped_classes)
    else:
        st.error("மாணவர்கள் ஒதுக்கப்படவில்லை.")
        sel_class_main = "-- தேர்வு செய்க --"
else:
    sel_class_main = col2.selectbox("2. வகுப்பு (Class):", ["-- தேர்வு செய்க --"])

# --- 6. பகுப்பாய்வு ---
if sel_exam_name and sel_class_main != "-- தேர்வு செய்க --":
    split_gender = st.toggle("🔍 ஆண் பெண் பிரித்து காட்டு", value=True)
    st.divider()

    relevant_sections = sorted(list(set([m['class_name'] for m in mapped_data if str(m['class_name']).startswith(sel_class_main)])))
    
    studs_mapping = supabase.table("exam_mapping").select("exam_no, student_name, emis_no, class_name").eq("exam_id", exam_id).in_("class_name", relevant_sections).execute().data
    all_students_base = supabase.table("students").select("emis_no, gender").execute().data
    gender_map = {str(st_b['emis_no']): str(st_b['gender']).strip() for st_b in all_students_base}
    marks_data = supabase.table("marks").select("*").eq("exam_id", exam_id).execute().data

    if studs_mapping:
        # --- பாடங்களை Subject Code அடிப்படையில் வரிசைப்படுத்துதல் ---
        raw_g_list = []
        for sec in relevant_sections:
            c_info = next((c for c in classes_data if (c.get('class_n') == sec or c.get('class_name') == sec)), None)
            if c_info:
                g_info = next((g for g in groups_data if g['group_name'] == c_info.get('group_name')), None)
                if g_info: raw_g_list.extend([s.strip() for s in g_info['subjects'].split(',')])
        
        unique_subs = list(set(raw_g_list))
        # இங்கேயே subject_code படி வரிசைப்படுத்துகிறோம்
        g_list = sorted(unique_subs, key=lambda x: str(sub_info_map.get(x, {}).get('subject_code', '999')))

        # கணக்கீடுகள்
        report_rows, centum_list, absent_list = [], [], []
        st_count = {"total": {"A": 0, "M": 0, "F": 0}, "present": {"A": 0, "M": 0, "F": 0}, "pass": {"A": 0, "M": 0, "F": 0}, "fail": {"A": 0, "M": 0, "F": 0}}
        subject_stats = {sn: {"total": {"M": 0, "F": 0}, "app": {"M": 0, "F": 0}, "pass": {"M": 0, "F": 0}, "fail": {"M": 0, "F": 0}, "marks": [], "only_this": 0, "student_marks": []} for sn in g_list}
        fail_cats = {1: [], 2: [], 3: [], 4: [], 5: [], "All": []}

        for s in studs_mapping:
            emis_key = str(s['emis_no'])
            r_g = gender_map.get(emis_key, 'Male').strip().lower()
            gen = 'F' if (r_g.startswith('f') or 'பெண்' in r_g) else 'M'
            st_count["total"]["A"] += 1; st_count["total"][gen] += 1
            
            row_raw = {"Rank": "-", "தேர்வு எண்": s.get('exam_no', '-'), "பெயர்": s['student_name'], "பிரிவு": s['class_name'], "gender": gen}
            total_m, fails, wrote_any, fail_subs, student_centums = 0, 0, False, [], []

            for sn in g_list:
                s_obj = sub_info_map.get(sn)
                if not s_obj: continue
                m = next((m for m in marks_data if str(m['emis_no']) == emis_key and m['subject_id'] == s_obj['subject_code']), None)
                
                if m:
                    subject_stats[sn]["total"][gen] += 1
                    is_abs = m.get('is_absent')
                    if is_abs is None:
                        row_raw[sn] = "EXEMPTED"; continue
                    if not is_abs:
                        wrote_any = True
                        tot, th, pr = m.get('total_mark', 0), m.get('theory_mark', 0), m.get('practical_mark', 0)
                        internal = tot - th - pr
                        eval_type = str(s_obj.get('eval_type', '90+10'))
                        is_subj_pass = (th >= 15 and pr >= 15 and tot >= 35) if '70' in eval_type else (tot >= 35)
                        tag = f"({th}+{pr}+{internal})" if '70' in eval_type else f"({th}+{internal})"
                        
                        subject_stats[sn]["app"][gen] += 1
                        subject_stats[sn]["marks"].append(tot)
                        subject_stats[sn]["student_marks"].append({"name": s['student_name'], "sec": s['class_name'], "mark": tot})
                        if is_subj_pass: 
                            subject_stats[sn]["pass"][gen] += 1
                            if tot == 100: student_centums.append(sn)
                        else: 
                            subject_stats[sn]["fail"][gen] += 1; fails += 1; fail_subs.append(sn)
                        total_m += tot
                        row_raw[sn] = {"tot": tot, "tag": tag, "pass": is_subj_pass}
                    else:
                        row_raw[sn] = "ABS"; fails += 1; fail_subs.append(sn)
                        subject_stats[sn]["app"][gen] += 1; subject_stats[sn]["fail"][gen] += 1
                else: row_raw[sn] = "-"

            if wrote_any:
                st_count["present"]["A"] += 1; st_count["present"][gen] += 1
                if fails == 0: st_count["pass"]["A"] += 1; st_count["pass"][gen] += 1
                else:
                    st_count["fail"]["A"] += 1; st_count["fail"][gen] += 1
                    if fails == 1: subject_stats[fail_subs[0]]["only_this"] += 1
                    txt = f"{s['student_name']} ({s['class_name']}) - ({', '.join(fail_subs)})"
                    if fails >= len(fail_subs): fail_cats["All"].append(txt)
                    elif fails in [1,2,3,4,5]: fail_cats[fails].append(txt)
                if student_centums: centum_list.append(f"{s['student_name']} ({s['class_name']} - {', '.join(student_centums)})")
            else: absent_list.append(f"{s['student_name']} ({s['class_name']})")

            row_raw.update({"மொத்தம்": total_m, "Fails": fails, "தோல்வி விவரம்": f"({', '.join(fail_subs)})" if fail_subs else ""})
            report_rows.append(row_raw)

        # --- Dashboard & Tables ---
        st.markdown(f'<div class="responsive-subtitle">📊 {sel_class_main}-ஆம் வகுப்பு ஒட்டுமொத்தப் புள்ளிவிவரம்</div>', unsafe_allow_html=True)
        def get_gt(k): return f"<span class='gender-sub'>({st_count[k]['F']}F|{st_count[k]['M']}M)</span>" if split_gender else ""
        
        st.markdown(f"""
            <div class="metric-container">
                <div class="metric-card"><div class="stat-label">Total</div><div class="stat-val">{st_count['total']['A']}{get_gt('total')}</div></div>
                <div class="metric-card"><div class="stat-label">Present</div><div class="stat-val">{st_count['present']['A']}{get_gt('present')}</div></div>
                <div class="metric-card"><div class="stat-label">Pass</div><div class="stat-val" style="color:green">{st_count['pass']['A']}{get_gt('pass')}</div></div>
                <div class="metric-card"><div class="stat-label">Fail</div><div class="stat-val" style="color:red">{st_count['fail']['A']}{get_gt('fail')}</div></div>
                <div class="metric-card"><div class="stat-label">Pass %</div><div class="stat-val" style="color:green">{round((st_count['pass']['A']/st_count['present']['A'])*100,1) if st_count['present']['A']>0 else 0}%</div></div>
            </div>
        """, unsafe_allow_html=True)

        # பாடவாரி விரிவான பகுப்பாய்வு (Subject Code வரிசையில்)
        st.markdown('<div class="responsive-subtitle">📈 பாடவாரி விரிவான பகுப்பாய்வு (By Code Order)</div>', unsafe_allow_html=True)
        sub_df_list = []
        for sn in g_list:
            stt = subject_stats[sn]
            if not (stt['app']['F'] + stt['app']['M']) > 0: continue
            avg_s = round(sum(stt["marks"])/len(stt["marks"]),1) if stt["marks"] else 0
            sub_df_list.append({
                "Subject": sn, "Code": sub_info_map.get(sn, {}).get('subject_code', '-'),
                "Total": f"{stt['total']['F']+stt['total']['M']} ({stt['total']['F']}F|{stt['total']['M']}M)" if split_gender else str(stt['total']['F']+stt['total']['M']),
                "Pass%": f"{round((stt['pass']['F']+stt['pass']['M'])/(stt['app']['F']+stt['app']['M'])*100,1) if (stt['app']['F']+stt['app']['M'])>0 else 0}%",
                "Min": min(stt["marks"]), "Max": max(stt["marks"]), "Avg": avg_s
            })
        st.table(pd.DataFrame(sub_df_list))

        # மதிப்பெண் பட்டியல்
        st.markdown('<div class="responsive-subtitle">📋 முழுமையான மதிப்பெண் பட்டியல்</div>', unsafe_allow_html=True)
        df_sorted = pd.DataFrame(report_rows).sort_values(by=["Fails", "மொத்தம்"], ascending=[True, False]).reset_index(drop=True)
        
        rv = 1
        for idx, row in df_sorted.iterrows():
            if int(row["Fails"]) == 0: df_sorted.at[idx, "Rank"] = rv; rv += 1
        
        final_disp = []
        for _, r in df_sorted.iterrows():
            d_row = {"Rank": r["Rank"], "பெயர்": r['பெயர்'], "பிரிவு": r['பிரிவு'], "மொத்தம்": r['மொத்தம்'], "Fails": r['Fails']}
            for sn in g_list:
                v = r.get(sn)
                d_row[sn] = v['tot'] if isinstance(v, dict) else v
            final_disp.append(d_row)

        st.dataframe(pd.DataFrame(final_disp), use_container_width=True, hide_index=True)
