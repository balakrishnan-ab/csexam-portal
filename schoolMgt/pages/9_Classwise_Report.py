import streamlit as st
import pandas as pd
from supabase import create_client
from io import BytesIO

# --- பக்க அமைப்பு ---
st.set_page_config(page_title="Evaluation Analysis", layout="wide")

# --- Supabase இணைப்பு ---
def get_supabase_client():
    if "supabase_instance" not in st.session_state:
        st.session_state.supabase_instance = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
    return st.session_state.supabase_instance

supabase = get_supabase_client()

# --- CSS ஸ்டைலிங் (Dashboard & Cards) ---
st.markdown("""
    <style>
    .metric-container { display: flex; flex-wrap: wrap; gap: 10px; justify-content: space-between; width: 100%; margin-bottom: 20px; }
    .metric-card { background-color: #f8fafc; border: 1px solid #e2e8f0; padding: 12px 8px; border-radius: 10px; text-align: center; flex: 1 1 calc(15% - 10px); min-width: 110px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    .stat-val { font-size: 24px; font-weight: bold; color: #1e293b; }
    .stat-label { font-size: 12px; color: #64748b; font-weight: bold; text-transform: uppercase; }
    .info-card { padding: 10px; border-radius: 6px; margin-bottom: 8px; border-left: 4px solid #10b981; background-color: #f0fdf4; font-size: 14px; font-weight: 500; }
    .responsive-subtitle { font-size: 22px; font-weight: bold; color: #334155; border-bottom: 2px solid #e2e8f0; margin: 15px 0; }
    </style>
    """, unsafe_allow_html=True)

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
    st.markdown(f'<div class="responsive-subtitle">📊 {sel_base_class}-ஆம் வகுப்பு ஒட்டுமொத்தப் புள்ளிவிவரம்</div>', unsafe_allow_html=True)

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
        st_count = {"total": 0, "present": 0, "pass": 0}
        subject_stats = {sn: {"total": 0, "app": 0, "pass": 0, "fail": 0, "marks": [], "only_this": 0} for sn in union_subs}
        fail_cats = {1: [], 2: [], 3: [], 4: [], 5: [], "All": []}

        for s in all_students:
            st_count["total"] += 1
            row_raw = {"தேர்வு எண்": s.get('exam_no', '-'), "பிரிவு": s['section'], "பெயர்": s['student_name']}
            total_m, fails, wrote_any, fail_subs, student_centums = 0, 0, False, [], []
            
            for sn in union_subs:
                if sn not in s['my_subjects']:
                    row_raw[sn] = "-"; continue
                
                subject_stats[sn]["total"] += 1
                s_obj = sub_info_map.get(sn)
                m = next((m for m in marks_data if m['emis_no'] == s['emis_no'] and m['subject_id'] == s_obj['subject_code']), None) if s_obj else None
                
                if m:
                    # null/None எனில் EXEMPTED லாஜிக்
                    is_abs = m.get('is_absent')
                    
                    if is_abs is None:
                        row_raw[sn] = "EXEMPTED"
                        continue

                    if not is_abs:
                        wrote_any = True
                        tot = m.get('total_mark', 0)
                        eval_type = str(s_obj.get('eval_type', '90+10'))
                        
                        is_subj_pass = True
                        if '70' in eval_type:
                            if m.get('theory_mark', 0) < 15 or m.get('practical_mark', 0) < 15 or tot < 35: is_subj_pass = False
                        else:
                            if tot < 35: is_subj_pass = False
                        
                        subject_stats[sn]["app"] += 1
                        subject_stats[sn]["marks"].append(tot)
                        if is_subj_pass: 
                            subject_stats[sn]["pass"] += 1
                            if tot == 100: student_centums.append(sn)
                        else: 
                            subject_stats[sn]["fail"] += 1; fails += 1; fail_subs.append(sn)
                        total_m += tot
                        row_raw[sn] = tot
                    else:
                        row_raw[sn] = "ABS"; fails += 1; fail_subs.append(sn)
                        subject_stats[sn]["app"] += 1; subject_stats[sn]["fail"] += 1
                else:
                    # மதிப்பெண் பதியப்படவில்லையெனில் (Database-ல் row இல்லை எனில்)
                    row_raw[sn] = "-"

            if wrote_any:
                st_count["present"] += 1
                if fails == 0: st_count["pass"] += 1
                if fails == 1: subject_stats[fail_subs[0]]["only_this"] += 1
                if student_centums: centum_list.append(f"{s['student_name']} ({s['section']} - {', '.join(student_centums)})")
                
                txt = f"{s['student_name']} ({s['section']} - {', '.join(fail_subs)})"
                if fails >= len(s['my_subjects']): fail_cats["All"].append(txt)
                elif fails in [1,2,3,4,5]: fail_cats[fails].append(txt)
            else:
                # அனைத்துப் பாடங்களும் ABS அல்லது row இல்லையெனில்
                if any(row_raw.get(sub) == "ABS" for sub in union_subs):
                    absent_list.append(f"{s['student_name']} ({s['section']})")

            row_raw.update({"மொத்தம்": total_m, "Fails": fails, "தோல்வி விவரம்": f"({', '.join(fail_subs)})" if fail_subs else ""})
            report_rows.append(row_raw)

        # --- Dashboard Metrics ---
        p_count = st_count["present"]
        fail_count = p_count - st_count["pass"]
        pass_pc = round((st_count["pass"]/p_count)*100, 1) if p_count > 0 else 0
        avg_v = round(sum([r['மொத்தம்'] for r in report_rows if r['மொத்தம்'] > 0])/p_count, 1) if p_count > 0 else 0

        st.markdown(f"""
            <div class="metric-container">
                <div class="metric-card"><div class="stat-label">TOTAL</div><div class="stat-val">{st_count['total']}</div></div>
                <div class="metric-card"><div class="stat-label">PRESENT</div><div class="stat-val">{p_count}</div></div>
                <div class="metric-card"><div class="stat-label">PASS</div><div class="stat-val" style="color:green">{st_count['pass']}</div></div>
                <div class="metric-card"><div class="stat-label">FAIL</div><div class="stat-val" style="color:red">{fail_count}</div></div>
                <div class="metric-card"><div class="stat-label">PASS %</div><div class="stat-val" style="color:green">{pass_pc}%</div></div>
                <div class="metric-card"><div class="stat-label">AVG</div><div class="stat-val" style="color:blue">{avg_v}</div></div>
            </div>
        """, unsafe_allow_html=True)

        st.divider()
        c_e1, c_e2 = st.columns(2)
        with c_e1:
            with st.expander(f"🏆 100/100 எடுத்தவர்கள்: {len(centum_list)} பேர்"):
                for itm in centum_list: st.markdown(f'<div class="info-card">🥇 {itm}</div>', unsafe_allow_html=True)
        with c_e2:
            with st.expander(f"🚶 தேர்வு எழுதாதவர்கள்: {len(absent_list)} பேர்"):
                for itm in absent_list: st.markdown(f'<div class="info-card" style="border-left-color:red; background-color:#fff5f5;">❌ {itm}</div>', unsafe_allow_html=True)

        # --- பாடவாரி விரிவான பகுப்பாய்வு ---
        st.markdown('<div class="responsive-subtitle">📈 பாடவாரி விரிவான பகுப்பாய்வு</div>', unsafe_allow_html=True)
        sub_analysis = []
        for sn in union_subs:
            stt = subject_stats[sn]
            sub_analysis.append({
                "Subject": sn, 
                "Total": stt["total"], 
                "App": stt["app"], 
                "Pass": stt["pass"], 
                "Fail": stt["fail"], 
                "Pass%": f"{round((stt['pass']/stt['app'])*100,1) if stt['app']>0 else 0}%", 
                "Max": max(stt["marks"]) if stt["marks"] else 0, 
                "Avg": round(sum(stt["marks"])/len(stt["marks"]),1) if stt["marks"] else 0, 
                "Only This": stt["only_this"]
            })
        st.table(pd.DataFrame(sub_analysis))

        # --- முழுமையான மதிப்பெண் பட்டியல் ---
        st.markdown('<div class="responsive-subtitle">📋 முழுமையான மதிப்பெண் பட்டியல்</div>', unsafe_allow_html=True)
        df_final = pd.DataFrame(report_rows).sort_values(by=["Fails", "மொத்தம்"], ascending=[True, False]).reset_index(drop=True)
        
        # Rank Column Setup & Fixing TypeError
        df_final["Rank"] = "-"
        df_final["Rank"] = df_final["Rank"].astype(object)
        
        rv = 1
        for idx, row in df_final.iterrows():
            if int(row["Fails"]) == 0:
                df_final.at[idx, "Rank"] = rv; rv += 1
        
        cols = ["Rank", "தேர்வு எண்", "பெயர்", "பிரிவு", "மொத்தம்", "Fails"] + union_subs

        # Styling Logic (AttributeError தவிர்க்க map பயன்படுத்துகிறோம்)
        def highlight_status(val):
            if val == 'ABS': return 'color: red'
            if val == 'EXEMPTED': return 'color: blue'
            if isinstance(val, (int, float)) and val < 35 and val > 0: return 'color: red'
            return ''

        st.dataframe(df_final[cols].style.map(highlight_status), use_container_width=True, hide_index=True)

        # --- விரிவான தோல்விப் பட்டியல் ---
        st.divider()
        st.markdown('<div class="responsive-subtitle">📉 தோல்வி அடைந்த மாணவர்களின் விரிவான விவரம்</div>', unsafe_allow_html=True)
        f_col1, f_col2 = st.columns(2)
        with f_col1:
            for n in [1, 2, 3]:
                if fail_cats[n]:
                    with st.expander(f"❌ {n} பாடத்தில் தோல்வி: {len(fail_cats[n])} பேர்"):
                        for itm in fail_cats[n]: st.markdown(f'<div class="info-card" style="border-left-color:orange; background-color:#fffaf0;">⚠️ {itm}</div>', unsafe_allow_html=True)
        with f_col2:
            for n in [4, 5, "All"]:
                if fail_cats[n]:
                    lbl = f"{n} பாடத்தில் தோல்வி" if n != "All" else "அனைத்துப் பாடங்களிலும் தோல்வி"
                    with st.expander(f"🔴 {lbl}: {len(fail_cats[n])} பேர்"):
                        for itm in fail_cats[n]: st.markdown(f'<div class="info-card" style="border-left-color:red; background-color:#fff5f5;">🚩 {itm}</div>', unsafe_allow_html=True)
