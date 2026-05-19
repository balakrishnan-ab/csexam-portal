import streamlit as st
import pdfplumber
import pandas as pd
import io
import re

# --- 1. பக்க அமைப்பு ---
st.set_page_config(page_title="Class-wise Overall Analysis from TML PDF", layout="wide")

# utils கோப்பு இருந்தால் பயன்படுத்தும், இல்லையெனில் பிழை வராமல் தவிர்க்கும் அமைப்பு
try:
    from utils import add_school_header
    add_school_header()
except ModuleNotFoundError:
    st.markdown("<h2 style='text-align: center; color: #1E3A8A;'>அரசு மேல்நிலைப்பள்ளி - தேவனாங்குறிச்சி</h2>", unsafe_allow_html=True)

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

def clean_txt(text):
    """PDF-ல் உள்ள வீண் இடைவெளிகள் மற்றும் சிதைந்த குறியீடுகளைச் சுத்தம் செய்ய"""
    if not text: return ""
    cleaned = re.sub(r'\(cid:\d+\)', '', text)
    return " ".join(cleaned.split()).strip()

# --- 3. PDF கோப்பைப் பதிவேற்றி தரவைப் பிரிக்கும் பகுதி ---
st.markdown('<h3 style="color: #1E3A8A;">📊 SSLC TML PDF - நேரடி பகுப்பாய்வு மற்றும் மாற்றி</h3>', unsafe_allow_html=True)
uploaded_file = st.file_uploader("பகுப்பாய்வு செய்ய வேண்டிய தேர்வுத் துறை TML PDF கோப்பைத் தேர்ந்தெடுக்கவும்...", type=["pdf"])

if uploaded_file is not None:
    st.success("✅ TML PDF வெற்றிகரமாகப் பதிவேற்றப்பட்டது!")
    
    all_students = []
    
    with st.spinner("PDF கோப்பில் இருந்து மாணவர் பெயர்கள் மற்றும் மதிப்பெண்கள் எடுக்கப்படுகின்றன..."):
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
                        
                        # 1. முதல் வரி: Roll No, TMR No, English Name, Marks
                        first_line_match = re.match(r'^(\d{7})\s+([A-Z0-9]{8})\s+(.+)', line_str)
                        if first_line_match:
                            if current_student: 
                                all_students.append(current_student)
                                
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
                                    val = str(marks_tokens[idx]).strip()
                                    if val in ['AAA', 'ABS', '-', '', '–', 'EX']: 
                                        return 0
                                    if val.isdigit():
                                        return int(val)
                                    num_check = re.findall(r'\d+', val)
                                    if num_check:
                                        return int(num_check[0])
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
                        
                        # 2. இரண்டாம் வரி: தமிழ் பெயர் கண்டறிதல்
                        if current_student and line_str.startswith("XM"):
                            reg_match = re.match(r'^XM[A-Z0-9]+\s+(.*?)\s+Father\'s Name\s*:', line_str)
                            if reg_match:
                                t_name = reg_match.group(1)
                                current_student["student_name_tam"] = clean_txt(t_name)
                            continue
                            
                        # 3. மூன்றாம் வரி: இறுதி செய்தல்
                        if current_student and "Father's Name" not in line_str and not line_str.startswith("XM") and not re.match(r'^\d{7}', line_str):
                            all_students.append(current_student)
                            current_student = None

            if current_student: all_students.append(current_student)
        except Exception as e:
            st.error(f"PDF கோப்பை பகுப்பதில் பிழை: {e}")

    # --- 4. பகுப்பாய்வு லாஜிக் மற்றும் UI ரெண்டரிங் ---
    if all_students:
        split_gender = st.toggle("🔍 ஆண் பெண் பிரித்து காட்டு", value=True)
        st.divider()

        g_list = ["LANGUAGE", "ENGLISH", "MATHEMATICS", "SCIENCE", "SOCIAL SCIENCE"]
        
        report_rows, centum_list, absent_list = [], [], []
        st_count = {"total": {"A": 0, "M": 0, "F": 0}, "present": {"A": 0, "M": 0, "F": 0}, "pass": {"A": 0, "M": 0, "F": 0}, "fail": {"A": 0, "M": 0, "F": 0}}
        subject_stats = {sn: {"total": {"M": 0, "F": 0}, "app": {"M": 0, "F": 0}, "pass": {"M": 0, "F": 0}, "fail": {"M": 0, "F": 0}, "marks": [], "student_marks": []} for sn in g_list}
