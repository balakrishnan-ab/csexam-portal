import streamlit as st
import pdfplumber
import pandas as pd
import re

# பக்கத்தின் அமைப்பினை அகலமாக மாற்றுதல் (Wide Mode)
st.set_page_config(layout="wide")

st.title("அரசு மேல்நிலைப்பள்ளி - தேவனாங்குறிச்சி")
st.subheader("10-ஆம் வகுப்பு பொதுத்தேர்வு மதிப்பெண் பகுப்பாய்வு")

# 1. PDF கோப்பைப் பதிவேற்றம் செய்தல்
uploaded_file = st.file_uploader("பள்ளி வாரியான SSLC PDF கோப்பைப் பதிவேற்றவும்", type=["pdf"])

def extract_data_from_pdf(pdf_file):
    students_list = []
    
    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if not text:
                continue
                
            # ஒவ்வொரு வரியாகப் பிரித்து மாணவர் விவரங்களை எடுத்தல்
            lines = text.split('\n')
            
            # குறிப்பு: உங்கள் PDF அமைப்பைப் பொறுத்து இந்த Regex மற்றும் லூப் மாறுபடலாம்.
            # இது ஒரு மாதிரி வடிவமைப்பு மட்டுமே.
            for i, line in enumerate(lines):
                # 7 இலக்க ரோல் நம்பர் உள்ளதா எனச் சரிபார்த்தல்
                if re.match(r'^\d{7}', line):
                    parts = line.split()
                    roll_no = parts[0]
                    
                    # பெயரைக் கண்டறிதல் (ஆங்கில எழுத்துக்கள் மட்டும்)
                    name_parts = [p for p in parts[2:] if p.isalpha()]
                    name = " ".join(name_parts)
                    
                    # மதிப்பெண்கள் மற்றும் தேர்ச்சி விவரம் (P/W அல்லது காலியாக இருந்தால் Fail)
                    # உங்கள் PDF தரவுகளுக்கு ஏற்ப மாற்றி அமைக்க வேண்டும்
                    result = "Pass" if " P " in line or line.endswith("P") else "Fail"
                    
                    # தற்காலிகமாக ஒரு மாதிரித் தரவைச் சேர்த்தல்
                    students_list.append({
                        "Roll No": roll_no,
                        "Name": name,
                        "Result": result,
                        "Total": int(parts[-2]) if parts[-2].isdigit() else 0
                    })
    
    return pd.DataFrame(students_list)

if uploaded_file is not None:
    # PDF-லிருந்து தரவுகளைப் பிரித்தெடுத்தல்
    df = extract_data_from_pdf(uploaded_file)
    
    if not df.empty:
        # 2. முக்கிய புள்ளிவிவரங்களைக் கணக்கிடுதல்
        total_candidates = len(df)
        passed_candidates = len(df[df["Result"] == "Pass"])
        failed_candidates = total_candidates - passed_candidates
        pass_percentage = (passed_candidates / total_candidates) * 100 if total_candidates > 0 else 0
        
        # 3. படத்தில் உள்ளது போன்ற மெட்ரிக்ஸ் (Metrics) கட்டங்கள்
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            st.metric(label="TOTAL (மொத்தம்)", value=total_candidates)
        with col2:
            st.metric(label="PRESENT (வருகை)", value=total_candidates) # ஆப்சென்ட் விவரம் இருந்தால் கழிக்கலாம்
        with col3:
            st.metric(label="PASS (தேர்ச்சி)", value=passed_candidates)
        with col4:
            st.metric(label="FAIL (தோல்வி)", value=failed_candidates)
        with col5:
            st.metric(label="PASS % (தேர்ச்சி சதவீதம்)", value=f"{pass_percentage:.2f}%")
            
        st.markdown("---")
        
        # 4. முழுமையான மதிப்பெண் பட்டியல் (Table)
        st.subheader("📋 முழுமையான மதிப்பெண் பட்டியல்")
        st.dataframe(df, use_container_width=True)
        
    else:
        st.error("PDF-லிருந்து விவரங்களைச் சரியாகப் பிரித்தெடுக்க முடியவில்லை. வடிவமைப்பைச் சரிபார்க்கவும்.")
