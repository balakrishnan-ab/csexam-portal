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

# CSS ஸ்டைலிங்
st.markdown("""
    <style>
    .stDataFrame td { font-weight: bold !important; font-size: 13px !important; white-space: pre !important; }
    .metric-container { display: flex; flex-wrap: wrap; gap: 10px; justify-content: space-between; width: 100%; margin-bottom: 20px; }
    .metric-card { background-color: #f8fafc; border: 1px solid #e2e8f0; padding: 12px 8px; border-radius: 10px; text-align: center; flex: 1 1 calc(15% - 10px); min-width: 110px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    .stat-val { font-size: 22px; font-weight: bold; color: #1e293b; }
    .stat-label { font-size: 12px; color: #64748b; font-weight: bold; }
    .responsive-subtitle { font-size: 20px; font-weight: bold; color: #334155; border-bottom: 2px solid #e2e8f0; margin: 15px 0; }
    .info-card { padding: 10px; border-radius: 6px; margin-bottom: 8px; border-left: 4px solid #10b981; background-color: #f0fdf4; font-size: 14px; }
    </style>
    """, unsafe_allow_html=True)

st.title("📊 விரிவான தேர்ச்சிப் பகுப்பாய்வு")

# --- 1. விலக்கு அளிக்கப்பட்ட மாணவர்கள் (EMIS எண்கள் & பாடங்கள்) ---
# உங்கள் பள்ளியில் உள்ள மாற்றுத்திறனாளி மாணவர்களின் EMIS மற்றும் பாடங்களை இங்கே சேர்க்கவும்
EXEMPTED_STUDENTS = {
    "3322110099": ["Tamil", "English"], 
    "3322110088": ["Tamil"]
}

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
        report_rows = []
        # Total, App, Pass, Fail, Pass%, Max, Avg, Only This
        subject_stats = {sn: {"total": 0, "app": 0, "pass": 0, "fail": 0, "marks": [], "only_this": 0} for sn in union_subs}
        st_count = {"total": 0, "present": 0, "pass": 0}

        for s in all_students:
            st_count["total"] += 1
            emis = str(s['emis_no'])
            exempt_subs = EXEMPTED_STUDENTS.get(emis, []) 
            
            row_raw = {"தேர்வு எண்": s.get('exam_no', '-'), "பிரிவு": s['section'], "பெயர்": s['student_name']}
            total_m, fails, wrote_any, fail_subs = 0, 0, False, []
            
            for sn in union_subs:
                if sn not in s['my_subjects']:
                    row_raw[sn] = "-"; continue
                
                subject_stats[sn]["total"] += 1 # பாடத்தை எடுத்தவர்கள் அனைவரும் இதில் வருவர்
                
                # மாற்றுத்திறனாளி மாணவர் - விலக்கு அளிக்கப்பட்ட பாடம்
                if sn in exempt_subs:
                    row_raw[sn] = "EXEMPTED"
                    # குறிப்பு: இங்கே 'app' அல்லது 'pass' எண்ணிக்கையில் இவர் சேர்க்கப்படமாட்டார்
                    continue

                s_obj = sub_info_map.get(sn)
                m = next((m for m in marks_data if m['emis_no'] == s['emis_no'] and m['subject_id'] == s_obj['subject_code']), None) if s_obj else None
                
                if m and not m.get('is_absent'):
                    wrote_any = True
                    tot = m.get('total_mark', 0)
                    eval_type = str(s_obj.get('eval_type', '90+10'))
                    
                    is_subj_pass = True
                    if '70' in eval_type: # Practicals பாடங்கள்
                        if m.get('theory_mark', 0) < 15 or m.get('practical_mark', 0) < 15 or tot < 35: is_subj_pass = False
                    else:
                        if tot < 35: is_subj_pass = False
                    
                    subject_stats[sn]["app"] += 1
                    subject_stats[sn]["marks"].append(tot)
                    if is_subj_pass: 
                        subject_stats[sn]["pass"] += 1
                    else: 
                        subject_stats[sn]["fail"] += 1; fails += 1; fail_subs.append(sn)
                    
                    total_m += tot
                    row_raw[sn] = tot
                else:
                    row_raw[sn] = "ABS"
                    fails += 1; fail_subs.append(sn)
                    subject_stats[sn]["app"] += 1; subject_stats[sn]["fail"] += 1

            if wrote_any:
                st_count["present"] += 1
                if fails == 0: st_count["pass"] += 1
                if fails == 1: subject_stats[fail_subs[0]]["only_this"] += 1

            row_raw.update({"மொத்தம்": total_m, "Fails": fails, "தோல்வி விவரம்": f"({', '.join(fail_subs)})" if fail_subs else ""})
            report_rows.append(row_raw)

        # --- 📈 பாடவாரி விரிவான பகுப்பாய்வு அட்டவணை ---
        st.markdown('<div class="responsive-subtitle">📈 பாடவாரி விரிவான பகுப்பாய்வு</div>', unsafe_allow_html=True)
        sub_analysis = []
        for sn in union_subs:
            stt = subject_stats[sn]
            pp = round((stt["pass"]/stt["app"])*100,1) if stt["app"]>0 else 0
            sub_analysis.append({
                "Subject": sn,
                "Total": stt["total"],
                "App": stt["app"],
                "Pass": stt["pass"],
                "Fail": stt["fail"],
                "Pass%": f"{pp}%",
                "Max": max(stt["marks"]) if stt["marks"] else 0,
                "Avg": round(sum(stt["marks"])/len(stt["marks"]),1) if stt["marks"] else 0,
                "Only This": stt["only_this"]
            })
        st.table(pd.DataFrame(sub_analysis))

        # --- 📋 முழுமையான பட்டியல் ---
        st.divider()
        df_final = pd.DataFrame(report_rows).sort_values(by=["Fails", "மொத்தம்"], ascending=[True, False]).reset_index(drop=True)
        
        df_final["Rank"] = "-"
        rank_v = 1
        for idx, r in df_final.iterrows():
            if r["Fails"] == 0:
                df_final.at[idx, "Rank"] = rank_v; rank_v += 1
        
        cols = ["Rank", "தேர்வு எண்", "பெயர்", "பிரிவு", "மொத்தம்", "Fails"] + union_subs
        
        # Color Styling Logic
        def highlight_status(val):
            if val == 'ABS': return 'color: red'
            if val == 'EXEMPTED': return 'color: blue'
            if isinstance(val, int) and val < 35 and val > 0: return 'color: red'
            return ''

        st.dataframe(df_final[cols].style.applymap(highlight_status), use_container_width=True, hide_index=True)
