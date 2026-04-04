import streamlit as st
import pandas as pd
from supabase import create_client

# --- Supabase இணைப்பு ---
def get_supabase_client():
    if "supabase_instance" not in st.session_state:
        st.session_state.supabase_instance = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
    return st.session_state.supabase_instance

supabase = get_supabase_client()

st.set_page_config(page_title="Result Analysis (6-12)", layout="wide")

# ⚡ வடிவமைப்பை அழகாக்க CSS
st.markdown("""
    <style>
    .stDataFrame td { font-weight: bold !important; font-size: 15px !important; }
    .stat-card { background-color: #f0fdf4; border-left: 5px solid #22c55e; padding: 15px; border-radius: 8px; font-size: 18px; font-weight: bold; }
    .centum-card { background-color: #fef3c7; border: 1px solid #f59e0b; padding: 10px; border-radius: 8px; text-align: center; }
    .fail-list-text { color: #dc2626; font-size: 13px; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

st.title("📂 பள்ளி அளவிலான தேர்ச்சிப் பகுப்பாய்வு (6 - 12)")

# --- 1. அடிப்படைத் தரவுகள் ---
exams_data = supabase.table("exams").select("*").execute().data
classes_data = supabase.table("classes").select("*").execute().data
groups_data = supabase.table("groups").select("*").execute().data
subjects_data = supabase.table("subjects").select("*").execute().data

# --- 2. வடிகட்டிகள் ---
c1, c2 = st.columns(2)
sel_exam_name = c1.selectbox("1. தேர்வைத் தேர்ந்தெடுக்கவும்:", [e['exam_name'] for e in exams_data])

# அனைத்து வகுப்புகளையும் (6, 7, 8... 12) வரிசைப்படுத்துதல்
class_list = sorted(list(set([c.get('class_n') or c.get('class_name') for c in classes_data])))
sel_class = c2.selectbox("2. வகுப்பு & பிரிவைத் தேர்ந்தெடுக்கவும்:", ["-- தேர்வு செய்க --"] + class_list)

if sel_exam_name and sel_class != "-- தேர்வு செய்க --":
    exam_id = next(e['id'] for e in exams_data if e['exam_name'] == sel_exam_name)
    
    # ⚡ அந்த வகுப்பிற்குரிய பாடப்பிரிவு மற்றும் பாடங்களை எடுத்தல்
    class_info = next((c for c in classes_data if (c.get('class_n') == sel_class or c.get('class_name') == sel_class)), None)
    relevant_subjects = []
    
    if class_info:
        g_name = class_info.get('group_name')
        group_info = next((g for g in groups_data if g['group_name'] == g_name), None)
        if group_info and group_info.get('subjects'):
            g_subs = [s.strip() for s in group_info['subjects'].split(',')]
            relevant_subjects = [s for s in subjects_data if s['subject_name'] in g_subs]

    # மாணவர்கள் மற்றும் மதிப்பெண்கள் தரவு
    students = supabase.table("exam_mapping").select("exam_no, student_name, emis_no").eq("exam_id", exam_id).eq("class_name", sel_class).order("exam_no").execute().data
    marks_data = supabase.table("marks").select("*").eq("exam_id", exam_id).execute().data

    if students and relevant_subjects:
        report_rows = []
        centum_list = []
        pass_count = 0

        for s in students:
            row = {"Rank": "-", "பெயர்": s['student_name']}
            total_score = 0
            fails = 0
            fail_subs_names = []
            
            for sub in relevant_subjects:
                s_name, s_code = sub['subject_name'], sub['subject_code']
                m = next((m for m in marks_data if m['emis_no'] == s['emis_no'] and m['subject_id'] == s_code), None)
                
                if m:
                    val = m.get('total_mark', 0)
                    if not m.get('is_absent'):
                        total_score += val
                        if val < 35: 
                            fails += 1; fail_subs_names.append(s_name)
                        if val == 100: 
                            centum_list.append({"பெயர்": s['student_name'], "பாடம்": s_name})
                    else:
                        val = "ABS"; fails += 1; fail_subs_names.append(s_name)
                    row[s_name] = val
                else:
                    row[s_name] = "-"
            
            row["மொத்தம்"] = total_score
            row["Fails"] = fails
            row["தோல்வி பாடங்கள்"] = ", ".join(fail_subs_names)
            if fails == 0: pass_count += 1
            report_rows.append(row)

        df = pd.DataFrame(report_rows)
        # ⚡ தரம் பிரித்தல் (தோல்வி இல்லாதவர்களுக்கு மட்டும்)
        df = df.sort_values(by=["Fails", "மொத்தம்"], ascending=[True, False]).reset_index(drop=True)
        
        # Rank கணக்கிடுதல்
        pass_df = df[df["Fails"] == 0].copy()
        pass_df["Rank"] = range(1, len(pass_df) + 1)
        df.update(pass_df)

        # ⚡ 100/100 எடுத்தவர்கள்
        if centum_list:
            st.subheader("🌟 100/100 எடுத்த சாதனையாளர்கள்")
            c_cols = st.columns(min(len(centum_list), 4))
            for idx, c in enumerate(centum_list):
                c_cols[idx % 4].markdown(f'<div class="centum-card">🏆 {c["பெயர்"]}<br><small>{c["பாடம்"]}</small></div>', unsafe_allow_html=True)

        # ⚡ முதன்மை அட்டவணை
        st.divider()
        st.subheader(f"📝 {sel_class} - {sel_exam_name} விரிவான பட்டியல்")
        st.dataframe(df.style.map(lambda v: 'color: red' if v == "ABS" or (isinstance(v, int) and v < 35) else '').set_properties(**{'background-color': '#f8fafc'}, subset=['மொத்தம்']), use_container_width=True)

        # ⚡ தேர்ச்சி மற்றும் சராசரி
        st.divider()
        c_avg = round(df["மொத்தம்"].mean(), 1) if not df.empty else 0
        p_per = round((pass_count / len(students)) * 100, 1)
        
        ca, cb = st.columns(2)
        ca.markdown(f'<div class="stat-card">🏫 வகுப்பு சராசரி மதிப்பெண்: {c_avg}</div>', unsafe_allow_html=True)
        cb.markdown(f'<div class="stat-card">🎓 தேர்ச்சி விழுக்காடு: {p_per}% ({pass_count}/{len(students)})</div>', unsafe_allow_html=True)

        # ⚡ பாடவாரி புள்ளிவிவரங்கள்
        st.subheader("📈 பாடவாரி பகுப்பாய்வு (Max/Min/Avg)")
        stats_list = []
        for sub in relevant_subjects:
            s_col = sub['subject_name']
            if s_col in df.columns:
                v = pd.to_numeric(df[s_col], errors='coerce').dropna()
                if not v.empty:
                    stats_list.append({
                        "பாடம்": s_col, "சராசரி": round(v.mean(), 1) if not v.empty else 0,
                        "அதிகபட்சம்": int(v.max()) if not v.empty else 0, "குறைந்தபட்சம்": int(v.min()) if not v.empty else 0,
                        "தோல்வி": len(v[v < 35])
                    })
        st.table(pd.DataFrame(stats_list))

        # ⚡ தோல்விப் பட்டியல் (எந்தப் பாடம் என்பதுடன்)
        st.divider()
        st.subheader("❌ தோல்வி விவரம் & பாடங்கள்")
        f_cols = st.columns(2)
        for i in range(1, len(relevant_subjects) + 1):
            f_data = df[df["Fails"] == i][["பெயர்", "தோல்வி பாடங்கள்"]]
            if not f_data.empty:
                with f_cols[(i-1)%2].expander(f"📌 {i} பாடத்தில் தோல்வி ({len(f_data)} பேர்)"):
                    for _, r in f_data.iterrows():
                        st.markdown(f"**• {r['பெயர்']}**")
                        st.markdown(f'<div class="fail-list-item">தோற்ற பாடங்கள்: {r["தோல்வி பாடங்கள்"]}</div>', unsafe_allow_html=True)

        # எக்செல் தரவிறக்கம்
        csv = df.to_csv(index=False).encode('utf-8-sig')
        st.download_button("📥 முழு அறிக்கையை எக்செல் கோப்பாக பதிவிறக்கு", data=csv, file_name=f"{sel_class}_Full_Report.csv")
