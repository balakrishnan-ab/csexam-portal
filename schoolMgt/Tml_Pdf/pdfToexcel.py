import streamlit as st
import pdfplumber
import pandas as pd
import io
import re

def clean_cid_text(text):
    """(cid:...) குறியீடுகளை நீக்க அல்லது தற்காலிகமாகச் சீரமைக்க"""
    if not text:
        return ""
    # cid குறியீடுகளை நீக்கிவிட்டு உரையை மட்டும் சுத்தம் செய்கிறது
    cleaned = re.sub(r'\(cid:\d+\)', '', text)
    return cleaned

def parse_tml_line(line):
    """
    ஒரு வரியில் உள்ள Roll No, TMR No, Name, Sex, DOB, Marks ஆகியவற்றை 
    Regex மூலம் தனித்தனி பத்திகளாகப் பிரிக்கும் செயல்பாடு.
    """
    # மாணவர் மதிப்பெண் வரிசையைக் கண்டறியும் Regex (எ.கா: 8382429 P2366185 AAFIYA HASSIN M F 07/12/2009 T 087 094 ...)
    student_pattern = re.compile(
        r'^(\d{7})\s+'                    # Roll No (7 இலக்கங்கள்)
        r'([A-Z0-9]{8})\s+'               # TMR No (8 எழுத்து/இலக்கங்கள்)
        r'(.+?)\s+'                       # Student Name (பெயர்)
        r'([M|F])\s+'                     # Sex (M அல்லது F)
        r'([0-9]{2}/[0-9]{2}/[0-9]{4})\s+' # DOB (DD/MM/YYYY)
        r'([A-Z])\s+'                     # Language Code (T, E, etc.)
        r'(\d{3}|AAA)\s+'                 # Language Mark
        r'([E|A-Z])\s+'                   # English Code
        r'(\d{3}|AAA)\s+'                 # English Mark
        r'(\d{3}|AAA)\s+'                 # Maths Mark
        r'(\d{3}|AAA)\s+'                 # Science Mark
        r'(\d{3}|AAA)\s+'                 # Social Science Mark
        r'(\d{3}|AAA)\s+'                 # Optional Mark / Total
        r'(\d{3})\s+'                     # Total Marks
        r'([P|F|A])'                      # Result (P-Pass, F-Fail)
    )
    
    match = student_pattern.match(line.strip())
    if match:
        return {
            "Roll No": match.group(1),
            "TMR No": match.group(2),
            "Student Name": clean_cid_text(match.group(3)),
            "Sex": match.group(4),
            "DOB": match.group(5),
            "Lang Mark": match.group(7),
            "Eng Mark": match.group(9),
            "Maths Mark": match.group(10),
            "Science Mark": match.group(11),
            "Social Mark": match.group(12),
            "Total": match.group(14),
            "Result": match.group(15),
            "Type": "Student Data"
        }
    
    # பெற்றோர்கள் பெயர் மற்றும் இதர விவரங்களைச் சேகரிக்க
    if "Father's Name" in line:
        # தந்தை மற்றும் தாய் பெயரைக் கண்டறிதல்
        f_m_match = re.search(r"Father's Name\s*:\s*(.*?)\s*Mother's Name\s*:\s*(.*)", line)
        if f_m_match:
            return {
                "Father's Name": clean_cid_text(f_m_match.group(1)),
                "Mother's Name": clean_cid_text(f_m_match.group(2)),
                "Type": "Parent Data"
            }
            
    return None

