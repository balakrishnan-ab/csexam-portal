import streamlit as st
import pdfplumber
import pandas as pd
import io
import re

def clean_tamil_text(text):
    """(cid:...) குறியீடுகளை நீக்கி உரையைச் சுத்தம் செய்ய"""
    if not text:
        return ""
    cleaned = re.sub(r'\(cid:\d+\)', '', text)
    # கூடுதல் இடைவெளிகளை நீக்குதல்
    return " ".join(cleaned.split())

def show_pdf_to_excel_page():
    st.markdown("""
        <style>
        .main-title { font-size:26px !important; font-weight: bold; color: #1E3A8A; text-align: center; }
        .sub-text { font-size:15px !important; color: #4B5563; text-align: center; margin-bottom: 20px; }
        </style>
        """, unsafe_allow_html=True)
    
    st.markdown('<p class="main-title">📊 SSLC TML PDF to Excel Converter (Multi-Line Parser)</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-text">3-வரி வடிவமைப்பு கொண்ட தேர்வுத்துறை TML PDF-ஐ துல்லியமாக பத்திகளாக பிரிக்கும் மேம்பட்ட தளம்.</p>', unsafe_allow_html=True)
    
    st.divider()

    uploaded_file = st.file_uploader("தேர்வுத் துறை TML PDF கோப்பைத் தேர்ந்தெடுக்கவும்...", type=["pdf"])

    if uploaded_file is not None:
        st.success("✅ TML PDF வெற்றிகரமாகப் பதிவேற்றப்பட்டது!")
        
        if st.button("தரவை பத்திகளாகப் பிரி (Process & Split Columns)", type="primary"):
            with st.spinner("PDF பக்கங்கள் மற்றும் வரிகள் விரிவாக பகுப்பாய்வு செய்யப்படுகின்றன..."):
                try:
                    pdf_bytes = io.BytesIO(uploaded_file.read())
                    all_students = []
                    
                    # தற்காலிகமாக ஒரு மாணவரின் 3 வரி தரவுகளைச் சேமிக்க
                    current_student = None

                    with pdfplumber.open(pdf_bytes) as pdf:
                        for page in pdf.pages:
                            text = page.extract_text()
                            if not text:
                                continue
                                
                            lines = text.split('\n')
                            
                            for i, line in enumerate(lines):
                                line_str = line.strip()
                                
                                # 1. முதல் வரியைக் கண்டறிதல்: 7 இலக்க Roll No மற்றும் 8 இலக்க TMR No உடன் தொடங்கும் வரி
                                # எ.கா: 8382429 P2366185 AAFIYA HASSIN M F 07/12/2009 T 087 094 ...
                                first_line_match = re.match(r'^(\d{7})\s+([A-Z0-9]{8})\s+(.+)', line_str)
                                
                                if first_line_match:
                                    # முந்தைய மாணவர் விவரம் அரைகுறையாக இருந்தால் சேமித்துவிட்டு புதிய மாணவரைத் தொடங்கு
                                    if current_student:
                                        all_students.append(current_student)
                                        
                                    roll_no = first_line_match.group(1)
                                    tmr_no = first_line_match.group(2)
                                    rest_of_line = first_line_match.group(3)
                                    
                                    # பாக்கி உள்ள வரியிலிருந்து தற்காலிகமாக ஸ்பேஸ் மூலம் தரவுகளைப் பிரித்தல்
                                    tokens = rest_of_line.split()
                                    
                                    # அத்தியாவசிய விவரங்களை Regex அல்லது டோக்கன் பொசிஷன் மூலம் எடுத்தல்
                                    # பாலினம் (M/F) மற்றும் பிறந்த தேதியைக் கண்டறிதல்
                                    sex = ""
                                    dob = ""
                                    name_parts = []
                                    
                                    for token in tokens:
                                        if token in ['M', 'F'] and not sex:
                                            sex = token
                                        elif re.match(r'\d{2}/\d{2}/\d{4}', token):
                                            dob = token
                                            break
                                        else:
                                            if not sex:
                                                name_parts.append(token)
                                                
                                    student_name_eng = " ".join(name_parts)
                                    
                                    # மதிப்பெண்களை வரியின் இறுதியிலிருந்து எடுத்தல் (Reverse Parsing)
                                    # எ.கா முடிவில்: ... 088 409 P
                                    # அறிவியல் பாடம் 3 மதிப்பெண்கள் (THE PRA TOT) கொண்டிருப்பதால் துல்லியமாக எடுக்க வேண்டும்
                                    marks_tokens = tokens[tokens.index(dob)+1:] if dob in tokens else []
                                    
                                    # பொதுவான மதிப்பெண் எடுக்கும் கட்டமைப்பு
                                    lang_mark = marks_tokens[1] if len(marks_tokens) > 1 else ""
                                    eng_mark = marks_tokens[2] if len(marks_tokens) > 2 else ""
                                    maths_mark = marks_tokens[4] if len(marks_tokens) > 4 else ""
                                    
                                    # அறிவியல் தியரி, பிராக்டிகல், டோட்டல் (Sci THE, Sci PRA, Sci TOT)
                                    sci_the = marks_tokens[5] if len(marks_tokens) > 5 else ""
                                    sci_pra = marks_tokens[6] if len(marks_tokens) > 6 else ""
                                    sci_tot = marks_tokens[7] if len(marks_tokens) > 7 else ""
                                    
                                    soc_mark = marks_tokens[8] if len(marks_tokens) > 8 else ""
                                    total_mark = marks_tokens[-2] if len(marks_tokens) > 2 else ""
                                    result = marks_tokens[-1] if len(marks_tokens) > 1 else ""
                                    
                                    current_student = {
                                        "Roll No": roll_no,
                                        "TMR No": tmr_no,
                                        "Student Name (ENG)": clean_tamil_text(student_name_eng),
                                        "Student Name (TAM)": "",
                                        "Sex": sex,
                                        "DOB": dob,
                                        "Father Name (ENG)": "",
                                        "Mother Name (ENG)": "",
                                        "Language": lang_mark,
                                        "English": eng_mark,
                                        "Maths": maths_mark,
                                        "Science THE": sci_the,
                                        "Science PRA": sci_pra,
                                        "Science TOT": sci_tot,
                                        "Social Science": soc_mark,
                                        "Total": total_mark,
                                        "Result": result
                                    }
                                    continue
                                
                                # 2. இரண்டாம் வரியைக் கண்டறிதல்: Permanent Reg No (XM...) உடன் தொடங்கும் வரி
                                # எ.கா: XM25R2238382429 ஆஃபியா ஹஸீன் மு Father's Name : MOHAMEDGHOUSE Mother's Name : TAJHASSIN
                                if current_student and line_str.startswith("XM"):
                                    reg_match = re.match(r'^(XM\d+)\s+(.*?)\s+Father\'s Name\s*:\s*(.*?)\s*Mother\'s Name\s*:\s*(.*)', line_str)
                                    if reg_match:
                                        current_student["Student Name (TAM)"] = clean_tamil_text(reg_match.group(2))
                                        current_student["Father Name (ENG)"] = clean_tamil_text(reg_match.group(3))
                                        current_student["Mother Name (ENG)"] = clean_tamil_text(reg_match.group(4))
                                    continue
                                    
                                # 3. மூன்றாம் வரியைக் கண்டறிதல்: தமிழ் தந்தை/தாய் பெயர் (வழக்கமாக 2ஆம் வரிக்கு அடுத்து வரும் உரை)
                                # நேரடியாக மாணவர் பட்டியல் முடியும் வரை அல்லது அடுத்த மாணவர் வரும் வரை தரவைச் சேர்க்கலாம்
                                if current_student and "Father's Name" not in line_str and not line_str.startswith("XM") and not re.match(r'^\d{7}', line_str):
                                    # இந்த வரியில் தமிழ் தந்தை மற்றும் தாய் பெயர்கள் இருக்கும் (தேவைப்பட்டால் தனியாகப் பிரிக்கலாம், தற்போதைக்குத் தவிர்க்கப்படுகிறது அல்லது தனிக் காலமில் வைக்கலாம்)
                                    all_students.append(current_student)
                                    current_student = None

                        # இறுதி மாணவர் விடுபட்டிருந்தால் சேர்த்தல்
                        if current_student:
                            all_students.append(current_student)

                    if all_students:
                        df_final = pd.DataFrame(all_students)
                        
                        # எக்ஸ்ெல் கோப்பாக மாற்றுதல்
                        excel_buffer = io.BytesIO()
                        with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
                            df_final.to_excel(writer, sheet_name="SSLC TML Marks", index=False)
                        
                        processed_data = excel_buffer.getvalue()
                        
                        st.balloons()
                        st.subheader("🎉 எக்ஸ்ெல் கோப்பு வெற்றிகரமாக உருவாக்கப்பட்டது!")
                        st.metric(label="மொத்த மாணவர்களின் எண்ணிக்கை", value=f"{len(df_final)} பேர்")
                        
                        st.write("📊 **பிரித்தெடுக்கப்பட்ட தரவின் மாதிரிக்காட்சி (Preview):**")
                        st.dataframe(df_final.head(5))
                        
                        st.download_button(
                            label="📥 பிரிக்கப்பட்ட எக்ஸ்ெல் கோப்பைப் பதிவிறக்கு (Download Flat Excel)",
                            data=processed_data,
                            file_name=f"Formatted_{uploaded_file.name.rsplit('.', 1)[0]}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            use_container_width=True
                        )
                    else:
                        st.warning("⚠️ PDF வடிவமைப்பைப் பிரிக்க இயலவில்லை. வரிகளின் அமைப்பைச் சரிபார்க்கவும்.")
                        
                except Exception as e:
                    st.error(f"❌ பிழை: {e}")

if __name__ == "__main__":
    show_pdf_to_excel_page()
