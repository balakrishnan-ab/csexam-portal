import streamlit as st
import pandas as pd
from supabase import create_client

# --- Supabase இணைப்பு ---
def get_supabase_client():
    if "supabase_instance" not in st.session_state:
        st.session_state.supabase_instance = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
    return st.session_state.supabase_instance

supabase = get_supabase_client()

st.set_page_config(page_title="Advanced School Analysis", layout="wide")

# ⚡ CSS வடிவமைப்பு
st.markdown("""
    <style>
    .stDataFrame td { font-weight: bold !important; font-size: 15px !important; }
    .main-stat { background-color: #f8fafc; border: 1px solid #e2e8f0; padding: 15px; border-radius: 10px; text-align: center; }
    .stat-val { font-size: 24px; font-weight: bold; color: #1e293b; }
    .centum-card { background-color: #fef3c7; border: 1px solid #f59e0b; padding: 8px; border-radius: 8px; text-align: center; margin-bottom: 5px; }
    .fail-box { background-color: #fff1f2; border-left: 4px solid #e11d48; padding: 8px; margin-bottom: 5px; border-radius: 4px; font-size: 14px; }
    .absent-box { background-color: #f1f5f9; border-left: 4px solid #64748b; padding: 8px; margin-bottom: 5px; border-radius: 4px; font-size: 14px; }
    </style>
    """, unsafe_allow_html=True)

st.title("📊 பள்ளித் தேர்ச்சி மற்றும் வருகைப் பகுப்பாய்வு")

# --- தரவுகள் பெறுதல் ---
exams_data = supabase.table("exams").select("*").execute().data
classes_data = supabase.table("classes").select("*").execute().data
groups_data = supabase.table("groups").select("*").execute().data
subjects_data = supabase.table("subjects").select("*").execute().data

c1, c2 = st.columns(2)
sel_exam_name = c1.selectbox("1. தேர்வு:", [e['exam_name'] for e in exams_data])
all_classes_raw = [c.get('class_n') or c.get('class_name') for c in classes_data]
base_classes = sorted(list(set([str(c).split('-')[0].strip() for c in all_classes_raw if c])), key=lambda x: int(x) if x.isdigit() else x)
sel_base_class = c2.selectbox("2. வகுப்பு (அனைத்துப் பிரிவுகளும்):", ["-- தேர்வு செய்க --"] + base_classes)

