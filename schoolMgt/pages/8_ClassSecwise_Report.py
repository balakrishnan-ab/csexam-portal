import streamlit as st
import pandas as pd
from supabase import create_client
from utils import add_school_header 

# --- பக்க அமைப்பு (Set Page Config) ---
st.set_page_config(page_title="Section-wise Analysis", layout="wide")
add_school_header()

def get_supabase_client():
    if "supabase_instance" not in st.session_state:
        st.session_state.supabase_instance = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
    return st.session_state.supabase_instance

supabase = get_supabase_client()

# --- CSS ஸ்டைலிங் (Dashboard & Cards) ---
st.markdown("""
    <style>
    .stDataFrame td { font-weight: bold !important; font-size: 13px !important; white-space: pre !important; }
    .metric-container { display: flex; flex-wrap: wrap; gap: 10px; justify-content: space-between; width: 100%; margin-bottom: 20px; }
    .metric-card { background-color: #f8fafc; border: 1px solid #e2e8f0; padding: 12px 8px; border-radius: 10px; text-align: center; flex: 1 1 calc(15% - 10px); min-width: 110px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    .stat-val { font-size: clamp(18px, 3vw, 24px); font-weight: bold; color: #1e293b; line-height: 1.2; }
    .stat-label { font-size: 11px; color: #64748b; font-weight: bold; text-transform: uppercase; }
    .gender-sub { font-size: 10px; color: #3b82f6; font-weight: bold; display: block; margin-top: 2px; }
    .responsive-subtitle { font-size: clamp(16px, 3.5vw, 22px); font-weight: bold; color: #334155; border-bottom: 2px solid #e2e8f0; margin: 15px 0 10px 0; }
    .info-card { padding: 10px; border-radius: 6px; margin-bottom: 8px; border-left: 4px solid #10b981; background-color: #f0fdf4; font-size: 14px; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- 1. தரவுகள் பெறுதல் ---
exams_data = supabase.table("exams").select("*").execute().data
classes_data = supabase.table("classes").select("*").execute().data
groups_data = supabase.table("groups").select("*").execute().data
subjects_data = supabase.table("subjects").select("*").execute().data

col1, col2 = st.columns(2)
sel_exam_name = col1.selectbox("1. தேர்வு:", [e['exam_name'] for e in exams_data])
all_sections = sorted(list(set([c.get('class_n') or c.get('class_name') for c in classes_data if c.get('class_n') or c.get('class_name')])))
sel_section = col2.selectbox("2. வகுப்பு மற்றும் பிரிவு:", ["-- தேர்வு செய்க --"] + all_sections)

if sel_exam_name and sel_section != "-- தேர்வு செய்க --":
    exam_id = next(e['id'] for e in exams_data if e['exam_name'] == sel_exam_name)
    split_gender = st.toggle("🔍 ஆண் பெண் பிரித்து காட்டு", value=True)

    # exam_mapping-லிருந்து மாணவர்களைப் பெறுதல்
    studs_mapping = supabase.table("exam_mapping").select("exam_no, student_name, emis_no, class_name").eq("exam_id", exam_id).eq("class_name", sel_section).execute().data
    
    # மாணவர்களின் பாலினத்தை students அட்டவணையிலிருந்து பெறுதல்
    all_students_base = supabase.table("students").select("emis_no, gender").execute().data
    gender_map = {str(st_b['emis_no']): str(st_b['gender']).strip() for st_b in all_students_base}

    c_info = next((c for c in classes_data if (c.get('class_n') == sel_section or c.get('class_name') == sel_section)), None)
    
    if studs_mapping and c_info:
        g_info = next((g for g in groups_data if g['group_name'] == c_info.get('group_name')), None)
        g_list = [s.strip() for s in g_info['subjects'].split(',')] if g_info else []
        marks_data = supabase.table("marks").select("*").eq("exam_id", exam_id).execute().data
        sub_info_map = {s['subject_name']: s for s in subjects_data}

        report_rows, centum_list, absent_list = [], [], []
        st_count = {"total": {"A": 0, "M": 0, "F": 0}, "present": {"A": 0, "M": 0, "F": 0}, "pass": {"A": 0, "M": 0, "F": 0}}
        subject_stats = {sn: {"total": {"M": 0, "F": 0}, "app": {"M": 0, "F": 0}, "pass": {"M": 0, "F": 0}, "fail": {"M": 0, "F": 0}, "marks": [], "only_this": 0} for sn in g_list}
        fail_cats = {1: [], 2: [], 3: [], 4: [], 5: [], "All": []}

        for s in studs_mapping:
            # --- துல்லியமான பாலினக் கண்டறிதல் ---
            emis_key = str(s['emis_no'])
            raw_gen = gender_map.get(emis_key, 'Male').strip().lower()
            
            # நிபந்தனை: 'f' இல் தொடங்கினால் அல்லது 'பெண்' என இருந்தால் அது Female
            if raw_gen.startswith('f') or 'பெண்' in raw_gen:
                gen = 'F'
            else:
                gen = 'M'
            
            st_count["total"]["A"] += 1; st_count["total"][gen] += 1
            row_raw = {"தேர்வு எண்": s.get('exam_no', '-'), "பெயர்": s['student_name'], "gender": gen}
            total_m, fails, wrote_any, fail_subs, student_centums = 0, 0, False, [], []

            for sn in g_list:
                subject_stats[sn]["total"][gen] += 1
                s_obj = sub_info_map.get(sn)
                m = next((m for m in marks_data if str(m['emis_no']) == emis_key and m['subject_id'] == s_obj['subject_code']), None) if s_obj else None
                
                if m:
                    # is_absent 'None' (null) எனில் விலக்கு (Exempted)
                    is_abs = m.get('is_absent')
                    
                    if is_abs is None:
                        row_raw[sn] = "EXEMPTED"
                        continue

                    if not is_abs:
                        wrote_any = True
                        tot, th, pr = m.get('total_mark', 0), m.get('theory_mark', 0), m.get('practical_mark', 0)
                        internal = tot - th - pr
                        eval_type = str(s_obj.get('eval_type', '90+10'))
                        
                        is_subj_pass = True
                        if '70' in eval_type:
                            if th < 15 or pr < 15 or tot < 35: is_subj_pass = False
                            tag = f"({th}+{pr}+{internal})"
                        else:
                            if tot < 35: is_subj_pass = False
                            tag = f"({th}+{internal})"
                        
                        subject_stats[sn]["app"][gen] += 1
                        subject_stats[sn]["marks"].append(tot)
                        if is_subj_pass: 
                            subject_stats[sn]["pass"][gen] += 1
                            if tot == 100: student_centums.append(sn)
                        else: 
                            subject_stats[sn]["fail"][gen] += 1; fails += 1; fail_subs.append(sn)
                        total_m += tot
                        row_raw[sn] = {"tot": tot, "tag": tag, "pass": is_subj_pass}
                    else: # ABS (True)
                        row_raw[sn] = "ABS"; fails += 1; fail_subs.append(sn)
                        subject_stats[sn]["app"][gen] += 1
                        subject_stats[sn]["fail"][gen] += 1
                else:
                    row_raw[sn] = "-"

            if wrote_any:
                st_count["present"]["A"] += 1; st_count["present"][gen] += 1
                if fails == 0: 
                    st_count["pass"]["A"] += 1; st_count["pass"][gen] += 1
                else:
                    if fails == 1: subject_stats[fail_subs[0]]["only_this"] += 1
                    txt = f"{s['student_name']} - ({', '.join(fail_subs)})"
                    if fails >= len(g_list): fail_cats["All"].append(txt)
                    elif fails in [1,2,3,4,5]: fail_cats[fails].append(txt)
                if student_centums: centum_list.append(f"{s['student_name']} ({', '.join(student_centums)})")
            else:
                absent_list.append(s['student_name'])

            row_raw.update({"மொத்தம்": total_m, "Fails": fails, "தோல்வி விவரம்": f"({', '.join(fail_subs)})" if fail_subs else ""})
            report_rows.append(row_raw)

        # --- Dashboard Metrics ---
        st.markdown(f'<div class="responsive-subtitle">📊 {sel_section} பிரிவு ஒட்டுமொத்தப் புள்ளிவிவரம்</div>', unsafe_allow_html=True)
        def get_gt(k): return f"<span class='gender-sub'>({st_count[k]['F']}F|{st_count[k]['M']}M)</span>" if split_gender else ""
        
        st.markdown(f"""
            <div class="metric-container">
                <div class="metric-card"><div class="stat-label">Total</div><div class="stat-val">{st_count['total']['A']}{get_gt('total')}</div></div>
                <div class="metric-card"><div class="stat-label">Present</div><div class="stat-val">{st_count['present']['A']}{get_gt('present')}</div></div>
                <div class="metric-card"><div class="stat-label">Pass</div><div class="stat-val" style="color:green">{st_count['pass']['A']}{get_gt('pass')}</div></div>
                <div class="metric-card"><div class="stat-label">Pass %</div><div class="stat-val">{round((st_count['pass']['A']/st_count['present']['A'])*100,1) if st_count['present']['A']>0 else 0}%</div></div>
            </div>
        """, unsafe_allow_html=True)

        st.divider()
        e1, e2 = st.columns(2)
        with e1:
            with st.expander(f"🏆 100/100 பெற்றவர்கள்: {len(centum_list)} பேர்"):
                for itm in centum_list: st.markdown(f'<div class="info-card">🥇 {itm}</div>', unsafe_allow_html=True)
        with e2:
            with st.expander(f"🚶 தேர்வு எழுதாதவர்கள்: {len(absent_list)} பேர்"):
                for itm in absent_list: st.markdown(f'<div class="info-card" style="border-left-color:red; background-color:#fff5f5;">❌ {itm}</div>', unsafe_allow_html=True)

        # --- பாடவாரி விரிவான பகுப்பாய்வு ---
        st.markdown('<div class="responsive-subtitle">📈 பாடவாரி விரிவான பகுப்பாய்வு</div>', unsafe_allow_html=True)
        sub_df_list = []
        for sn in g_list:
            stt = subject_stats[sn]
            t_f, t_m = stt['total']['F'], stt['total']['M']
            a_f, a_m = stt['app']['F'], stt['app']['M']
            p_f, p_m = stt['pass']['F'], stt['pass']['M']
            f_f, f_m = stt['fail']['F'], stt['fail']['M']
            
            def fmt_gt(f, m): return f"{f+m} ({f}F|{m}M)" if split_gender else str(f+m)

            sub_df_list.append({
                "Subject": sn, "Total": fmt_gt(t_f, t_m), "App": fmt_gt(a_f, a_m), "Pass": fmt_gt(p_f, p_m),
                "Fail": fmt_gt(f_f, f_m), "Pass%": f"{round((p_f+p_m)/(a_f+a_m)*100,1) if (a_f+a_m)>0 else 0}%",
                "Min": min(stt["marks"]) if stt["marks"] else 0, "Max": max(stt["marks"]) if stt["marks"] else 0, "Only This": stt["only_this"]
            })
        st.table(pd.DataFrame(sub_df_list))

        # --- முழுமையான மதிப்பெண் பட்டியல் ---
        st.markdown('<div class="responsive-subtitle">📋 முழுமையான மதிப்பெண் பட்டியல்</div>', unsafe_allow_html=True)
        show_det = st.toggle("🔍 மதிப்பீட்டு விவரங்களைக் காட்டு (T+P+I / T+I)", value=True)
        
        df_sorted = pd.DataFrame(report_rows).sort_values(by=["Fails", "மொத்தம்"], ascending=[True, False]).reset_index(drop=True)
        df_sorted["Rank"] = "-"
        df_sorted["Rank"] = df_sorted["Rank"].astype(object)
        
        rank_val = 1
        for idx, row in df_sorted.iterrows():
            if int(row["Fails"]) == 0:
                df_sorted.at[idx, "Rank"] = rank_val
                rank_val += 1
        
        final_disp = []
        for _, r in df_sorted.iterrows():
            d_row = {"Rank": r["Rank"], "தேர்வு எண்": r["தேர்வு எண்"], "பெயர்": r['பெயர்'], "மொத்தம்": r['மொத்தம்'], "Fails": r['Fails'], "தோல்வி விவரம்": r['தோல்வி விவரம்']}
            for sn in g_list:
                v = r.get(sn)
                if isinstance(v, dict):
                    d_row[sn] = f"{v['tot']}\n{v['tag']}" if show_det else v['tot']
                else:
                    d_row[sn] = v
            final_disp.append(d_row)
        
        df_disp = pd.DataFrame(final_disp)
        
        def highlight_cells(val):
            s = str(val)
            if 'ABS' in s or (isinstance(val, (int, float)) and 0 < val < 35): return 'color: red'
            if '\n' in s:
                try:
                    score = int(s.split('\n')[0])
                    if score < 35: return 'color: red'
                except: pass
            if 'EXEMPTED' in s: return 'color: blue'
            return ''

        st.dataframe(df_disp.style.map(highlight_cells), use_container_width=True, hide_index=True)
    else:
        st.warning("தேர்வுத் தரவுகள் கிடைக்கவில்லை.")
