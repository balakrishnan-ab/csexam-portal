import streamlit as st
import pandas as pd
from supabase import create_client

# --- Supabase இணைப்பு ---
def get_supabase_client():
    if "supabase_instance" not in st.session_state:
        st.session_state.supabase_instance = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
    return st.session_state.supabase_instance

supabase = get_supabase_client()

st.set_page_config(page_title="Detailed School Analysis", layout="wide")

# ⚡ டிசைன் ஸ்டைலிங் (CSS)
st.markdown("""
    <style>
    .stDataFrame td { font-weight: bold !important; font-size: 15px !important; }
    .main-stat { background-color: #f8fafc; border: 1px solid #e2e8f0; padding: 20px; border-radius: 12px; text-align: center; }
    .stat-val { font-size: 24px; font-weight: bold; color: #1e293b; }
    .stat-label { font-size: 14px; color: #64748b; }
    .fail-box { background-color: #fff1f2; border-left: 4px solid #e11d48; padding: 10px; margin-bottom: 5px; border-radius: 4px; }
    </style>
    """, unsafe_allow_html=True)

st.title("📊 ஒருங்கிணைந்த விரிவான தேர்ச்சிப் பகுப்பாய்வு")

# --- 1. தரவுகள் பெறுதல் ---
exams_data = supabase.table("exams").select("*").execute().data
classes_data = supabase.table("classes").select("*").execute().data
groups_data = supabase.table("groups").select("*").execute().data
subjects_data = supabase.table("subjects").select("*").execute().data

# --- 2. வடிகட்டிகள் ---
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
        pass_count = 0
        present_count = 0

        for s in all_students:
            row = {"பிரிவு": s['section'], "பெயர்": s['student_name']}
            total = 0
            fails = 0
            fail_subs = []
            is_absent_all = True
            
            for sub in relevant_subjects:
                m = next((m for m in marks_data if m['emis_no'] == s['emis_no'] and m['subject_id'] == sub['subject_code']), None)
                if m:
                    val = m.get('total_mark', 0)
                    if not m.get('is_absent'):
                        is_absent_all = False
                        total += val
                        if val < 35: 
                            fails += 1; fail_subs.append(sub['subject_name'])
                    else:
                        val = "ABS"; fails += 1; fail_subs.append(sub['subject_name'])
                    row[sub['subject_name']] = val
                else:
                    row[sub['subject_name']] = "-"

            if not is_absent_all: present_count += 1
            row["மொத்தம்"] = total
            row["Fails"] = fails
            row["தோல்வி விவரம்"] = f"({', '.join(fail_subs)})" if fail_subs else ""
            if fails == 0: pass_count += 1
            report_rows.append(row)

        df = pd.DataFrame(report_rows)
        df = df.sort_values(by=["Fails", "மொத்தம்"], ascending=[True, False]).reset_index(drop=True)
        
        # ⚡ 3. ஒட்டுமொத்தப் புள்ளிவிவரங்கள் (Dashboard)
        st.subheader(f"📌 {sel_base_class}-ஆம் வகுப்பு ஒட்டுமொத்தப் புள்ளிவிவரம்")
        m1, m2, m3, m4, m5 = st.columns(5)
        m1.markdown(f'<div class="main-stat"><div class="stat-label">மொத்த மாணவர்கள்</div><div class="stat-val">{len(all_students)}</div></div>', unsafe_allow_html=True)
        m2.markdown(f'<div class="main-stat"><div class="stat-label">தேர்வு எழுதியவர்</div><div class="stat-val">{present_count}</div></div>', unsafe_allow_html=True)
        m3.markdown(f'<div class="main-stat"><div class="stat-label">தேர்ச்சி</div><div class="stat-val">{pass_count}</div></div>', unsafe_allow_html=True)
        m4.markdown(f'<div class="main-stat"><div class="stat-label">தேர்ச்சி பெறாதவர்</div><div class="stat-val">{present_count - pass_count}</div></div>', unsafe_allow_html=True)
        pass_per = round((pass_count/present_count)*100,1) if present_count > 0 else 0
        m5.markdown(f'<div class="main-stat"><div class="stat-label">தேர்ச்சி சதவீதம்</div><div class="stat-val" style="color:#16a34a">{pass_per}%</div></div>', unsafe_allow_html=True)

        # ⚡ 4. பாடவாரி புள்ளிவிவரங்கள்
        st.divider()
        st.subheader("📈 பாடவாரி பகுப்பாய்வு (Subject-wise Stats)")
        subj_stats = []
        for sub in relevant_subjects:
            s_col = sub['subject_name']
            if s_col in df.columns:
                v = pd.to_numeric(df[s_col], errors='coerce').dropna()
                if not v.empty:
                    subj_stats.append({
                        "பாடம்": s_col, "சராசரி": round(v.mean(), 1), "அதிகபட்சம்": int(v.max()),
                        "குறைந்தபட்சம்": int(v.min()), "தேர்ச்சி பெறாதவர்": len(v[v < 35])
                    })
        st.table(pd.DataFrame(subj_stats))

        # ⚡ 5. தோல்வி அடைந்தவர்கள் - பெயரும் பாடமும்
        st.divider()
        st.subheader("❌ தோல்வி அடைந்தவர்கள் விவரம்")
        f_cols = st.columns(2)
        for i in range(1, len(relevant_subjects) + 1):
            fail_list = df[df["Fails"] == i][["பெயர்", "பிரிவு", "தோல்வி விவரம்"]]
            if not fail_list.empty:
                with f_cols[(i-1)%2].expander(f"🚩 {i} பாடத்தில் தோல்வி ({len(fail_list)} பேர்)"):
                    for _, r in fail_list.iterrows():
                        st.markdown(f'<div class="fail-box"><b>{r["பெயர்"]}</b> ({r["பிரிவு"]}) <br> <small style="color:#be123c">{r["தோல்வி விவரம்"]}</small></div>', unsafe_allow_html=True)

        # ⚡ 6. முதன்மை அட்டவணை (Rank உடன்)
        st.divider()
        st.subheader("📋 முழுமையான மதிப்பெண் பட்டியல்")
        ranks = []
        r_val = 1
        for idx, row in df.iterrows():
            if row["Fails"] == 0: ranks.append(str(r_val)); r_val += 1
            else: ranks.append("-")
        df.insert(0, "Rank", ranks)
        st.dataframe(df.style.map(lambda v: 'color: red' if v == "ABS" or (isinstance(v, int) and v < 35) else '').set_properties(**{'background-color': '#f8fafc'}, subset=['மொத்தம்']), use_container_width=True)

        # Download
        csv = df.to_csv(index=False).encode('utf-8-sig')
        st.download_button("📥 அறிக்கையை பதிவிறக்கவும்", data=csv, file_name=f"{sel_base_class}_Overall_Analysis.csv")
