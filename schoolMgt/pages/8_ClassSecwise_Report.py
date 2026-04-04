import streamlit as st
import pandas as pd
from supabase import create_client

# --- Supabase இணைப்பு ---
def get_supabase_client():
    if "supabase_instance" not in st.session_state:
        st.session_state.supabase_instance = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
    return st.session_state.supabase_instance

supabase = get_supabase_client()

st.set_page_config(page_title="Refined Section Analysis", layout="wide")

# ⚡ CSS வடிவமைப்பு
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

        # --- ⚡ 1. தரவு தயாரிப்பு மற்றும் தேர்ச்சி சரிபார்ப்பு ---
        for s in students:
            row_data = {"பெயர்": s['student_name'], "emis_no": s['emis_no'], "exam_no": s['exam_no']}
            total = 0; fails = 0; fail_subs = []
            wrote_any = False
            
            for sub in relevant_subjects:
                m = next((m for m in marks_data if m['emis_no'] == s['emis_no'] and m['subject_id'] == sub['subject_code']), None)
                if m:
                    if not m.get('is_absent'):
                        wrote_any = True
                        tot = m.get('total_mark', 0)
                        th = m.get('theory_mark', 0)
                        pr = m.get('practical_mark', 0)
                        
                        # ✅ தேர்ச்சி விதிமுறை (Pass Rule)
                        is_subject_pass = True
                        if sub.get('has_practical'):
                            if th < 15 or pr < 15 or tot < 35: is_subject_pass = False
                        else:
                            if tot < 35: is_subject_pass = False
                        
                        total += tot
                        if not is_subject_pass:
                            fails += 1; fail_subs.append(sub['subject_name'])
                        if tot == 100: centum_winners.append(f"{s['student_name']} - {sub['subject_name']}")
                        
                        # தற்காலிகமாக மதிப்பெண்களைச் சேமிக்க
                        row_data[sub['subject_name']] = {"tot": tot, "th": th, "pr": pr, "in": m.get('internal_mark', 0), "prac_flag": sub.get('has_practical')}
                    else:
                        row_data[sub['subject_name']] = "ABS"
                        fails += 1; fail_subs.append(sub['subject_name'])
                else:
                    row_data[sub['subject_name']] = "-"
            
            if wrote_any:
                present_count += 1
                if fails == 0: pass_count += 1
            else:
                full_absents.append(s['student_name'])
            
            row_data["Present"] = wrote_any
            row_data["மொத்தம்"] = total
            row_data["Fails"] = fails
            row_data["தோல்வி விவரம்"] = f"({', '.join(fail_subs)})" if fail_subs else ""
            report_rows.append(row_data)

        # --- 📊 2. Dashboard ---
        st.subheader(f"📌 {sel_class} ஒட்டுமொத்தப் புள்ளிவிவரம்")
        m1, m2, m3, m4, m5 = st.columns(5)
        m1.markdown(f'<div class="main-stat"><div class="stat-label">மொத்தம்</div><div class="stat-val">{len(students)}</div></div>', unsafe_allow_html=True)
        m2.markdown(f'<div class="main-stat"><div class="stat-label">எழுதியவர்</div><div class="stat-val">{present_count}</div></div>', unsafe_allow_html=True)
        m3.markdown(f'<div class="main-stat"><div class="stat-label">தேர்ச்சி</div><div class="stat-val">{pass_count}</div></div>', unsafe_allow_html=True)
        m4.markdown(f'<div class="main-stat"><div class="stat-label">தோல்வி</div><div class="stat-val">{present_count - pass_count}</div></div>', unsafe_allow_html=True)
        p_per = round((pass_count/present_count)*100, 1) if present_count > 0 else 0
        m5.markdown(f'<div class="main-stat"><div class="stat-label">தேர்ச்சி %</div><div class="stat-val" style="color:#16a34a">{p_per}%</div></div>', unsafe_allow_html=True)

        # --- 🏆 3. Expanders ---
        st.markdown("---")
        e1, e2 = st.columns(2)
        with e1:
            with st.expander(f"🏆 100/100 எடுத்தவர்கள்: {len(centum_winners)} பேர்"):
                for cw in centum_winners: st.markdown(f'<div class="info-card">🥇 {cw}</div>', unsafe_allow_html=True)
        with e2:
            with st.expander(f"🚶 தேர்வுக்கே வராதவர்கள்: {len(full_absents)} பேர்"):
                for fa in full_absents: st.markdown(f'<div class="info-card">❌ {fa}</div>', unsafe_allow_html=True)

        # --- 📈 4. பாடவாரி விரிவான பகுப்பாய்வு ---
        st.divider()
        st.subheader("📈 பாடவாரி விரிவான பகுப்பாய்வு")
        subj_stats = []
        for sub in relevant_subjects:
            s_name = sub['subject_name']
            s_code = sub['subject_code']
            # அந்தப் பாடத்தை எழுதியவர்களின் மதிப்பெண்கள் மட்டும்
            v_marks = []
            p_cnt = 0
            for r in report_rows:
                if isinstance(r.get(s_name), dict):
                    v_marks.append(r[s_name]['tot'])
                    # இங்கு மேலே சொன்ன அதே தேர்ச்சி விதியைப் பயன்படுத்த வேண்டும்
                    is_p = True
                    if sub.get('has_practical'):
                        if r[s_name]['th'] < 15 or r[s_name]['pr'] < 15 or r[s_name]['tot'] < 35: is_p = False
                    elif r[s_name]['tot'] < 35: is_p = False
                    if is_p: p_cnt += 1

            if v_marks:
                v = pd.Series(v_marks)
                subj_stats.append({
                    "பாடம்": s_name, "எழுதியவர்": len(v), "தேர்ச்சி": p_cnt, "தோல்வி": len(v)-p_cnt,
                    "தேர்ச்சி %": f"{round((p_cnt/len(v))*100,1)}%", "சராசரி": round(v.mean(),1),
                    "அதிகபட்சம்": int(v.max()), "குறைந்தபட்சம்": int(v.min())
                })
        st.table(pd.DataFrame(subj_stats))

        # --- 📋 5. முழுமையான மதிப்பெண் பட்டியல் ---
        st.divider()
        st.subheader("📋 முழுமையான மதிப்பெண் பட்டியல்")
        show_breakup = st.toggle("🔍 அகமதிப்பீடு மற்றும் செய்முறை மதிப்பெண்களைக் காட்டு (Theory/Internal/Practical)")

        final_display_rows = []
        for r in report_rows:
            display_row = {"பெயர்": r['பெயர்'], "மொத்தம்": r['மொத்தம்'], "Fails": r['Fails'], "தோல்வி விவரம்": r['தோல்வி விவரம்'], "Present": r['Present']}
            for sub in relevant_subjects:
                val = r.get(sub['subject_name'])
                if isinstance(val, dict):
                    tot_val = val['tot']
                    if show_breakup:
                        breakup = f"{tot_val}\n({val['th']}+{val['in']}+{val['pr']})" if val['prac_flag'] else f"{tot_val}\n({val['th']}+{val['in']})"
                        display_row[sub['subject_name']] = breakup
                    else:
                        display_row[sub['subject_name']] = tot_val
                else:
                    display_row[sub['subject_name']] = val
            final_display_rows.append(display_row)

        df_final = pd.DataFrame(final_display_rows).sort_values(by=["Fails", "மொத்தம்"], ascending=[True, False]).reset_index(drop=True)
        
        # Smart Rank
        ranks = []; r_val = 1
        for idx, row in df_final.iterrows():
            if row["Fails"] == 0 and row["Present"]:
                ranks.append(str(r_val)); r_val += 1
            else: ranks.append("-")
        df_final.insert(0, "Rank", ranks)

        # ⚡ Highlight Logic (பெரியசாமி போன்ற கேஸ்களைக் கண்டறிய)
        def apply_fail_style(row):
            styles = ['' for _ in row.index]
            for i, col in enumerate(row.index):
                if col in [s['subject_name'] for s in relevant_subjects]:
                    val = row[col]
                    # ABS செக்
                    if val == "ABS": styles[i] = 'color: red'
                    # Detailed Mark செக்
                    elif isinstance(val, str) and '\n' in val:
                        parts = val.split('\n')[1].strip('()').split('+')
                        th_val = int(parts[0])
                        pr_val = int(parts[2]) if len(parts) > 2 else 35 # செய்முறை இல்லை எனில் பாஸ் என வைத்துக்கொள்வோம்
                        tot_val = int(val.split('\n')[0])
                        if th_val < 15 or (len(parts)>2 and pr_val < 15) or tot_val < 35:
                            styles[i] = 'color: red'
                    # Normal Number செக்
                    elif isinstance(val, (int, float)) and val < 35:
                        styles[i] = 'color: red'
            return styles

        cols_to_show = ["Rank", "பெயர்"] + [s['subject_name'] for s in relevant_subjects] + ["மொத்தம்", "தோல்வி விவரம்"]
        st.dataframe(df_final[cols_to_show].style.apply(apply_fail_style, axis=1)
                     .set_properties(**{'background-color': '#f8fafc'}, subset=['மொத்தம்']), use_container_width=True, hide_index=True)

        # 📥 Download
        csv = df_final.to_csv(index=False).encode('utf-8-sig')
        st.download_button("📥 எக்செல் பதிவிறக்கம்", data=csv, file_name=f"{sel_class}_Full_Report.csv")
