import streamlit as st
import pandas as pd
from supabase import create_client

# --- Supabase இணைப்பு ---
def get_supabase_client():
    if "supabase_instance" not in st.session_state:
        st.session_state.supabase_instance = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
    return st.session_state.supabase_instance

supabase = get_supabase_client()

st.set_page_config(page_title="Detailed Result Analysis", layout="wide")

# ⚡ டிசைனை அழகாக்க CSS
st.markdown("""
    <style>
    .stDataFrame td { font-weight: bold !important; font-size: 16px !important; }
    .centum-card { background-color: #fef3c7; border: 2px solid #f59e0b; padding: 10px; border-radius: 10px; text-align: center; margin-bottom: 10px; }
    .stat-card { background-color: #f0fdf4; border-left: 5px solid #22c55e; padding: 15px; border-radius: 8px; font-size: 20px; font-weight: bold; }
    .fail-detail { color: #dc2626; font-size: 14px; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

st.title("📊 முழுமையான வகுப்பு வாரி தேர்ச்சிப் பகுப்பாய்வு")

# --- 1. தரவுகள் பெறுதல் ---
exams_data = supabase.table("exams").select("*").execute().data
classes_data = supabase.table("classes").select("*").execute().data
groups_data = supabase.table("groups").select("*").execute().data
subjects_data = supabase.table("subjects").select("*").execute().data

c1, c2 = st.columns(2)
sel_exam_name = c1.selectbox("1. தேர்வு:", [e['exam_name'] for e in exams_data])
class_list = sorted(list(set([c.get('class_n') or c.get('class_name') for c in classes_data])))
sel_class = c2.selectbox("2. வகுப்பு:", ["-- தேர்வு செய்க --"] + class_list)

if sel_exam_name and sel_class != "-- தேர்வு செய்க --":
    exam_id = next(e['id'] for e in exams_data if e['exam_name'] == sel_exam_name)
    
    # பாடப்பிரிவு கண்டறிதல்
    class_info = next((c for c in classes_data if (c.get('class_n') == sel_class or c.get('class_name') == sel_class)), None)
    relevant_subjects = []
    if class_info:
        group_info = next((g for g in groups_data if g['group_name'] == class_info.get('group_name')), None)
        if group_info and group_info.get('subjects'):
            g_subs = [s.strip() for s in group_info['subjects'].split(',')]
            relevant_subjects = [s for s in subjects_data if s['subject_name'] in g_subs]

    students = supabase.table("exam_mapping").select("exam_no, student_name, emis_no").eq("exam_id", exam_id).eq("class_name", sel_class).order("exam_no").execute().data
    marks_data = supabase.table("marks").select("*").eq("exam_id", exam_id).execute().data

    if students and relevant_subjects:
        report_rows = []
        centum_winners = [] # 100 எடுத்தவர்கள் பட்டியல்
        pass_count = 0

        for s in students:
            row = {"Rank": 0, "பெயர்": s['student_name']}
            total_score = 0
            fail_subs = []
            
            for sub in relevant_subjects:
                s_name, s_code = sub['subject_name'], sub['subject_code']
                m = next((m for m in marks_data if m['emis_no'] == s['emis_no'] and m['subject_id'] == s_code), None)
                
                if m:
                    tot = m.get('total_mark', 0)
                    if not m.get('is_absent'):
                        total_score += tot
                        if tot < 35: fail_subs.append(s_name)
                        if tot == 100: centum_winners.append({"பெயர்": s['student_name'], "பாடம்": s_name})
                    else:
                        tot = "ABS"; fail_subs.append(s_name)
                    row[s_name] = tot
                else:
                    row[s_name] = "-"
            
            row["மொத்தம்"] = total_score
            row["தோல்வி எண்ணிக்கை"] = len(fail_subs)
            row["தோல்வி விவரம்"] = ", ".join(fail_subs)
            if len(fail_subs) == 0: pass_count += 1
            report_rows.append(row)

        df = pd.DataFrame(report_rows)
        df = df.sort_values(by="மொத்தம்", ascending=False).reset_index(drop=True)
        df["Rank"] = range(1, 1 + len(df))

        # ⚡ 2. செண்டம் எடுத்தவர்கள் (Centum)
        if centum_winners:
            st.subheader("🏆 100/100 எடுத்த மாணவர்கள்")
            cols = st.columns(min(len(centum_winners), 5))
            for idx, c in enumerate(centum_winners):
                cols[idx % 5].markdown(f'<div class="centum-card">🥇 <b>{c["பெயர்"]}</b><br><small>{c["பாடம்"]}</small></div>', unsafe_allow_html=True)

        # ⚡ 3. முதன்மை அட்டவணை
        st.divider()
        st.subheader(f"📝 {sel_class} மதிப்பெண் பட்டியல்")
        st.dataframe(df.style.map(lambda v: 'color: red' if v == "ABS" or (isinstance(v, int) and v < 35) else '').set_properties(**{'background-color': '#f8fafc'}, subset=['மொத்தம்']), use_container_width=True)

        # ⚡ 4. வகுப்பு சராசரி & தேர்ச்சி %
        st.divider()
        col_avg, col_pass = st.columns(2)
        c_avg = round(df["மொத்தம்"].mean(), 1) if not df.empty else 0
        p_per = round((pass_count / len(students)) * 100, 1)
        
        col_avg.markdown(f'<div class="stat-card">🏫 வகுப்பு சராசரி: {c_avg}</div>', unsafe_allow_html=True)
        col_pass.markdown(f'<div class="stat-card">🎓 தேர்ச்சி விழுக்காடு: {p_per}% ({pass_count}/{len(students)})</div>', unsafe_allow_html=True)

        # ⚡ 5. பாடவாரி புள்ளிவிவரங்கள் (Max/Min/Avg)
        st.subheader("📈 பாடவாரி விரிவான பகுப்பாய்வு")
        stats = []
        for sub in relevant_subjects:
            s_col = sub['subject_name']
            if s_col in df.columns:
                v = pd.to_numeric(df[s_col], errors='coerce').dropna()
                stats.append({
                    "பாடம்": s_col, 
                    "சராசரி (Avg)": round(v.mean(), 1) if not v.empty else 0,
                    "அதிகபட்சம் (Max)": int(v.max()) if not v.empty else 0, 
                    "குறைந்தபட்சம் (Min)": int(v.min()) if not v.empty else 0,
                    "தோல்வி எண்ணிக்கை": len(v[v < 35])
                })
        st.table(pd.DataFrame(stats))

        # ⚡ 6. தோல்வி அடைந்தவர்களின் விவரம் (Subject-wise Fail Analysis)
        st.divider()
        st.subheader("❌ தோல்வி அடைந்தவர்களின் பட்டியல் (எந்தப் பாடம்?)")
        f_cols = st.columns(2)
        for i in range(1, len(relevant_subjects) + 1):
            fail_df = df[df["தோல்வி எண்ணிக்கை"] == i][["பெயர்", "தோல்வி விவரம்"]]
            if not fail_df.empty:
                with f_cols[(i-1)%2].expander(f"📌 {i} பாடத்தில் தோல்வி ({len(fail_df)} பேர்)"):
                    for _, r in fail_df.iterrows():
                        st.markdown(f"**• {r['பெயர்']}**")
                        st.markdown(f'<div class="fail-detail">தவறிய பாடங்கள்: {r["தோல்வி விவரம்"]}</div>', unsafe_allow_html=True)

        # Download
        csv = df.to_csv(index=False).encode('utf-8-sig')
        st.download_button("📥 முழு அறிக்கையை பதிவிறக்கு (Excel)", data=csv, file_name=f"{sel_class}_Full_Report.csv")
