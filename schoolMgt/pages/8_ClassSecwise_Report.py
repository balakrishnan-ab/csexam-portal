import streamlit as st
import pandas as pd
from supabase import create_client

# --- Supabase இணைப்பு ---
def get_supabase_client():
    if "supabase_instance" not in st.session_state:
        st.session_state.supabase_instance = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
    return st.session_state.supabase_instance

supabase = get_supabase_client()

st.set_page_config(page_title="Final Result Analysis", layout="wide")

# ⚡ CSS வடிவமைப்பு
st.markdown("""
    <style>
    .stDataFrame td { font-weight: bold !important; font-size: 14px !important; white-space: pre !important; }
    .main-stat { background-color: #f8fafc; border: 1px solid #e2e8f0; padding: 15px; border-radius: 10px; text-align: center; }
    .stat-val { font-size: 22px; font-weight: bold; color: #1e293b; }
    .stat-label { font-size: 13px; color: #64748b; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

st.title("📊 வகுப்பு வாரி விரிவான தேர்ச்சிப் பகுப்பாய்வு")

# --- தரவுகள் பெறுதல் ---
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
    class_info = next((c for c in classes_data if (c.get('class_n') == sel_class or c.get('class_name') == sel_class)), None)
    
    relevant_subjects = []
    if class_info:
        g_info = next((g for g in groups_data if g['group_name'] == class_info.get('group_name')), None)
        if g_info and g_info.get('subjects'):
            g_subs = [s.strip() for s in g_info['subjects'].split(',')]
            relevant_subjects = [s for s in subjects_data if s['subject_name'] in g_subs]

    students = supabase.table("exam_mapping").select("exam_no, student_name, emis_no").eq("exam_id", exam_id).eq("class_name", sel_class).order("exam_no").execute().data
    marks_data = supabase.table("marks").select("*").eq("exam_id", exam_id).execute().data

    if students and relevant_subjects:
        report_rows = []
        centum_winners = []
        full_absents = []
        present_count = 0
        pass_count = 0

        # --- ⚡ 1. ஒவ்வொரு மாணவருக்கும் தேர்ச்சி நிலையைத் தீர்மானித்தல் ---
        for s in students:
            row_raw = {"பெயர்": s['student_name'], "emis_no": s['emis_no'], "exam_no": s['exam_no']}
            total = 0; fails = 0; fail_subs = []
            wrote_any = False
            
            for sub in relevant_subjects:
                m = next((m for m in marks_data if m['emis_no'] == s['emis_no'] and m['subject_id'] == sub['subject_code']), None)
                if m:
                    if not m.get('is_absent'):
                        wrote_any = True
                        tot, th, in_m, pr = m.get('total_mark',0), m.get('theory_mark',0), m.get('internal_mark',0), m.get('practical_mark',0)
                        
                        # ✅ கட்டாயத் தேர்ச்சி விதி (Theory >= 15 & Practical >= 15 & Total >= 35)
                        is_pass = True
                        if sub.get('has_practical'):
                            if th < 15 or pr < 15 or tot < 35: is_pass = False
                        else:
                            if tot < 35: is_pass = False
                        
                        total += tot
                        if not is_pass:
                            fails += 1; fail_subs.append(sub['subject_name'])
                        
                        # தற்காலிக சேமிப்பு
                        row_raw[sub['subject_name']] = {"tot": tot, "th": th, "in": in_m, "pr": pr, "prac": sub.get('has_practical'), "pass": is_pass}
                        if tot == 100: centum_winners.append(f"{s['student_name']} - {sub['subject_name']}")
                    else:
                        row_raw[sub['subject_name']] = "ABS"
                        fails += 1; fail_subs.append(sub['subject_name'])
                else:
                    row_raw[sub['subject_name']] = "-"

            if wrote_any:
                present_count += 1
                if fails == 0: pass_count += 1
            else:
                full_absents.append(s['student_name'])
            
            row_raw["Present"] = wrote_any
            row_raw["மொத்தம்"] = total
            row_raw["Fails"] = fails
            row_raw["தோல்வி விவரம்"] = f"({', '.join(fail_subs)})" if fail_subs else ""
            report_rows.append(row_raw)

        # --- 📊 2. Dashboard & Expanders ---
        st.subheader(f"📌 {sel_class} ஒட்டுமொத்தப் புள்ளிவிவரம்")
        m1, m2, m3, m4, m5 = st.columns(5)
        m1.markdown(f'<div class="main-stat"><div class="stat-label">மொத்தம்</div><div class="stat-val">{len(students)}</div></div>', unsafe_allow_html=True)
        m2.markdown(f'<div class="main-stat"><div class="stat-label">எழுதியவர்</div><div class="stat-val">{present_count}</div></div>', unsafe_allow_html=True)
        m3.markdown(f'<div class="main-stat"><div class="stat-label">தேர்ச்சி</div><div class="stat-val">{pass_count}</div></div>', unsafe_allow_html=True)
        m4.markdown(f'<div class="main-stat"><div class="stat-label">தோல்வி</div><div class="stat-val">{present_count - pass_count}</div></div>', unsafe_allow_html=True)
        p_per = round((pass_count/present_count)*100, 1) if present_count > 0 else 0
        m5.markdown(f'<div class="main-stat"><div class="stat-label">தேர்ச்சி %</div><div class="stat-val" style="color:#16a34a">{p_per}%</div></div>', unsafe_allow_html=True)

        st.divider()
        e1, e2 = st.columns(2)
        with e1:
            with st.expander(f"🏆 100/100 எடுத்தவர்கள்: {len(centum_winners)} பேர்"):
                for cw in centum_winners: st.info(cw)
        with e2:
            with st.expander(f"🚶 தேர்வுக்கே வராதவர்கள்: {len(full_absents)} பேர்"):
                for fa in full_absents: st.error(fa)

        # --- 📈 3. பாடவாரி பகுப்பாய்வு ---
        st.subheader("📈 பாடவாரி விரிவான பகுப்பாய்வு")
        subj_stats = []
        for sub in relevant_subjects:
            s_name = sub['subject_name']
            s_marks = [r[s_name]['tot'] for r in report_rows if isinstance(r.get(s_name), dict)]
            s_pass_cnt = sum(1 for r in report_rows if isinstance(r.get(s_name), dict) and r[s_name]['pass'])
            if s_marks:
                v = pd.Series(s_marks)
                subj_stats.append({
                    "பாடம்": s_name, "எழுதியவர்": len(v), "தேர்ச்சி": s_pass_cnt, "தோல்வி": len(v)-s_pass_cnt,
                    "தேர்ச்சி %": f"{round((s_pass_cnt/len(v))*100,1)}%", "சராசரி": round(v.mean(),1),
                    "அதிகபட்சம்": int(v.max()), "குறைந்தபட்சம்": int(v.min())
                })
        st.table(pd.DataFrame(subj_stats))

        # --- 📋 4. முழுமையான மதிப்பெண் பட்டியல் ---
        st.divider()
        st.subheader("📋 முழுமையான மதிப்பெண் பட்டியல்")
        show_breakup = st.toggle("🔍 அகமதிப்பீடு மற்றும் செய்முறை மதிப்பெண்களைக் காட்டு (Theory/Internal/Practical)")

        final_rows = []
        for r in report_rows:
            d_row = {"பெயர்": r['பெயர்'], "மொத்தம்": r['மொத்தம்'], "Fails": r['Fails'], "தோல்வி விவரம்": r['தோல்வி விவரம்'], "Present": r['Present']}
            for sub in relevant_subjects:
                val = r.get(sub['subject_name'])
                if isinstance(val, dict):
                    if show_breakup:
                        breakup = f"{val['tot']}\n({val['th']}+{val['in']}+{val['pr']})" if val['prac'] else f"{val['tot']}\n({val['th']}+{val['in']})"
                        d_row[sub['subject_name']] = breakup
                    else:
                        d_row[sub['subject_name']] = val['tot']
                else:
                    d_row[sub['subject_name']] = val
            final_rows.append(d_row)

        df_final = pd.DataFrame(final_rows).sort_values(by=["Fails", "மொத்தம்"], ascending=[True, False]).reset_index(drop=True)
        
        # ⚡ Smart Rank: Fails > 0 இருந்தால் கண்டிப்பாக Rank வராது
        ranks = []; r_val = 1
        for idx, row in df_final.iterrows():
            if int(row["Fails"]) == 0 and row["Present"]:
                ranks.append(str(r_val)); r_val += 1
            else:
                ranks.append("-")
        df_final.insert(0, "Rank", ranks)

        # ⚡ Styling Logic (சிவப்பு நிறம் காட்டுவதற்கு)
        def highlight_fail_cells(row):
            styles = ['' for _ in row.index]
            for i, col in enumerate(row.index):
                if col in [s['subject_name'] for s in relevant_subjects]:
                    val = row[col]
                    if val == "ABS": styles[i] = 'color: red'
                    elif isinstance(val, str) and '\n' in val:
                        p = val.split('\n')[1].strip('()').split('+')
                        th, pr = int(p[0]), (int(p[2]) if len(p)>2 else 35)
                        tot = int(val.split('\n')[0])
                        if th < 15 or pr < 15 or tot < 35: styles[i] = 'color: red'
                    elif isinstance(val, (int, float)) and val < 35:
                        styles[i] = 'color: red'
            return styles

        cols_to_show = ["Rank", "பெயர்"] + [s['subject_name'] for s in relevant_subjects] + ["மொத்தம்", "தோல்வி விவரம்"]
        st.dataframe(df_final[cols_to_show].style.apply(highlight_fail_cells, axis=1)
                     .set_properties(**{'background-color': '#f8fafc'}, subset=['மொத்தம்']), use_container_width=True, hide_index=True)
