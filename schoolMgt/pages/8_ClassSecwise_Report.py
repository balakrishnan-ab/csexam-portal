import streamlit as st
import pandas as pd
from supabase import create_client
from utils import add_school_header 

# --- பக்க அமைப்பு (config முதலில் இருக்க வேண்டும்) ---
st.set_page_config(page_title="Section-wise Analysis", layout="wide")

# பள்ளியின் பொதுவான தலைப்பை utils.py-லிருந்து அழைத்தல்
add_school_header()

# --- Supabase இணைப்பு ---
def get_supabase_client():
    if "supabase_instance" not in st.session_state:
        st.session_state.supabase_instance = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
    return st.session_state.supabase_instance

supabase = get_supabase_client()

# ⚡ CSS - Responsive ஸ்டைலிங்
st.markdown("""
    <style>
    /* டேபிள் ஸ்டைல் */
    .stDataFrame td { font-weight: bold !important; font-size: 13px !important; white-space: pre !important; }
    
    /* 📱 1. புள்ளிவிவரக் கட்டங்களுக்கான (Metric Cards) Responsive ஸ்டைல் */
    .metric-container {
        display: flex;
        flex-wrap: wrap;
        gap: 10px;
        justify-content: space-between;
        width: 100%;
        margin-bottom: 20px;
    }
    .metric-card {
        background-color: #f8fafc;
        border: 1px solid #e2e8f0;
        padding: 12px 8px;
        border-radius: 10px;
        text-align: center;
        flex: 1 1 calc(15% - 10px); 
        min-width: 110px; 
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .stat-val { font-size: clamp(18px, 3vw, 24px); font-weight: bold; color: #1e293b; line-height: 1.2; }
    .stat-label { font-size: 12px; color: #64748b; font-weight: bold; margin-bottom: 4px; text-transform: uppercase; }
    .gender-sub { font-size: 11px; color: #3b82f6; font-weight: bold; display: block; margin-top: 2px; }

    /* 📱 2. தலைப்புகளுக்கான Responsive ஸ்டைல் */
    .responsive-header {
        font-size: clamp(20px, 4.5vw, 30px);
        font-weight: bold;
        color: #1e293b;
        text-align: left;
        padding: 10px 0;
        line-height: 1.4;
    }
    .responsive-subtitle {
        font-size: clamp(16px, 3.5vw, 22px);
        font-weight: bold;
        color: #334155;
        text-align: left;
        padding: 8px 0;
        border-bottom: 2px solid #e2e8f0;
        margin: 15px 0 10px 0;
    }

    /* தகவல் கார்டுகள் (Centum/Absent) */
    .info-card { padding: 10px; border-radius: 6px; margin-bottom: 8px; border-left: 4px solid #10b981; background-color: #f0fdf4; font-size: 14px; font-weight: bold; }

    @media (max-width: 600px) {
        .metric-card { flex: 1 1 calc(45% - 10px); } /* மொபைலில் ஒரு வரிசைக்கு 2 கட்டங்கள் */
    }
    </style>
    """, unsafe_allow_html=True)

