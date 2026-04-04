import streamlit as st
import pandas as pd
from supabase import create_client

# --- Supabase இணைப்பு ---
def get_supabase_client():
    if "supabase_instance" not in st.session_state:
        st.session_state.supabase_instance = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
    return st.session_state.supabase_instance

supabase = get_supabase_client()

st.set_page_config(page_title="Overall Class Analysis", layout="wide")

# ⚡ CSS வடிவமைப்பு
st.markdown("""
    <style>
    .stDataFrame td { font-weight: bold !important; font-size: 15px !important; }
    .stat-card { background-color: #f0fdf4; border-left: 5px solid #22c55e; padding: 15px; border-radius: 8px; font-size: 18px; font-weight: bold; margin-bottom:10px; }
    .centum-card { background-color: #fef3c7; border: 1px solid #f59e0b; padding: 10px; border-radius: 8px; text-align: center; }
    .fail-text { color: #dc2626; font-size: 13px; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

st.title("📂 ஒருங்கிணைந்த வகுப்புத் தேர்ச்சிப் பகுப்பாய்வு (6 - 12)")

# --- 1. தரவுகள் பெறுதல் ---
exams_data = supabase.table("exams").select("*").execute().data
classes_data = supabase.table("classes").select("*").execute().data
groups_data = supabase.table("groups").select("*").execute().data
subjects_data = supabase.table("subjects").select("*").execute().data

# --- 2. வடிகட்டிகள் ---
c1, c2 = st.columns(2)
sel_exam_name = c1.selectbox("1. தேர்வு:", [e['exam_name'] for e in exams_data])

# வகுப்புகளை மட்டும் பிரித்தெடுத்தல் (எ.கா: 11, 12...)
all_classes_raw = [c.get('class_n') or c.get('class_name') for c in classes_data]
base_classes = sorted(list(set([str(c).split('-')[0].strip() for c in all_classes_raw if c])), key=lambda x: int(x) if x.isdigit() else x)

sel_base_class = c2.selectbox("2. வகுப்பைத் தேர்ந்தெடுக்கவும் (எ.கா: 11):", ["-- தேர்வு செய்க --"] + base_classes)

if sel_exam_name and sel_base_class != "-- தேர்வு செய்க --":
    exam_id = next(e['id'] for e in exams_data if e['exam_name'] == sel_exam_name)
    
    # ⚡ அந்த வகுப்பில் உள்ள அனைத்துப் பிரிவுகளையும் கண்டறிதல் (11-A, 11-B, 11-A1...)
    matching_sections = [c for c in all_classes_raw if str(c).startswith(sel_base_class)]
    
    all_students_data = []
    union_subjects_list = []

    # அனைத்துப் பிரிவுகளையும் சுழற்சி முறையில் ஆய்வு செய்தல்
    for section in matching_sections:
        class_info = next((c for c in classes_data if (c.get('class_n') == section or c.get('class_name') == section)), None)
        if class_info:
            g_name = class_info.get('group_name')
            group_info = next((g for g in groups_data if g['group_name'] == g_name), None)
            if group_info and group_info.get('subjects'):
                g_subs = [s.strip() for s in group_info['subjects'].split(',')]
                for gs in g_subs:
                    if gs not in union_subjects_list: union_subjects_list.append(gs)
                
                # மாணவர் பட்டியல்
                sects_studs = supabase.table("exam_mapping").select("exam_no, student_name, emis_no").eq("exam_id", exam_id).eq("class_name", section).execute().data
                if sects_studs:
                    for s in sects_studs:
                        s['section_name'] = section
                        all_students_data.append(s)

    marks_data = supabase.table("marks").select("*").eq("exam_id", exam_id).execute().data
    relevant_subjects = [s for s in subjects_data if s['subject_name'] in union_subjects_list]

    if all_students_data:
        report_rows = []
        centum_list = []
        pass_count = 0

        for s in all_students_data:
            row = {"பிரிவு": s['section_name'], "பெயர்": s['student_name']}
            total_score = 0
            fails = 0
            fail_names = []
            
            for sub in relevant_subjects:
                s_name, s_code = sub['subject_name'], sub['subject_code']
                m = next((m for m in marks_data if m['emis_no'] == s['emis_no'] and m['subject_id'] == s_code), None)
                
                if m:
                    val = m.get('total_mark', 0)
                    if not m.get('is_absent'):
                        total_score += val
                        if val < 35: 
                            fails += 1; fail_names.append(s_name)
                        if val == 100: 
                            centum_list.append({"பெயர்": s['student_name'], "பாடம்": s_name, "பிரிவு": s['section_name']})
                    else:
                        val = "ABS"; fails += 1; fail_names.append(s_name)
                    row[s_name] = val
                else:
                    row[s_name] = "-"
            
            row["மொத்தம்"] = total_score
            row["Fails"] = fails
            row["தோல்வி பாடங்கள்"] = ", ".join(fail_names)
            if fails == 0: pass_count += 1
            report_rows.append(row)

        df = pd.DataFrame(report_rows)
        # ⚡ ஒருங்கிணைந்த தரவரிசை (Fails = 0 மற்றும் அதிக மதிப்பெண் அடிப்படையில்)
        df = df.sort_values(by=["Fails", "மொத்தம்"], ascending=[True, False]).reset_index(drop=True)
        
        # Rank பட்டியல் தயாரித்தல்
        ranks = []
        r_counter = 1
        for idx, row in df.iterrows():
            if row["Fails"] == 0:
                ranks.append(str(r_counter)); r_counter += 1
            else:
                ranks.append("-")
        df.insert(0, "Rank", ranks)

        # ⚡ 100 எடுத்தவர்கள் (Centum)
        if centum_list:
            st.subheader(f"🏆 {sel_base_class}-ஆம் வகுப்பில் 100/100 எடுத்தவர்கள்")
            c_cols = st.columns(min(len(centum_list), 4))
            for idx, c in enumerate(centum_list):
                c_cols[idx%4].markdown(f'<div class="centum-card">⭐ <b>{c["பெயர்"]}</b><br><small>{c["பிரிவு"]} | {c["பாடம்"]}</small></div>', unsafe_allow_html=True)

        # ⚡ அட்டவணை
        st.divider()
        st.subheader(f"📝 {sel_base_class}-ஆம் வகுப்பு ஒருங்கிணைந்த மதிப்பெண் பட்டியல்")
        st.dataframe(df.style.map(lambda v: 'color: red' if v == "ABS" or (isinstance(v, int) and v < 35) else '').set_properties(**{'background-color': '#f8fafc'}, subset=['மொத்தம்']), use_container_width=True)

        # ⚡ ஒட்டுமொத்தப் புள்ளிவிவரங்கள்
        st.divider()
        c_avg = round(df["மொத்தம்"].mean(), 1)
        p_per = round((pass_count / len(all_students_data)) * 100, 1)
        ca, cb = st.columns(2)
        ca.markdown(f'<div class="stat-card">🏫 வகுப்பு சராசரி: {c_avg}</div>', unsafe_allow_html=True)
        cb.markdown(f'<div class="stat-card">🎓 தேர்ச்சி விழுக்காடு: {p_per}% ({pass_count}/{len(all_students_data)})</div>', unsafe_allow_html=True)

        # ⚡ பாடவாரி ஆய்வு
        st.subheader("📈 பாடவாரி பகுப்பாய்வு (அனைத்துப் பிரிவுகளும் சேர்த்து)")
        stats_data = []
        for sub in relevant_subjects:
            s_col = sub['subject_name']
            if s_col in df.columns:
                v = pd.to_numeric(df[s_col], errors='coerce').dropna()
                if not v.empty:
                    stats_data.append({
                        "பாடம்": s_col, "சராசரி": round(v.mean(), 1),
                        "அதிகபட்சம்": int(v.max()), "குறைந்தபட்சம்": int(v.min()),
                        "தோல்வி": len(v[v < 35])
                    })
        st.table(pd.DataFrame(stats_data))

        # ⚡ தோல்வி விவரம்
        st.divider()
        st.subheader("❌ தோல்வி விவரம் & பாடங்கள்")
        f_cols = st.columns(2)
        for i in range(1, len(relevant_subjects) + 1):
            f_list = df[df["Fails"] == i][["பெயர்", "பிரிவு", "தோல்வி பாடங்கள்"]]
            if not f_list.empty:
                with f_cols[(i-1)%2].expander(f"📌 {i} பாடத்தில் தோல்வி ({len(f_list)} பேர்)"):
                    for _, r in f_list.iterrows():
                        st.markdown(f"**• {r['பெயர்']}** ({r['பிரிவு']})")
                        st.markdown(f'<div class="fail-text">தவறிய பாடங்கள்: {r["தோல்வி பாடங்கள்"]}</div>', unsafe_allow_html=True)

        csv = df.to_csv(index=False).encode('utf-8-sig')
        st.download_button("📥 முழு அறிக்கையையும் பதிவிறக்கு", data=csv, file_name=f"{sel_base_class}_Full_Analysis.csv")
