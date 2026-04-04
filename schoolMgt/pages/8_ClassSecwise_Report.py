import streamlit as st
import pandas as pd
from supabase import create_client

# --- Supabase இணைப்பு ---
def get_supabase_client():
    if "supabase_instance" not in st.session_state:
        st.session_state.supabase_instance = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
    return st.session_state.supabase_instance

supabase = get_supabase_client()

st.set_page_config(page_title="Section-wise Analysis", layout="wide")

# ⚡ CSS - அட்டவணை மற்றும் கார்டுகளை சீரமைக்க
st.markdown("""
    <style>
    .stDataFrame td { font-weight: bold !important; font-size: 14px !important; white-space: pre !important; }
    .main-stat { background-color: #f8fafc; border: 1px solid #e2e8f0; padding: 15px; border-radius: 10px; text-align: center; }
    .stat-val { font-size: 22px; font-weight: bold; color: #1e293b; }
    .stat-label { font-size: 13px; color: #64748b; font-weight: bold; }
    .info-card { background-color: #f1f5f9; padding: 8px; border-radius: 5px; margin-bottom: 5px; border-left: 4px solid #3b82f6; font-size: 13px; }
    </style>
    """, unsafe_allow_html=True)

st.title("📊 வகுப்பு வாரி விரிவான தேர்ச்சிப் பகுப்பாய்வு")

# --- 1. தரவுகள் பெறுதல் ---
exams_data = supabase.table("exams").select("*").execute().data
classes_data = supabase.table("classes").select("*").execute().data
groups_data = supabase.table("groups").select("*").execute().data
subjects_data = supabase.table("subjects").select("*").execute().data

c1, c2 = st.columns(2)
sel_exam_name = c1.selectbox("1. தேர்வு:", [e['exam_name'] for e in exams_data])
class_list = sorted(list(set([c.get('class_n') or c.get('class_name') for c in classes_data])))
sel_class = c2.selectbox("2. வகுப்பு:", ["-- தேர்வு செய்க --"] + class_list)

 # 🔍 Toggle Switch - மதிப்பெண் விரிவாகக் காட்ட
st.divider()
show_breakup = st.toggle("🔍 அகமதிப்பீடு மற்றும் செய்முறை மதிப்பெண்களைக் காட்டு (Theory/Internal/Practical)")

