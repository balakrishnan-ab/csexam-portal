import streamlit as st
import pdfplumber
import pandas as pd
import io
import re

# --- 1. பக்க அமைப்பு ---
st.set_page_config(page_title="Class-wise Overall Analysis from TML PDF", layout="wide")

# --- 2. CSS ஸ்டைலிங் (UI மற்றும் அச்சு வடிவமைப்பு) ---
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
    
    /* பிரிண்டரில் அச்சிடும் போது தேவையில்லாத கூறுகளை மறைக்கும் CSS */
    @media print {
        header, [data-testid="stSidebar"], [data-testid="stHeader"], .stButton, [data-testid="stElementToolbar"], .stToggle, hr {
            display: none !important;
        }
        .main .block-container {
            padding-top: 0px !important;
            padding-bottom: 0px !important;
        }
    }
    
    /* அச்சிடக்கூடிய தாள்களுக்கான அட்டவணை வடிவமைப்பு */
    .print-table { width: 100%; border-collapse: collapse; font-family: Arial, sans-serif; font-size: 10pt; margin-top: 15px; }
    .print-table th { background-color: #1e3a8a !important; color: white !important; padding: 8px 5px; border: 1px solid #cbd5e1; font-size: 9.5pt; text-align: center; }
    .print-table td { border: 1px solid #cbd5e1; padding: 7px 5px; text-align: center; font-weight: bold; color: #1e293b; }
    .print-table tr:nth-child(even) { background-color: #f8fafc; }
    .print-header { text-align: center; padding-bottom: 10px; border-bottom: 3px double #1e3a8a; margin-bottom: 20px; }
    </style>
    """, unsafe_allow_html=True)

def clean_txt(text):
    if not text: return ""
    cleaned = re.sub(r'\(cid:\d+\)', '', text)
    return " ".join(cleaned.split()).strip()

# --- 3. Session State மேனேஜ்மென்ட் ---
if "parsed_students" not in st.session_state:
    st.session_state.parsed_students = None
if "excel_data" not in st.session_state:
    st.session_state.excel_data = None
if "pdf_file_name" not in st.session_state:
    st.session_state.pdf_file_name = ""
if "school_name" not in st.session_state:
    st.session_state.school_name = "அரசு மேல்நிலைப்பள்ளி"

# --- 4. PDF கோப்பைப் பதிவேற்றும் பகுதி ---
st.markdown('<h3 style="color: #1E3A8A;">📊 SSLC TML PDF - நேரடி பகுப்பாய்வு மற்றும் மாற்றி</h3>', unsafe_allow_html=True)
uploaded_file = st.file_uploader("பகுப்பாய்வு செய்ய வேண்டிய தேர்வுத் துறை TML PDF கோப்பைத் தேர்ந்தெடுக்கவும்...", type=["pdf"])

if uploaded_file is not None:
    if st.session_state.pdf_file_name != uploaded_file.name:
        st.session_state.parsed_students = None
        st.session_state.excel_data = None
        st.session_state.pdf_file_name = uploaded_file.name
        st.session_state.school_name = "அரசு மேல்நிலைப்பள்ளி"

    st.success("✅ TML PDF வெற்றிகரமாகப் பதிவேற்றப்பட்டது!")
    split_gender = st.toggle("🔍 ஆண் பெண் பிரித்து காட்டு", value=True)
    
    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        process_analysis = st.button("📊 பள்ளி பகுப்பாய்வை மட்டும் காட்டு", type="primary", use_container_width=True)
    with col_btn2:
        process_excel = st.button("📥 எக்ஸ்ெல் கோப்பை மட்டும் உருவாக்கு", type="secondary", use_container_width=True)

    # --- பிரதான PDF Parsing லாஜிக் ---
    if (process_analysis or process_excel) and st.session_state.parsed_students is None:
        students_list = []
        detected_school = ""
        
        with st.spinner("PDF கோப்பில் இருந்து விவரங்கள் எடுக்கப்படுகின்றன..."):
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
                            
                            if not detected_school and ("GOVT HR" in line_str or "SCHL" in line_str or "SCHOOL" in line_str):
                                schl_match = re.search(r'(GOVT\s+HR\s+SEC\s+SCHOOL\s+.*)', line_str)
                                if schl_match:
                                    detected_school = clean_txt(schl_match.group(1))
                                    st.session_state.school_name = detected_school
                            
                            first_line_match = re.match(r'^(\d{7})\s+([A-Z0-9]{8})\s+(.+)', line_str)
                            if first_line_match:
                                if current_student: 
                                    students_list.append(current_student)
                                    
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
                                
                                def get_m(idx, default=0):
                                    if idx < len(marks_tokens):
                                        val = str(marks_tokens[idx]).strip().upper()
                                        if val in ['AAA', 'ABS', '-', '', '–', 'EX']: return "ABS"
                                        if val == "XXX": return "EXEMPTED"
                                        if val.isdigit(): 
                                            num = int(val)
                                            return "ABS" if num == 0 else num
                                        num_check = re.findall(r'\d+', val)
                                        if num_check: 
                                            num = int(num_check[0])
                                            return "ABS" if num == 0 else num
                                    return default

                                lang_mark = get_m(1)
                                eng_mark = get_m(2)
                                maths_mark = get_m(4)
                                sci_the = get_m(5)
                                sci_pra = get_m(6)
                                sci_tot = get_m(7)
                                soc_mark = get_m(8)
                                
                                total_val = marks_tokens[-2] if len(marks_tokens) > 2 else "0"
                                total_mark = int(total_val) if str(total_val).isdigit() else 0
                                result = marks_tokens[-1] if len(marks_tokens) > 1 else "F"
                                
                                current_student = {
                                    "exam_no": roll_no, "TMR No": tmr_no, "student_name": student_name_eng, "student_name_tam": "",
                                    "gender": sex, "dob": dob, "LANGUAGE": lang_mark, "ENGLISH": eng_mark,
                                    "MATHEMATICS": maths_mark, "SCIENCE_THE": sci_the, "SCIENCE_PRA": sci_pra,
                                    "SCIENCE": sci_tot, "SOCIAL SCIENCE": soc_mark, "மொத்தம்": total_mark, "Result": result,
                                    "class_name": "SSLC", "இனம்": "BC" if int(roll_no) % 2 == 0 else "MBC"
                                }
                                continue
                            
                            if current_student and line_str.startswith("XM"):
                                reg_match = re.match(r'^XM[A-Z0-9]+\s+(.*?)\s+Father\'s Name\s*:', line_str)
                                if reg_match:
                                    t_name = reg_match.group(1)
                                    current_student["student_name_tam"] = clean_txt(t_name)
                                continue
                                
                            if current_student and "Father's Name" not in line_str and not line_str.startswith("XM") and not re.match(r'^\d{7}', line_str):
                                students_list.append(current_student)
                                current_student = None

                if current_student: students_list.append(current_student)
                st.session_state.parsed_students = students_list
            except Exception as e:
                st.error(f"❌ PDF கோப்பை பகுப்பதில் பிழை: {e}")

    # --- பிரதான பள்ளிப் பெயர் தலைப்பு ---
    st.markdown(f"<h2 style='text-align: center; color: #1E3A8A; font-weight: bold;'>🏫 {st.session_state.school_name}</h2>", unsafe_allow_html=True)

    # --- 5. Excel கோப்பு பதிவிறக்கம் பகுதி ---
    if process_excel or st.session_state.excel_data is not None:
        if st.session_state.parsed_students:
            if st.session_state.excel_data is None:
                flat_excel_rows = []
                for s in st.session_state.parsed_students:
                    flat_excel_rows.append({
                        "Roll No": s.get("exam_no", ""), "TMR No": s.get("TMR No", ""), 
                        "Student Name (ENG)": s.get("student_name", ""), "Student Name (TAM)": s.get("student_name_tam", ""),
                        "Sex": s.get("gender", ""), "DOB": s.get("dob", ""), 
                        "Language": s.get("LANGUAGE", "ABS"), "English": s.get("ENGLISH", "ABS"),
                        "Maths": s.get("MATHEMATICS", "ABS"), "Science THE": s.get("SCIENCE_THE", 0), "Science PRA": s.get("SCIENCE_PRA", 0),
                        "Science TOT": s.get("SCIENCE", "ABS"), "Social Science": s.get("SOCIAL SCIENCE", "ABS"), 
                        "Total": s.get("மொத்தம்", 0), "Result": s.get("Result", "F")
                    })
                df_download = pd.DataFrame(flat_excel_rows)
                excel_buffer = io.BytesIO()
                with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
                    df_download.to_excel(writer, sheet_name="SSLC TML Marks", index=False)
                st.session_state.excel_data = excel_buffer.getvalue()
            
            st.markdown('<div class="responsive-subtitle">📥 எக்ஸ்ெல் கோப்பு பதிவிறக்கம் (Download Excel)</div>', unsafe_allow_html=True)
            st.download_button(
                label="🟢 சுத்தமான எக்ஸ்ெல் கோப்பைப் பதிவிறக்கம் செய்ய இங்கே கிளிக் செய்யவும்",
                data=st.session_state.excel_data,
                file_name=f"Formatted_{uploaded_file.name.rsplit('.', 1)[0]}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )

    # --- 6. பள்ளி ஒட்டுமொத்தப் பகுப்பாய்வு UI ரெண்டரிங் ---
    if process_analysis or (st.session_state.parsed_students is not None and not process_excel):
        if st.session_state.parsed_students:
            st.divider()
            g_list = ["LANGUAGE", "ENGLISH", "MATHEMATICS", "SCIENCE", "SOCIAL SCIENCE"]
            
            report_rows, centum_list, absent_list = [], [], []
            st_count = {"total": {"A": 0, "M": 0, "F": 0}, "present": {"A": 0, "M": 0, "F": 0}, "pass": {"A": 0, "M": 0, "F": 0}, "fail": {"A": 0, "M": 0, "F": 0}}
            subject_stats = {sn: {"total": {"M": 0, "F": 0}, "app": {"M": 0, "F": 0}, "pass": {"M": 0, "F": 0}, "fail": {"M": 0, "F": 0}, "marks": [], "student_marks": []} for sn in g_list}
            fail_cats = {1: [], 2: [], 3: [], 4: [], 5: [], "All": []}

            for s in st.session_state.parsed_students:
                gen = s['gender'] if s['gender'] in ['M', 'F'] else 'M'
                comm = s['இனம்']
                disp_name = s['student_name_tam'] if s['student_name_tam'] else s['student_name']
                
                st_count["total"]["A"] += 1; st_count["total"][gen] += 1
                row_raw = {"Rank": "-", "தேர்வு எண்": s['exam_no'], "பெயர்": disp_name, "பிரிவு": s['class_name'], "gender": gen, "இனம்": comm}
                total_m, fails, wrote_any, fail_subs, student_centums = 0, 0, False, [], []

                for sn in g_list:
                    tot = s.get(sn)
                    subject_stats[sn]["total"][gen] += 1
                    
                    if tot == "EXEMPTED":
                        row_raw[sn] = "EXEMPTED"
                    elif tot == "ABS":
                        row_raw[sn] = "ABS"
                        fails += 1; fail_subs.append(sn)
                        subject_stats[sn]["fail"][gen] += 1
                    else:
                        wrote_any = True
                        tot = int(tot)
                        
                        if sn == "SCIENCE":
                            th = int(s.get("SCIENCE_THE", 0)) if str(s.get("SCIENCE_THE")).isdigit() else 0
                            pr = int(s.get("SCIENCE_PRA", 0)) if str(s.get("SCIENCE_PRA")).isdigit() else 0
                            is_subj_pass = (th >= 15 and pr >= 15 and tot >= 35)
                            tag_str = f"({th}+{pr})"
                        else:
                            is_subj_pass = (tot >= 35)
                            tag_str = ""
                            
                        subject_stats[sn]["app"][gen] += 1
                        subject_stats[sn]["marks"].append(tot)
                        subject_stats[sn]["student_marks"].append({"name": disp_name, "mark": tot, "exam_no": s['exam_no']})
                        
                        if is_subj_pass: 
                            subject_stats[sn]["pass"][gen] += 1
                            if tot == 100: student_centums.append(sn)
                        else: 
                            subject_stats[sn]["fail"][gen] += 1
                            fails += 1; fail_subs.append(sn)
                            
                        total_m += tot
                        row_raw[sn] = {"tot": tot, "tag": tag_str, "pass": is_subj_pass}

                if wrote_any:
                    st_count["present"]["A"] += 1; st_count["present"][gen] += 1
                    if fails == 0: st_count["pass"]["A"] += 1; st_count["pass"][gen] += 1
                    else:
                        st_count["fail"]["A"] += 1; st_count["fail"][gen] += 1
                        txt = f"{disp_name} - ({', '.join(fail_subs)})"
                        if fails >= len(g_list): fail_cats["All"].append(txt)
                        elif fails in [1,2,3,4,5]: fail_cats[fails].append(txt)
                    if student_centums: centum_list.append(f"🥇 {disp_name} - {', '.join(student_centums)}")
                else: 
                    absent_list.append(f"❌ {disp_name}")

                row_raw.update({"மொத்தம்": total_m, "Fails": fails, "தோல்வி விவரம்": f"({', '.join(fail_subs)})" if fail_subs else ""})
                report_rows.append(row_raw)

            # --- Dashboard Cards UI ---
            st.markdown('<div class="responsive-subtitle">📊 PDF-லிருந்து பெறப்பட்ட பள்ளி ஒட்டுமொத்தப் புள்ளிவிவரம்</div>', unsafe_allow_html=True)
            gt_total = f"({st_count['total']['F']}F|{st_count['total']['M']}M)" if split_gender else ""
            gt_present = f"({st_count['present']['F']}F|{st_count['present']['M']}M)" if split_gender else ""
            gt_pass = f"({st_count['pass']['F']}F|{st_count['pass']['M']}M)" if split_gender else ""
            gt_fail = f"({st_count['fail']['F']}F|{st_count['fail']['M']}M)" if split_gender else ""
            pass_percentage = round((st_count['pass']['A'] / st_count['present']['A']) * 100, 1) if st_count['present']['A'] > 0 else 0
            avg_v = round(sum([r['மொத்தம்'] for r in report_rows if r['மொத்தம்'] > 0]) / st_count['present']['A'], 1) if st_count['present']['A'] > 0 else 0

            # ஸ்ட்ரீம்லிட்டின் சொந்த மெட்ரிக் கொண்டு டேஷ்போர்டு கார்டுகள் அமைத்தல்
            md_col1, md_col2, md_col3, md_col4, md_col5, md_col6 = st.columns(6)
            md_col1.metric("Total Applied", f"{st_count['total']['A']}", gt_total)
            md_col2.metric("Present", f"{st_count['present']['A']}", gt_present)
            md_col3.metric("Passed", f"{st_count['pass']['A']}", gt_pass)
            md_col4.metric("Failed", f"{st_count['fail']['A']}", gt_fail)
            md_col5.metric("Pass %", f"{pass_percentage}%")
            md_col6.metric("School Avg", f"{avg_v}")

            # --- 📈 பாடவாரி விரிவான பகுப்பாய்வு அட்டவணை ---
            st.markdown('<div class="responsive-subtitle">📈 பாடவாரி விரிவான பகுப்பாய்வு</div>', unsafe_allow_html=True)
            sub_df_list = []
            for sn in g_list:
                stt = subject_stats[sn]
                total_applied = stt['total']['F'] + stt['total']['M']
                total_appeared = stt['app']['F'] + stt['app']['M']
                total_passed = stt['pass']['F'] + stt['pass']['M']
                total_failed = stt['fail']['F'] + stt['fail']['M']
                
                avg_s = round(sum(stt["marks"])/len(stt["marks"]),1) if stt["marks"] else 0
                pass_perc = f"{round((total_passed / total_appeared) * 100, 1)}%" if total_appeared > 0 else "0.0%"
                
                sub_df_list.append({
                    "Subject": sn, "Total (Applied)": f"{total_applied}", "Appeared (தேர்வு எழுதியோர்)": f"{total_appeared}",
                    "Pass": f"{total_passed}", "Fail": f"{total_failed}", "Pass%": pass_perc, 
                    "Min": min(stt["marks"]) if stt["marks"] else 0, "Max": max(stt["marks"]) if stt["marks"] else 0, "Avg": avg_s
                })
            st.table(pd.DataFrame(sub_df_list))

            # --- Ranks sorting ---
            df_sorted = pd.DataFrame(report_rows).sort_values(by=["Fails", "மொத்தம்"], ascending=[True, False]).reset_index(drop=True)
            rv = 1
            for idx, row in df_sorted.iterrows():
                if int(row["Fails"]) == 0: 
                    df_sorted.at[idx, "Rank"] = str(rv)
                    rv += 1

            # --- 🖨️ அச்சிடக்கூடிய அறிக்கை வடிவம் (முழுமையான HTML பிக்ஸ்) ---
            st.markdown('<div class="responsive-subtitle">🖨️ அச்சிடக்கூடிய அறிக்கை வடிவம் (Printable Report Layout)</div>', unsafe_allow_html=True)
            st.info("💡 **பிரிண்ட் செய்யும் முறை:** இந்த ரிப்போர்ட்டை அப்படியே காகிதத்தில் அச்சிட அல்லது PDF ஆகச் சேமிக்க உங்கள் விசைப்பலகையில் (Keyboard) **Ctrl + P** அழுத்தவும். சைட் பார் மெனு மற்றும் தேவையற்ற பொத்தான்கள் தானாகவே மறைந்துவிடும்.")
            
            sub_table_rows_html = ""
            for item in sub_df_list:
                sub_table_rows_html += f"<tr><td>{item['Subject']}</td><td>{item['Total (Applied)']}</td><td>{item['Appeared (தேர்வு எழுதியோர்)']}</td><td>{item['Pass']}</td><td>{item['Fail']}</td><td style='color:green;'>{item['Pass%']}</td><td>{item['Min']}</td><td>{item['Max']}</td><td>{item['Avg']}</td></tr>"

            marks_table_rows_html = ""
            for _, r in df_sorted.iterrows():
                m_lang = r['LANGUAGE']['tot'] if isinstance(r['LANGUAGE'], dict) else r['LANGUAGE']
                m_eng = r['ENGLISH']['tot'] if isinstance(r['ENGLISH'], dict) else r['ENGLISH']
                m_math = r['MATHEMATICS']['tot'] if isinstance(r['MATHEMATICS'], dict) else r['MATHEMATICS']
                m_sci = r['SCIENCE']['tot'] if isinstance(r['SCIENCE'], dict) else r['SCIENCE']
                m_soc = r['SOCIAL SCIENCE']['tot'] if isinstance(r['SOCIAL SCIENCE'], dict) else r['SOCIAL SCIENCE']
                
                f_color = "red" if int(r['Fails']) > 0 else "black"
                rank_val = r['Rank'] if r['Rank'] != "-" else ""
                s_name = r['பெயர்']
                s_exam_no = r['தேர்வு எண்']
                s_total = r['மொத்தம்']
                s_fails = r['Fails']
                
                marks_table_rows_html += f"<tr><td>{rank_val}</td><td>{s_exam_no}</td><td style='text-align: left; padding-left:10px;'>{s_name}</td><td>{m_lang}</td><td>{m_eng}</td><td>{m_math}</td><td>{m_sci}</td><td>{m_soc}</td><td style='font-weight: bold;'>{s_total}</td><td>{'PASS' if int(s_fails)==0 else 'FAIL'}</td></tr>"

            # HTML குறியீடு எங்கும் உடையாமல் இருக்க முழுமையாக வெளியே ஸ்ட்ரிங் இணைக்கப்படுகிறது
            full_report_html = f"""
            <div style="background-color: white; padding: 25px; border: 1px solid #cbd5e1; border-radius: 8px; color: #1e293b;">
                <div class="print-header">
                    <div class="school-title">🏫 {st.session_state.school_name}</div>
                    <div style="font-size:13pt; font-weight:bold; color:#475569; margin-top:5px;">SSLC TML PERFORMANCE ANALYSIS REPORT</div>
                </div>
                
                <table class="print-table">
                    <thead>
                        <tr>
                            <th>Subject Name</th>
                            <th>Applied</th>
                            <th>Appeared</th>
                            <th>Passed</th>
                            <th>Failed</th>
                            <th>Pass %</th>
                            <th>Min</th>
                            <th>Max</th>
                            <th>Avg</th>
                        </tr>
                    </thead>
                    <tbody>
                        {sub_table_rows_html}
                    </tbody>
                </table>
                
                <h4 style="margin-top:35px; color:#1e3a8a; border-bottom: 2px solid #e2e8f0; padding-bottom:5px;">Consolidated Student Mark Register</h4>
                <table class="print-table">
                    <thead>
                        <tr>
                            <th>Rank</th>
                            <th>Roll No</th>
                            <th style="text-align: left; padding-left:10px;">Student Name</th>
                            <th>Lang</th>
                            <th>Eng</th>
                            <th>Math</th>
                            <th>Sci</th>
                            <th>Soc</th>
                            <th>Total</th>
                            <th>Result</th>
                        </tr>
                    </thead>
                    <tbody>
                        {marks_table_rows_html}
                    </tbody>
                </table>
                <div style="text-align:right; margin-top:60px; font-weight:bold; font-size:11pt; padding-right:15px;">Headmaster / Principal Signature</div>
            </div>
            """
            
            # மார்க் டவுன் மூலம் HTML-ஐ அப்படியே போர்ட்டலில் ரெண்டர் செய்தல்
            st.markdown(full_report_html, unsafe_allow_html=True)
            st.divider()

            # --- 📋 UI-இல் முழுமையான மதிப்பெண் பட்டியல் (திரையில் பார்க்க மட்டும்) ---
            st.markdown('<div class="responsive-subtitle">📋 முழுமையான மதிப்பெண் பட்டியல் (Interactive Screen View)</div>', unsafe_allow_html=True)
            show_det = st.toggle("🔍 மதிப்பீட்டு விவரங்களைக் காட்டு", value=True)
            
            final_disp = []
            for _, r in df_sorted.iterrows():
                d_row = {"Rank": r["Rank"], "தேர்வு எண்": r["தேர்வு எண்"], "பெயர்": r['பெயர்'], "இனம்": r['இனம்'], "மொத்தம்": r['மொத்தம்'], "Fails": r['Fails'], "தோல்வி விவரம்": r['தோல்வி விவரம்']}
                for sn in g_list:
                    v = r.get(sn)
                    if isinstance(v, dict): d_row[sn] = f"{v['tot']}\n{v['tag']}" if show_det and v['tag'] else v['tot']
                    else: d_row[sn] = v
                final_disp.append(d_row)

            st.dataframe(pd.DataFrame(final_disp).style.map(lambda v: 'color: red' if 'ABS' in str(v) or (isinstance(v, (int,float)) and 0<v<35) else ('color: blue' if 'EXEMPTED' in str(v) else '')), use_container_width=True, hide_index=True)
