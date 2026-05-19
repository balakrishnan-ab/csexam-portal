import streamlit as st
import pdfplumber
import pandas as pd
import io
import re
from weasyprint import HTML

# --- 1. பக்க அமைப்பு ---
st.set_page_config(page_title="Class-wise Overall Analysis from TML PDF", layout="wide")

# --- 2. CSS ஸ்டைலிங் (Streamlit UI-க்காக) ---
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
        
        with st.spinner("PDF கோப்பில் இருந்து பள்ளி பெயர், மாணவர் விவரங்கள் எடுக்கப்படுகின்றன..."):
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

    # --- 6. பள்ளி ஒட்டுமொத்தப் பகுப்பாய்வு UI & PDF ஜெனரேஷன் ---
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
                row_raw = {"Rank": "-", "தேர்வு எண்": s['exam_no'], "பெயர்": disp_name, "ப