if sel_exam_name and sel_class != "-- தேர்வு செய்க --":
    exam_id = next(e['id'] for e in exams_data if e['exam_name'] == sel_exam_name)
    
    # பாடப்பிரிவு தகவல்
    class_info = next((c for c in classes_data if (c.get('class_n') == sel_class or c.get('class_name') == sel_class)), None)
    relevant_subjects = []
    if class_info:
        g_info = next((g for g in groups_data if g['group_name'] == class_info.get('group_name')), None)
        if g_info and g_info.get('subjects'):
            g_subs = [s.strip() for s in g_info['subjects'].split(',')]
            relevant_subjects = [s for s in subjects_data if s['subject_name'] in g_subs]

    # மாணவர்கள் மற்றும் மதிப்பெண்கள்
    students = supabase.table("exam_mapping").select("exam_no, student_name, emis_no").eq("exam_id", exam_id).eq("class_name", sel_class).order("exam_no").execute().data
    marks_data = supabase.table("marks").select("*").eq("exam_id", exam_id).execute().data

    if students and relevant_subjects:
        report_rows = []
        centum_winners = []
        full_absents = []
        present_count = 0
        pass_count = 0

        for s in students:
            row = {"பெயர்": s['student_name']}
            total = 0; fails = 0; fail_subs = []
            wrote_any = False
            
            for sub in relevant_subjects:
                s_name, s_code = sub['subject_name'], sub['subject_code']
                m = next((m for m in marks_data if m['emis_no'] == s['emis_no'] and m['subject_id'] == s_code), None)
                
                if m:
                    if not m.get('is_absent'):
                        wrote_any = True
                        tot = m.get('total_mark', 0)
                        total += tot
                        if tot < 35: fails += 1; fail_subs.append(s_name)
                        if tot == 100: centum_winners.append(f"{s['student_name']} - {s_name}")
                        
                        # Detailed Marks Logic
                        if show_breakup:
                            th, inter, prac = m.get('theory_mark', 0), m.get('internal_mark', 0), m.get('practical_mark', 0)
                            if sub.get('has_practical'):
                                row[s_name] = f"{tot}\n({th}+{inter}+{prac})"
                            else:
                                row[s_name] = f"{tot}\n({th}+{inter})"
                        else:
                            row[s_name] = tot
                    else:
                        row[s_name] = "ABS"; fails += 1; fail_subs.append(s_name)
                else:
                    row[s_name] = "-"

            if wrote_any:
                present_count += 1
                if fails == 0: pass_count += 1
            else:
                full_absents.append(s['student_name'])

            row["Present"] = wrote_any
            row["மொத்தம்"] = total
            row["Fails"] = fails
            row["தோல்வி விவரம்"] = f"({', '.join(fail_subs)})" if fail_subs else ""
            report_rows.append(row)

        df = pd.DataFrame(report_rows)

        # ⚡ 1. Dashboard
        st.subheader(f"📌 {sel_class} ஒட்டுமொத்தப் புள்ளிவிவரம்")
        m1, m2, m3, m4, m5 = st.columns(5)
        m1.markdown(f'<div class="main-stat"><div class="stat-label">மொத்தம்</div><div class="stat-val">{len(students)}</div></div>', unsafe_allow_html=True)
        m2.markdown(f'<div class="main-stat"><div class="stat-label">எழுதியவர்</div><div class="stat-val">{present_count}</div></div>', unsafe_allow_html=True)
        m3.markdown(f'<div class="main-stat"><div class="stat-label">தேர்ச்சி</div><div class="stat-val">{pass_count}</div></div>', unsafe_allow_html=True)
        m4.markdown(f'<div class="main-stat"><div class="stat-label">தோல்வி</div><div class="stat-val">{present_count - pass_count}</div></div>', unsafe_allow_html=True)
        p_per = round((pass_count/present_count)*100, 1) if present_count > 0 else 0
        m5.markdown(f'<div class="main-stat"><div class="stat-label">தேர்ச்சி %</div><div class="stat-val" style="color:#16a34a">{p_per}%</div></div>', unsafe_allow_html=True)

        # ⚡ 2. Expanders (100/100 & Absents)
        st.markdown("---")
        e1, e2 = st.columns(2)
        with e1:
            with st.expander(f"🏆 100/100 எடுத்தவர்கள்: {len(centum_winners)} பேர்"):
                for cw in centum_winners: st.markdown(f'<div class="info-card">🥇 {cw}</div>', unsafe_allow_html=True)
        with e2:
            with st.expander(f"🚶 தேர்வுக்கே வராதவர்கள்: {len(full_absents)} பேர்"):
                for fa in full_absents: st.markdown(f'<div class="info-card">❌ {fa}</div>', unsafe_allow_html=True)

        # ⚡ 3. பாடவாரி பகுப்பாய்வு
        st.divider()
        st.subheader("📈 பாடவாரி விரிவான பகுப்பாய்வு")
        subj_stats = []
        for sub in relevant_subjects:
            s_col = sub['subject_name']
            if s_col in df.columns:
                # எண்களை மட்டும் பிரித்தெடுத்தல் (Detailed marks இருந்தால்)
                v = pd.to_numeric(df[s_col].apply(lambda x: str(x).split('\n')[0]), errors='coerce').dropna()
                if not v.empty:
                    app = len(v); pas = len(v[v >= 35])
                    subj_stats.append({
                        "பாடம்": s_col, "எழுதியவர்": app, "தேர்ச்சி": pas, "தோல்வி": app-pas,
                        "தேர்ச்சி %": f"{round((pas/app)*100,1)}%", "சராசரி": round(v.mean(),1),
                        "அதிகபட்சம்": int(v.max()), "குறைந்தபட்சம்": int(v.min())
                    })
        st.table(pd.DataFrame(subj_stats))

        # ⚡ 4. முழுமையான மதிப்பெண் பட்டியல் (Smart Rank)
       
        st.divider()
        st.subheader("📋 முழுமையான மதிப்பெண் பட்டியல்")
        df_final = df.sort_values(by=["Fails", "மொத்தம்"], ascending=[True, False]).reset_index(drop=True)
        
        ranks = []; r_val = 1
        for idx, row in df_final.iterrows():
            if row["Fails"] == 0 and row["Present"]:
                ranks.append(str(r_val)); r_val += 1
            else:
                ranks.append("-")
        df_final.insert(0, "Rank", ranks)

        # காண்பிக்க வேண்டிய நெடுவரிசைகள்
        cols_to_show = ["Rank", "பெயர்"] + [s['subject_name'] for s in relevant_subjects] + ["மொத்தம்", "தோல்வி விவரம்"]
        
        st.dataframe(
            df_final[cols_to_show].style.map(lambda v: 'color: red' if "ABS" in str(v) or (isinstance(v, int) and v < 35) else '')
            .set_properties(**{'background-color': '#f8fafc'}, subset=['மொத்தம்']), 
            use_container_width=True, hide_index=True
        )

        csv = df_final.to_csv(index=False).encode('utf-8-sig')
        st.download_button("📥 எக்செல் பதிவிறக்கம்", data=csv, file_name=f"{sel_class}_Report.csv")