def show_pdf_to_excel_page():
    st.markdown("""
        <style>
        .main-title { font-size:26px !important; font-weight: bold; color: #1E3A8A; text-align: center; }
        .sub-text { font-size:15px !important; color: #4B5563; text-align: center; margin-bottom: 20px; }
        </style>
        """, unsafe_allow_html=True)
    
    st.markdown('<p class="main-title">📊 SSLC TML PDF to Excel Converter</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-text">அரசுத் தேர்வுத் துறை TML PDF மதிப்பெண் பட்டியலை பத்திகளாக (Columns) பிரித்து எக்ஸ்ெல்லாக மாற்றும் தளம்.</p>', unsafe_allow_html=True)
    
    st.divider()

    uploaded_file = st.file_uploader("தேர்வுத் துறை TML PDF கோப்பைத் தேர்ந்தெடுக்கவும்...", type=["pdf"])

    if uploaded_file is not None:
        st.success("✅ TML PDF வெற்றிகரமாகப் பதிவேற்றப்பட்டது!")
        
        if st.button("தரவைப் பிரித்தெடு (Process & Columns Split)", type="primary"):
            with st.spinner("PDF வரிகள் பகுப்பாய்வு செய்யப்பட்டு பத்திகளாகப் பிரிக்கப்படுகின்றன..."):
                try:
                    pdf_bytes = io.BytesIO(uploaded_file.read())
                    parsed_records = []
                    
                    current_student = {}

                    with pdfplumber.open(pdf_bytes) as pdf:
                        for page in pdf.pages:
                            text = page.extract_text()
                            if text:
                                for line in text.split('\n'):
                                    data = parse_tml_line(line)
                                    
                                    if data:
                                        if data["Type"] == "Student Data":
                                            # முந்தைய மாணவர் விவரம் விடுபட்டிருந்தால் சேமிக்கவும்
                                            if current_student:
                                                parsed_records.append(current_student)
                                            current_student = data
                                        elif data["Type"] == "Parent Data" and current_student:
                                            # தற்போதைய மாணவருடன் பெற்றோர் பெயரை இணைக்கவும்
                                            current_student["Father's Name"] = data["Father's Name"]
                                            current_student["Mother's Name"] = data["Mother's Name"]
                                            parsed_records.append(current_student)
                                            current_student = {} # ரீசெட் செய்தல்

                        # கடைசி மாணவர் விவரம் இருந்தால் சேர்த்தல்
                        if current_student:
                            parsed_records.append(current_student)

                    if parsed_records:
                        # DataFrame ஆக மாற்றுதல்
                        df_final = pd.DataFrame(parsed_records)
                        
                        # தேவையற்ற 'Type' காலம்களை நீக்குதல்
                        if 'Type' in df_final.columns:
                            df_final.drop(columns=['Type'], inplace=True)
                            
                        # காலம்களை ஒழுங்குபடுத்துதல்
                        columns_order = [
                            "Roll No", "TMR No", "Student Name", "Sex", "DOB", 
                            "Father's Name", "Mother's Name", "Lang Mark", 
                            "Eng Mark", "Maths Mark", "Science Mark", "Social Mark", "Total", "Result"
                        ]
                        # இருக்கும் காலம்களை மட்டும் வரிசைப்படுத்துதல்
                        columns_order = [col for col in columns_order if col in df_final.columns]
                        df_final = df_final[columns_order]

                        # எக்ஸ்ெல் கோப்பாக மாற்றுதல்
                        excel_buffer = io.BytesIO()
                        with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
                            df_final.to_excel(writer, sheet_name="SSLC Marks", index=False)
                        
                        processed_data = excel_buffer.getvalue()
                        
                        st.balloons()
                        st.subheader("🎉 பகுப்பாய்வு நிறைவுற்றது!")
                        st.metric(label="வெற்றிகரமாகப் பிரிக்கப்பட்ட மாணவர்களின் எண்ணிக்கை", value=f"{len(df_final)} பேர்")
                        
                        # மாதிரிக்காக முதல் 5 வரிசைகளைக் காட்டுதல்
                        st.write("📊 எக்ஸ்ெல் மாதிரிக்காட்சி (Preview):")
                        st.dataframe(df_final.head())
                        
                        st.download_button(
                            label="📥 பிரிக்கப்பட்ட Excel கோப்பைப் பதிவிறக்கு (Download Processed Excel)",
                            data=processed_data,
                            file_name=f"Split_{uploaded_file.name.rsplit('.', 1)[0]}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            use_container_width=True
                        )
                    else:
                        st.warning("⚠️ PDF-ல் உள்ள வரிகளை முறையான வடிவத்தில் பிரிக்க முடியவில்லை. PDF வடிவமைப்பு மாறியிருக்கலாம்.")
                        
                except Exception as e:
                    st.error(f"❌ பிழை ஏற்பட்டது: {e}")

if __name__ == "__main__":
    show_pdf_to_excel_page()