if sel_exam_name and sel_base_class != "-- தேர்வு செய்க --":
    exam_id = next(e['id'] for e in exams_data if e['exam_name'] == sel_exam_name)
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
                
                studs = supabase.table("exam_mapping").select("exam_no, student_name, emis_no").eq("exam_id", exam_id).eq("class_name", section).execute().data
                if studs:
                    for s in studs:
                        s['section'] = section
                        all_students.append(s)

    marks_data = supabase.table("marks").select("*").eq("exam_id", exam_id).execute().data
    relevant_subjects = [s for s in subjects_data if s['subject_name'] in union_subs]

    if all_students:
        report_rows = []
        centum_winners = []
        full_absents = []
        present_count = 0
        pass_count = 0

        for s in all_students:
            row = {"பிரிவு": s['section'], "பெயர்": s['student_name']}
            total = 0
            fails = 0
            fail_subs = []
            wrote_atleast_one = False
            
            for sub in relevant_subjects:
                m = next((m for m in marks_data if m['emis_no'] == s['emis_no'] and m['subject_id'] == sub['subject_code']), None)
                if m:
                    if not m.get('is_absent'):
                        wrote_atleast_one = True
                        val = m.get('total_mark', 0)
                        total += val
                        if val < 35: 
                            fails += 1; fail_subs.append(sub['subject_name'])
                        if val == 100:
                            centum_winners.append({"பெயர்": s['student_name'], "பாடம்": sub['subject_name'], "பிரிவு": s['section']})
                    else:
                        val = "ABS"; fails += 1; fail_subs.append(sub['subject_name'])
                    row[sub['subject_name']] = val
                else:
                    row[sub['subject_name']] = "-"

            if wrote_atleast_one: 
                present_count += 1
                if fails == 0: pass_count += 1
            else:
                full_absents.append({"பெயர்": s['student_name'], "பிரிவு": s['section']})

            row["மொத்தம்"] = total
            row["Fails"] = fails
            row["தோல்வி விவரம்"] = f"({', '.join(fail_subs)})" if fail_subs else ""
            report_rows.append(row)

        df = pd.DataFrame(report_rows)
        
        # ⚡ 1. ஒட்டுமொத்தப் புள்ளிவிவரங்கள்
        st.subheader(f"📌 {sel_base_class}-ஆம் வகுப்பு ஒட்டுமொத்த நிலை")
        m1, m2, m3, m4, m5 = st.columns(5)
        m1.markdown(f'<div class="main-stat"><div class="stat-label">மொத்த மாணவர்கள்</div><div class="stat-val">{len(all_students)}</div></div>', unsafe_allow_html=True)
        m2.markdown(f'<div class="main-stat"><div class="stat-label">தேர்வு எழுதியவர்</div><div class="stat-val">{present_count}</div></div>', unsafe_allow_html=True)
        m3.markdown(f'<div class="main-stat"><div class="stat-label">தேர்ச்சி</div><div class="stat-val">{pass_count}</div></div>', unsafe_allow_html=True)
        m4.markdown(f'<div class="main-stat"><div class="stat-label">தேர்ச்சி பெறாதவர்</div><div class="stat-val">{present_count - pass_count}</div></div>', unsafe_allow_html=True)
        p_per = round((pass_count/present_count)*100, 1) if present_count > 0 else 0
        m5.markdown(f'<div class="main-stat"><div class="stat-label">தேர்ச்சி சதவீதம்</div><div class="stat-val" style="color:#16a34a">{p_per}%</div></div>', unsafe_allow_html=True)

        # ⚡ 2. 100/100 எடுத்தவர்கள் & வராதவர்கள்
        c_left, c_right = st.columns(2)
        with c_left:
            st.subheader("🏆 100/100 எடுத்தவர்கள்")
            if centum_winners:
                for cw in centum_winners:
                    st.markdown(f'<div class="centum-card">🥇 <b>{cw["பெயர்"]}</b> ({cw["பிரிவு"]}) - {cw["பாடம்"]}</div>', unsafe_allow_html=True)
            else: st.write("யாரும் இல்லை")
        
        with c_right:
            st.subheader("🚶 தேர்வுக்கே வராதவர்கள் (Full Absent)")
            if full_absents:
                for fa in full_absents:
                    st.markdown(f'<div class="absent-box">❌ <b>{fa["பெயர்"]}</b> ({fa["பிரிவு"]})</div>', unsafe_allow_html=True)
            else: st.write("அனைவரும் வந்துள்ளனர்")

        # ⚡ 3. பாடவாரி பகுப்பாய்வு
        st.divider()
        st.subheader("📈 பாடவாரி விரிவான பகுப்பாய்வு (Subject-wise)")
        subj_stats = []
        for sub in relevant_subjects:
            s_col = sub['subject_name']
            if s_col in df.columns:
                v = pd.to_numeric(df[s_col], errors='coerce').dropna()
                if not v.empty:
                    p_in_sub = len(v)
                    pass_in_sub = len(v[v >= 35])
                    subj_stats.append({
                        "பாடம்": s_col, "எழுதியவர்": p_in_sub, "தேர்ச்சி": pass_in_sub,
                        "தோல்வி": p_in_sub - pass_in_sub,
                        "தேர்ச்சி %": f"{round((pass_in_sub/p_in_sub)*100, 1)}%",
                        "அதிகபட்சம்": int(v.max()), "குறைந்தபட்சம்": int(v.min()), "சராசரி": round(v.mean(), 1)
                    })
        st.table(pd.DataFrame(subj_stats))

        # ⚡ 4. தோல்வி அடைந்தவர்கள் விவரம்
        st.divider()
        st.subheader("❌ தோல்வி அடைந்தவர்கள் (எந்தெந்தப் பாடங்கள்?)")
        f_cols = st.columns(2)
        # 1 பாடம் முதல் அனைத்துப் பாடங்கள் வரை (6 வரை)
        for i in range(1, len(relevant_subjects) + 1):
            fail_list = df[df["Fails"] == i][["பெயர்", "பிரிவு", "தோல்வி விவரம்"]]
            if not fail_list.empty:
                with f_cols[(i-1)%2].expander(f"📌 {i} பாடத்தில் தோல்வி ({len(fail_list)} பேர்)"):
                    for _, r in fail_list.iterrows():
                        st.markdown(f'<div class="fail-box"><b>{r["பெயர்"]}</b> ({r["பிரிவு"]}) <br> <span style="color:#e11d48">{r["தோல்வி விவரம்"]}</span></div>', unsafe_allow_html=True)

        # ⚡ 5. முழுப் பட்டியல்
        st.divider()
        st.subheader("📋 முழுமையான மதிப்பெண் பட்டியல்")
        df = df.sort_values(by=["Fails", "மொத்தம்"], ascending=[True, False]).reset_index(drop=True)
        ranks = []
        r_val = 1
        for idx, row in df.iterrows():
            if row["Fails"] == 0 and row["மொத்தம்"] > 0:
                ranks.append(str(r_val)); r_val += 1
            else: ranks.append("-")
        df.insert(0, "Rank", ranks)
        st.dataframe(df.style.map(lambda v: 'color: red' if v == "ABS" or (isinstance(v, int) and v < 35) else '').set_properties(**{'background-color': '#f8fafc'}, subset=['மொத்தம்']), use_container_width=True)

        csv = df.to_csv(index=False).encode('utf-8-sig')
        st.download_button("📥 எக்செல் பதிவிறக்கம்", data=csv, file_name=f"{sel_base_class}_Full_Report.csv")
