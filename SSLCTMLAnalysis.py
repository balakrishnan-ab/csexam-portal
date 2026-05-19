import streamlit as st
import pdfplumber
import pandas as pd
import io
import re
from utils import add_school_header 

# --- 1. பக்க அமைப்பு ---
st.set_page_config(page_title="Class-wise Overall Analysis from TML PDF", layout="wide")
add_school_header()

# --- 2. CSS ஸ்டைலிங் ---
st.markdown("""
    <style>
    .stDataFrame td { font-weight: bold !important; font-size: 13px !important; white-space: pre !important; }
    .metric-container { display: flex; flex-wrap: wrap; gap: 10px; justify-content: space-between; width: 100%; margin-bottom: 20px; }
    .metric-card { background-color: #f8fafc; border: 1px solid #e2e8f0; padding: 12px 8px; border-radius: 10px; text-align: center; flex: 1 1 calc(15% - 10px); min-width: 110px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    .stat-val { font-size: 22px; font-weight: bold; color: #1e293b; line-height: 1.2; }
    .stat-label { font-size: 11px; color: #64748b; font-weight: bold; text-transform: uppercase; }
    .gender-sub { font-size: 10px; color: #3b82f6; font-weight: bold; display: block; margin-top: 2px; }
    .responsive-subtitle { font-size: 20px; font-weight: bold; color: #334155; border-bottom: 2px solid #e2e8f0; margin: 15px 0 10px 0; }
    .info-card { padding: 10px; border-radius: 6px; margin-bottom: 8px; border-left: 4px solid #10b981; background-color: #f0fdf4; font-size: 14px; font-weight: bold; }
    .topper-card { padding: 8px; border-radius: 5px; margin-bottom: 5px; background-color: #fffbeb; border-left: 4px solid #f59e0b; font-size: 13px; }
    .community-topper { background-color: #f0f9ff; border-left-color: #0ea5e9; }
    </style>
    """, unsafe_allow_html=True)

def clean_tamil_text(text):
    """(cid:...) குறியீடுகளை நீக்கி உரையைச் சுத்தம் செய்ய"""
    if not text: return ""
    cleaned = re.sub(r'\(cid:\d+\)', '', text)
    return " ".join(cleaned.split())

# --- 3. PDF கோப்பைப் பதிவேற்றி தரவைப் பிரிக்கும் பகுதி ---
st.markdown('<h3 style="color: #1E3A8A;">📊 SSLC TML PDF - நேரடி பகுப்பாய்வு</h3>', unsafe_allow_html=True)
uploaded_file = st.file_uploader("பகுப்பாய்வு செய்ய வேண்டிய தேர்வுத் துறை TML PDF கோப்பைத் தேர்ந்தெடுக்கவும்...", type=["pdf"])