st.markdown('<div class="responsive-header">📌 வகுப்பு & பிரிவு வாரி விரிவான தேர்ச்சிப் பகுப்பாய்வு</div>', unsafe_allow_html=True)

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
    st.divider()
    split_gender = st.toggle("🔍 ஆண் பெண் பிரித்து காட்டு", value=True)

    studs = supabase.table("exam_mapping").select("exam_no, student_name, emis_no, gender").eq("exam_id", exam_id).eq("class_name", sel_section).execute().data
    c_info = next((c for c in classes_data if (c.get('class_n') == sel_section or c.get('class_name') == sel_section)), None)
    
    if studs and c_info:
        g_info = next((g for g in groups_data if g['group_name'] == c_info.get('group_name')), None)
        g_list = [s.strip() for s in g_info['subjects'].split(',')] if g_info else []
        
        marks_data = supabase.table("marks").select("*").eq("exam_id", exam_id).execute().data
        sub_info_map = {s['subject_name']: s for s in subjects_data}

        report_rows, centum_list, absent_list = [], [], []
        st_count = {"total": {"A": 0, "M": 0, "F": 0}, "present": {"A": 0, "M": 0, "F": 0}, "pass": {"A": 0, "M": 0, "F": 0}}
        all_marks_list = {"A": [], "M": [], "F": []}
        fail_cats = {1: [], 2: [], 3: [], 4: [], 5: [], "All": []}
        subject_stats = {sn: {"app": 0, "pass": 0, "fail": 0, "marks": [], "only_this": 0} for sn in g_list}

        for s in studs:
            raw_gen = str(s.get('gender', 'Male')).strip().upper()
            gen = 'F' if raw_gen.startswith('F') else 'M'
            st_count["total"]["A"] += 1; st_count["total"][gen] += 1
            
            row_raw = {"தேர்வு எண்": s.get('exam_no', '-'), "பெயர்": s['student_name'], "gender": gen}
            total_m, fails, wrote_any, fail_subs, student_centums = 0, 0, False, [], []

            for sn in g_list:
                s_obj = sub_info_map.get(sn)
                if not s_obj: continue
                
                m = next((m for m in marks_data if m['emis_no'] == s['emis_no'] and m['subject_id'] == s_obj['subject_code']), None)
                if m and not m.get('is_absent'):
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
                    
                    subject_stats[sn]["app"] += 1
                    subject_stats[sn]["marks"].append(tot)
                    if is_subj_pass: subject_stats[sn]["pass"] += 1
                    else: 
                        subject_stats[sn]["fail"] += 1; fails += 1; fail_subs.append(sn)
                    
                    total_m += tot
                    if tot == 100: student_centums.append(sn)
                    row_raw[sn] = {"tot": tot, "tag": tag, "pass": is_subj_pass}
                else:
                    row_raw[sn] = "ABS"; fails += 1; fail_subs.append(sn)
                    subject_stats[sn]["app"] += 1; subject_stats[sn]["fail"] += 1

            if student_centums:
                centum_list.append(f"{s['student_name']} ({', '.join(student_centums)})")

            if wrote_any:
                st_count["present"]["A"] += 1; st_count["present"][gen] += 1
                all_marks_list["A"].append(total_m); all_marks_list[gen].append(total_m)
                if fails == 0:
                    st_count["pass"]["A"] += 1; st_count["pass"][gen] += 1
                else:
                    txt = f"{s['student_name']} - ({', '.join(fail_subs)})"
                    if fails == 1: subject_stats[fail_subs[0]]["only_this"] += 1
                    if fails >= len(g_list): fail_cats["All"].append(txt)
                    elif fails in [1,2,3,4,5]: fail_cats[fails].append(txt)
            else: 
                absent_list.append(s['student_name'])

            row_raw.update({"மொத்தம்": total_m, "Fails": fails, "தோல்வி விவரம்": f"({', '.join(fail_subs)})" if fail_subs else ""})
            report_rows.append(row_raw)

        # --- 📱 Dashboard (Metric Cards) ---
        st.markdown(f'<div class="responsive-subtitle">📊 {sel_section} பிரிவு ஒட்டுமொத்தப் புள்ளிவிவரம்</div>', unsafe_allow_html=True)
        
        f_a = st_count["present"]["A"] - st_count["pass"]["A"]
        p_a = round((st_count["pass"]["A"]/st_count["present"]["A"])*100, 1) if st_count["present"]["A"]>0 else 0
        avg_v = round(sum(all_marks_list["A"])/len(all_marks_list["A"]),1) if all_marks_list["A"] else 0

        def get_gt(k): return f"<span class='gender-sub'>({st_count[k]['F']}F|{st_count[k]['M']}M)</span>" if split_gender else ""
        f_gt = f"<span class='gender-sub'>({st_count['present']['F']-st_count['pass']['F']}F|{st_count['present']['M']-st_count['pass']['M']}M)</span>" if split_gender else ""

        st.markdown(f"""
            <div class="metric-container">
                <div class="metric-card"><div class="stat-label">Total</div><div class="stat-val">{st_count['total']['A']}{get_gt('total')}</div></div>
                <div class="metric-card"><div class="stat-label">Present</div><div class="stat-val">{st_count['present']['A']}{get_gt('present')}</div></div>
                <div class="metric-card"><div class="stat-label">Pass</div><div class="stat-val" style="color:#16a34a">{st_count['pass']['A']}{get_gt('pass')}</div></div>
                <div class="metric-card"><div class="stat-label">Fail</div><div class="stat-val" style="color:#ef4444">{f_a}{f_gt}</div></div>
                <div class="metric-card"><div class="stat-label">Pass %</div><div class="stat-val" style="color:#16a34a">{p_a}%</div></div>
                <div class="metric-card"><div class="stat-label">Avg</div><div class="stat-val" style="color:#3b82f6">{avg_v}</div></div>
            </div>
        """, unsafe_allow_html=True)

        st.divider()
        c_e1, c_e2 = st.columns(2)
        with c_e1:
            with st.expander(f"🏆 100/100 பெற்றவர்கள்: {len(centum_list)} பேர்"):
                for itm in centum_list: st.markdown(f'<div class="info-card">🥇 {itm}</div>', unsafe_allow_html=True)
        with c_e2:
            with st.expander(f"🚶 தேர்வு எழுதாதவர்கள்: {len(absent_list)} பேர்"):
                for itm in absent_list: st.markdown(f'<div class="info-card" style="border-left-color:#ef4444; background-color:#fef2f2;">❌ {itm}</div>', unsafe_allow_html=True)

        # --- பாடவாரி விரிவான பகுப்பாய்வு ---
        st.markdown('<div class="responsive-subtitle">📈 பாடவாரி விரிவான பகுப்பாய்வு</div>', unsafe_allow_html=True)
        sub_df = []
        for sn in g_list:
            stt = subject_stats[sn]; avg_s = round(sum(stt["marks"])/len(stt["marks"]),1) if stt["marks"] else 0
            pp = round((stt["pass"]/stt["app"])*100,1) if stt["app"]>0 else 0
            sub_df.append({"Subject": sn, "App": stt["app"], "Pass": stt["pass"], "Fail": stt["fail"], "Pass%": f"{pp}%", "Max": max(stt["marks"]) if stt["marks"] else 0, "Avg": avg_s, "Only This": stt["only_this"]})
        st.table(pd.DataFrame(sub_df))

        # --- முழுமையான மதிப்பெண் பட்டியல் ---
        st.divider()
        st.markdown('<div class="responsive-subtitle">📋 முழுமையான மதிப்பெண் பட்டியல்</div>', unsafe_allow_html=True)
        show_det = st.toggle("🔍 மதிப்பீட்டு விவரங்களைக் காட்டு (T+P+I / T+I)", value=True)
        
        final_list = []
        for r in report_rows:
            d_row = {"Rank": "-", "தேர்வு எண்": r["தேர்வு எண்"], "பெயர்": r['பெயர்'], "மொத்தம்": r['மொத்தம்'], "Fails": r['Fails'], "தோல்வி விவரம்": r['தோல்வி விவரம்']}
            for sn in g_list:
                v = r.get(sn)
                if isinstance(v, dict): d_row[sn] = f"{v['tot']}\n{v['tag']}" if show_det else v['tot']
                else: d_row[sn] = v
            final_list.append(d_row)
        
        df_f = pd.DataFrame(final_list).sort_values(by=["Fails", "மொத்தம்"], ascending=[True, False]).reset_index(drop=True)
        rv = 1
        for idx, row in df_f.iterrows():
            if int(row["Fails"]) == 0: df_f.at[idx, "Rank"] = str(rv); rv += 1
        
        def highlight_fail(val):
            s = str(val)
            if 'ABS' in s or '-' in s: return 'color: red'
            if '\n' in s:
                try:
                    score = int(s.split('\n')[0])
                    if score < 35: return 'color: red'
                except: pass
            elif isinstance(val, (int, float)) and val < 35: return 'color: red'
            return ''

        st.dataframe(df_f.style.map(highlight_fail), use_container_width=True, hide_index=True)

        # --- விரிவான தோல்விப் பட்டியல் ---
        st.divider()
        st.markdown('<div class="responsive-subtitle">📉 தோல்வி அடைந்த மாணவர்களின் விரிவான விவரம்</div>', unsafe_allow_html=True)
        b1, b2 = st.columns(2)
        with b1:
            for n in [1, 2, 3]:
                if fail_cats[n]:
                    with st.expander(f"❌ {n} பாடத்தில் தோல்வி: {len(fail_cats[n])} பேர்"):
                        for itm in fail_cats[n]: st.markdown(f'<div class="info-card" style="border-left-color:#f59e0b; background-color:#fffbeb;">⚠️ {itm}</div>', unsafe_allow_html=True)
        with b2:
            for n in [4, 5, "All"]:
                if fail_cats[n]:
                    lbl = f"{n} பாடத்தில் தோல்வி" if n != "All" else "அனைத்துப் பாடங்களிலும் தோல்வி"
                    with st.expander(f"🔴 {lbl}: {len(fail_cats[n])} பேர்"):
                        for itm in fail_cats[n]: st.markdown(f'<div class="info-card" style="border-left-color:#ef4444; background-color:#fef2f2;">🚩 {itm}</div>', unsafe_allow_html=True)
    else:
        st.warning("இந்த பிரிவில் மாணவர்கள் யாரும் இல்லை அல்லது தேர்வு தரவுகள் இல்லை.")