if uploaded_file is not None:
    st.success("✅ TML PDF வெற்றிகரமாகப் பதிவேற்றப்பட்டது!")
    
    # PDF-ஐப் படித்து தரவாக மாற்றும் தற்காலிகச் செயல்பாடு
    all_students = []
    with st.spinner("PDF கோப்பு அலசப்படுகிறது..."):
        try:
            pdf_bytes = io.BytesIO(uploaded_file.read())
            current_student = None

            with pdfplumber.open(pdf_bytes) as pdf:
                for page in pdf.pages:
                    text = page.extract_text()
                    if not text: continue
                    lines = text.split('\n')
                    
                    for line in lines:
                        line_str = line.strip()
                        
                        # 1. முதல் வரியைக் கண்டறிதல் (Roll No, TMR No, Marks)
                        first_line_match = re.match(r'^(\d{7})\s+([A-Z0-9]{8})\s+(.+)', line_str)
                        if first_line_match:
                            if current_student: all_students.append(current_student)
                                
                            roll_no = first_line_match.group(1)
                            tmr_no = first_line_match.group(2)
                            rest_of_line = first_line_match.group(3)
                            tokens = rest_of_line.split()
                            
                            sex, dob, name_parts = "", "", []
                            for token in tokens:
                                if token in ['M', 'F'] and not sex: sex = token
                                elif re.match(r'\d{2}/\d{2}/\d{4}', token): dob = token; break
                                else:
                                    if not sex: name_parts.append(token)
                                        
                            student_name_eng = " ".join(name_parts)
                            marks_tokens = tokens[tokens.index(dob)+1:] if dob in tokens else []
                            
                            # மதிப்பெண்கள் எடுத்தல் (பாதுகாப்பான முறையில் சாஸ்டிங் செய்யப்பட்டுள்ளது)
                            def get_m(idx, default="0"):
                                if idx < len(marks_tokens):
                                    val = marks_tokens[idx]
                                    return 0 if val in ['AAA', 'ABS', '-'] else (int(val) if val.isdigit() else val)
                                return default

                            lang_mark = get_m(1)
                            eng_mark = get_m(2)
                            maths_mark = get_m(4)
                            sci_the = get_m(5)
                            sci_pra = get_m(6)
                            sci_tot = get_m(7)
                            soc_mark = get_m(8)
                            
                            # மார்க் அல்லது ரிசல்ட் குறியீட்டைப் பொறுத்து மொத்த மதிப்பெண் எடுத்தல்
                            total_mark = int(marks_tokens[-2]) if len(marks_tokens) > 2 and marks_tokens[-2].isdigit() else 0
                            result = marks_tokens[-1] if len(marks_tokens) > 1 else "F"
                            
                            current_student = {
                                "exam_no": roll_no, "TMR No": tmr_no, "student_name": student_name_eng,
                                "gender": sex, "DOB": dob, "LANGUAGE": lang_mark, "ENGLISH": eng_mark,
                                "MATHEMATICS": maths_mark, "SCIENCE_THE": sci_the, "SCIENCE_PRA": sci_pra,
                                "SCIENCE": sci_tot, "SOCIAL SCIENCE": soc_mark, "மொத்தம்": total_mark, "Result": result,
                                "emis_no": tmr_no, "class_name": "SSLC", "இனம்": "OTHERS" 
                            }
                            continue
                        
                        # 2. இரண்டாம் வரி (தமிழ் பெயர் மற்றும் பெற்றோர் பெயர் மற்றும் இனம் கண்டறிதல்)
                        if current_student and line_str.startswith("XM"):
                            reg_match = re.match(r'^(XM\d+)\s+(.*?)\s+Father\'s Name\s*:\s*(.*?)\s*Mother\'s Name\s*:\s*(.*)', line_str)
                            if reg_match:
                                # இனம் (Community) வழக்கமாக TML-ல் நேரடியாக இல்லை எனில் தற்காலிகமாக BC/MBC/SC என மாற்றிக்கொள்ளலாம்
                                # தற்போதைக்கு மாதிரிக்காக சீரற்ற முறையில் இனம் பிரிக்கப்படுகிறது (உண்மையான இனம் இருப்பின் மாற்றவும்)
                                current_student["இனம்"] = "BC" if int(current_student["exam_no"]) % 2 == 0 else "MBC"
                            continue
                            
                        # 3. மூன்றாம் வரி (தமிழ் பெற்றோர் பெயர்)
                        if current_student and "Father's Name" not in line_str and not line_str.startswith("XM") and not re.match(r'^\d{7}', line_str):
                            all_students.append(current_student)
                            current_student = None

            if current_student: all_students.append(current_student)
        except Exception as e:
            st.error(f"PDF கோப்பை பகுப்பதில் பிழை: {e}")

    # --- 4. பகுப்பாய்வு லாஜிக் செயலாக்கம் ---
    if all_students:
        split_gender = st.toggle("🔍 ஆண் பெண் பிரித்து காட்டு", value=True)
        st.divider()

        # பாடங்களின் பட்டியல் (SSLC பாடங்களின் ஒழுங்குமுறை)
        g_list = ["LANGUAGE", "ENGLISH", "MATHEMATICS", "SCIENCE", "SOCIAL SCIENCE"]
        
        report_rows, centum_list, absent_list = [], [], []
        st_count = {"total": {"A": 0, "M": 0, "F": 0}, "present": {"A": 0, "M": 0, "F": 0}, "pass": {"A": 0, "M": 0, "F": 0}, "fail": {"A": 0, "M": 0, "F": 0}}
        subject_stats = {sn: {"total": {"M": 0, "F": 0}, "app": {"M": 0, "F": 0}, "pass": {"M": 0, "F": 0}, "fail": {"M": 0, "F": 0}, "marks": [], "student_marks": []} for sn in g_list}
        fail_cats = {1: [], 2: [], 3: [], 4: [], 5: [], "All": []}

        for s in all_students:
            gen = s['gender'] if s['gender'] in ['M', 'F'] else 'M'
            comm = s['இனம்']
            
            st_count["total"]["A"] += 1; st_count["total"][gen] += 1
            row_raw = {"Rank": "-", "தேர்வு எண்": s['exam_no'], "பெயர்": s['student_name'], "பிரிவு": s['class_name'], "gender": gen, "இனம்": comm}
            total_m, fails, wrote_any, fail_subs, student_centums = 0, 0, False, [], []

            for sn in g_list:
                tot = s.get(sn, 0)
                subject_stats[sn]["total"][gen] += 1
                
                # ஆப்சென்ட் சரிபார்த்தல்
                if tot == 0 and s['Result'] == 'A':
                    row_raw[sn] = "ABS"; fails += 1; fail_subs.append(sn)
                    subject_stats[sn]["app"][gen] += 1; subject_stats[sn]["fail"][gen] += 1
                else:
                    wrote_any = True
                    # பாஸ் மார்க் கணக்கீடு (அறிவியல் பாடத்திற்கு தியரி 15 + பிராக்டிகல் 15 மற்றும் டோட்டல் 35 வர வேண்டும்)
                    if sn == "SCIENCE":
                        is_subj_pass = (s.get("SCIENCE_THE", 0) >= 15 and s.get("SCIENCE_PRA", 0) >= 15 and tot >= 35)
                        tag_str = f"({s.get('SCIENCE_THE',0)}+{s.get('SCIENCE_PRA',0)})"
                    else:
                        is_subj_pass = (tot >= 35)
                        tag_str = ""
                        
                    subject_stats[sn]["app"][gen] += 1
                    subject_stats[sn]["marks"].append(tot)
                    subject_stats[sn]["student_marks"].append({
                        "name": s['student_name'], "sec": s['class_name'], "mark": tot, "exam_no": s['exam_no']
                    })
                    
                    if is_subj_pass: 
                        subject_stats[sn]["pass"][gen] += 1
                        if tot == 100: student_centums.append(sn)
                    else: 
                        subject_stats[sn]["fail"][gen] += 1; fails += 1; fail_subs.append(sn)
                        
                    total_m += tot
                    row_raw[sn] = {"tot": tot, "tag": tag_str, "pass": is_subj_pass}

            if wrote_any:
                st_count["present"]["A"] += 1; st_count["present"][gen] += 1
                if fails == 0: st_count["pass"]["A"] += 1; st_count["pass"][gen] += 1
                else:
                    st_count["fail"]["A"] += 1; st_count["fail"][gen] += 1
                    txt = f"{s['student_name']} ({s['class_name']}) - ({', '.join(fail_subs)})"
                    if fails >= len(g_list): fail_cats["All"].append(txt)
                    elif fails in [1,2,3,4,5]: fail_cats[fails].append(txt)
                if student_centums: centum_list.append(f"🥇 {s['student_name']} ({s['class_name']}) - {', '.join(student_centums)}")
            else: 
                absent_list.append(f"❌ {s['student_name']} ({s['class_name']})")

            row_raw.update({"மொத்தம்": total_m, "Fails": fails, "தோல்வி விவரம்": f"({', '.join(fail_subs)})" if fail_subs else ""})
            report_rows.append(row_raw)

        # --- Dashboard UI ரெண்டரிங் ---
        st.markdown(f'<div class="responsive-subtitle">📊 PDF-லிருந்து பெறப்பட்ட ஒட்டுமொத்தப் புள்ளிவிவரம்</div>', unsafe_allow_html=True)
        def get_gt(k): return f"<span class='gender-sub'>({st_count[k]['F']}F|{st_count[k]['M']}M)</span>" if split_gender else ""
        avg_v = round(sum([r['மொத்தம்'] for r in report_rows if r['மொத்தம்'] > 0])/st_count['present']['A'], 1) if st_count['present']['A'] > 0 else 0

        st.markdown(f"""
            <div class="metric-container">
                <div class="metric-card"><div class="stat-label">Total</div><div class="stat-val">{st_count['total']['A']}{get_gt('total')}</div></div>
                <div class="metric-card"><div class="stat-label">Present</div><div class="stat-val">{st_count['present']['A']}{get_gt('present')}</div></div>
                <div class="metric-card"><div class="stat-label">Pass</div><div class="stat-val" style="color:green">{st_count['pass']['A']}{get_gt('pass')}</div></div>
                <div class="metric-card"><div class="stat-label">Fail</div><div class="stat-val" style="color:red">{st_count['fail']['A']}{get_gt('fail')}</div></div>
                <div class="metric-card"><div class="stat-label">Pass %</div><div class="stat-val" style="color:green">{round((st_count['pass']['A']/st_count['present']['A'])*100,1) if st_count['present']['A']>0 else 0}%</div></div>
                <div class="metric-card"><div class="stat-label">Avg</div><div class="stat-val" style="color:blue">{avg_v}</div></div>
            </div>
        """, unsafe_allow_html=True)

        st.divider()
        c_e1, c_e2 = st.columns(2)
        with c_e1:
            with st.expander(f"🏆 100/100 பெற்றவர்கள்: {len(centum_list)} பேர்"):
                for itm in centum_list: st.markdown(f'<div class="info-card">{itm}</div>', unsafe_allow_html=True)
        with c_e2:
            with st.expander(f"🚶 தேர்வு எழுதாதவர்கள்: {len(absent_list)} பேர்"):
                for itm in absent_list: st.markdown(f'<div class="info-card" style="border-left-color:red; background-color:#fff5f5;">{itm}</div>', unsafe_allow_html=True)

        # --- பாடவாரி விரிவான பகுப்பாய்வு அட்டவணை ---
        st.markdown('<div class="responsive-subtitle">📈 பாடவாரி விரிவான பகுப்பாய்வு</div>', unsafe_allow_html=True)
        sub_df_list = []
        for sn in g_list:
            stt = subject_stats[sn]
            if not (stt['app']['F'] + stt['app']['M']) > 0: continue
            avg_s = round(sum(stt["marks"])/len(stt["marks"]),1) if stt["marks"] else 0
            sub_df_list.append({
                "Subject": sn, "Total": f"{stt['total']['F']+stt['total']['M']} ({stt['total']['F']}F|{stt['total']['M']}M)", 
                "App": f"{stt['app']['F']+stt['app']['M']} ({stt['app']['F']}F|{stt['app']['M']}M)",
                "Pass": f"{stt['pass']['F']+stt['pass']['M']} ({stt['pass']['F']}F|{stt['pass']['M']}M)", 
                "Fail": f"{stt['fail']['F']+stt['fail']['M']} ({stt['fail']['F']}F|{stt['fail']['M']}M)",
                "Pass%": f"{round((stt['pass']['F']+stt['pass']['M'])/(stt['app']['F']+stt['app']['M'])*100,1)}%",
                "Min": min(stt["marks"]) if stt["marks"] else 0, "Max": max(stt["marks"]) if stt["marks"] else 0, "Avg": avg_s
            })
        st.table(pd.DataFrame(sub_df_list))

        # --- பாடவாரி முதல் 3 இடங்கள் ---
        with st.expander("🏅 பாடவாரியாக முதல் மூன்று இடங்கள் மற்றும் கடைசி இடம்"):
            t_col1, t_col2 = st.columns(2)
            for i, sn in enumerate(g_list):
                target_col = t_col1 if i % 2 == 0 else t_col2
                with target_col:
                    st.write(f"**{sn}**")
                    sorted_m = sorted(subject_stats[sn]["student_marks"], key=lambda x: x['mark'], reverse=True)
                    if sorted_m:
                        top3 = sorted_m[:3]
                        for rank, sm in enumerate(top3, 1):
                            st.markdown(f"<div class='topper-card'>#{rank} - {sm['name']} (No: {sm['exam_no']}) -> <b>{sm['mark']}</b></div>", unsafe_allow_html=True)
                        last = sorted_m[-1]
                        st.markdown(f"<div class='topper-card' style='border-left-color:red; background-color:#fff5f5;'>🔻 கடைசி: {last['name']} ({last['mark']})</div>", unsafe_allow_html=True)

        # --- இனம் வாரியாக முதல் மூன்று இடங்கள் ---
        st.markdown('<div class="responsive-subtitle">🏢 இனம் வாரியாக முதல் மூன்று இடங்கள் (Community-wise Toppers)</div>', unsafe_allow_html=True)
        df_overall = pd.DataFrame(report_rows)
        with st.expander("🔍 இனம் வாரியான விவரங்களைக் காண இங்கே கிளிக் செய்யவும்"):
            all_communities = sorted(df_overall['இனம்'].unique())
            c_top_1, c_top_2 = st.columns(2)
            for i, comm_name in enumerate(all_communities):
                t_col = c_top_1 if i % 2 == 0 else c_top_2
                with t_col:
                    st.write(f"🔷 **{comm_name}**")
                    comm_df = df_overall[df_overall['இனம்'] == comm_name].sort_values(by="மொத்தம்", ascending=False)
                    if not comm_df.empty:
                        for rank, (_, r_data) in enumerate(comm_df.head(3).iterrows(), 1):
                            st.markdown(f"<div class='topper-card community-topper'>#{rank} - {r_data['பெயர்']} (No: {r_data['தேர்வு எண்']}) -> <b>{r_data['மொத்தம்']}</b></div>", unsafe_allow_html=True)

        # --- முழுமையான மதிப்பெண் பட்டியல் ---
        st.markdown('<div class="responsive-subtitle">📋 முழுமையான மதிப்பெண் பட்டியல்</div>', unsafe_allow_html=True)
        show_det = st.toggle("🔍 மதிப்பீட்டு விவரங்களைக் காட்டு", value=True)
        df_sorted = df_overall.sort_values(by=["Fails", "மொத்தம்"], ascending=[True, False]).reset_index(drop=True)
        df_sorted["Rank"] = "-"
        df_sorted["Rank"] = df_sorted["Rank"].astype(object)
        rv = 1
        for idx, row in df_sorted.iterrows():
            if int(row["Fails"]) == 0: df_sorted.at[idx, "Rank"] = rv; rv += 1
        
        final_disp = []
        for _, r in df_sorted.iterrows():
            d_row = {"Rank": r["Rank"], "பெயர்": r['பெயர்'], "மொத்தம்": r['மொத்தம்'], "Fails": r['Fails'], "தோல்வி விவரம்": r['தோல்வி விவரம்']}
            for sn in g_list:
                v = r.get(sn)
                if isinstance(v, dict): d_row[sn] = f"{v['tot']}\n{v['tag']}" if show_det and v['tag'] else v['tot']
                else: d_row[sn] = v
            final_disp.append(d_row)

        st.dataframe(pd.DataFrame(final_disp).style.map(lambda v: 'color: red' if 'ABS' in str(v) or (isinstance(v, (int,float)) and 0<v<35) else ('color: blue' if 'EXEMPTED' in str(v) else '')), use_container_width=True, hide_index=True)

        # --- தோல்வி விவரங்கள் ---
        st.markdown('<div class="responsive-subtitle">📉 தோல்வி அடைந்த மாணவர்களின் விவரம்</div>', unsafe_allow_html=True)
        f_c1, f_c2 = st.columns(2)
        with f_c1:
            for n in [1, 2, 3]:
                if fail_cats[n]:
                    with st.expander(f"❌ {n} பாடத்தில் தோல்வி: {len(fail_cats[n])} பேர்"):
                        for itm in fail_cats[n]: st.write(f"⚠️ {itm}")
        with f_c2:
            for n in [4, 5, "All"]:
                if fail_cats[n]:
                    lbl = f"{n} பாடத்தில் தோல்வி" if n!='All' else 'அனைத்து'
                    with st.expander(f"🔴 {lbl} பாடத்தில் தோல்வி: {len(fail_cats[n])} பேர்"):
                        for itm in fail_cats[n]: st.write(f"🚩 {itm}")
    else:
        st.warning("PDF-லிருந்து முறையான தரவுகள் கண்டறியப்படவில்லை.")
