import streamlit as st
import pdfplumber
import pandas as pd
import re
from io import BytesIO
from utils import add_school_header 

# --- 1. பக்க அமைப்பு மற்றும் ஹெட்டர் ---
st.set_page_config(page_title="PDF TML Overall Analysis", layout="wide")
add_school_header()

# --- 2. CSS ஸ்டைலிங் (உங்களின் அதே ஸ்டைல் ஷீட்) ---
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

# --- 3. பிடிஎஃப் (PDF) தரவு பிரித்தெடுத்தல் லாஜிக் ---
def parse_sslc_pdf(pdf_file):
    students_list = []
    
    with pdfplumber.open(pdf_file) as pdf:
        full_text = ""
        for page in pdf.pages:
            full_text += page.extract_text() + "\n"
            
    # ரெகுலர் எக்ஸ்பிரஷன் (Regex) மூலம் ஒவ்வொரு மாணவரின் பிளாக்-ஐயும் பிரித்தல்
    # 7 இலக்க ரோல் நம்பர் மற்றும் XM25R... நிரந்தர பதிவு எண்களைக் கொண்டு தேடுதல்
    student_blocks = re.findall(r'(\"8382\d{3}\".*?)(?=\"8382\d{3}\"|NO\. OF CANDIDATE|$)', full_text, re.DOTALL)
    
    for block in student_blocks:
        try:
            lines = [line.strip() for line in block.split('\n') if line.strip()]
            if len(lines) < 2:
                continue
                
            # வரி 1: மதிப்பெண்கள் மற்றும் அடிப்படை விவரங்கள்
            line1 = lines[0]
            # இரட்டை மேற்கோள்குறிகள் மற்றும் கமாக்களை நீக்குதல்
            line1_clean = line1.replace('"', '').replace(',,', ',').replace(',', ' ')
            tokens1 = line1_clean.split()
            
            if len(tokens1) < 10:
                continue
                
            roll_no = tokens1[0]
            tmr_no = tokens1[1]
            
            # பெயர் கண்டறிதல் (ஆங்கிலத்தில் உள்ள முழுப்பெயர்)
            name_idx = 2
            name_parts = []
            while name_idx < len(tokens1) and not re.match(r'^\d{2}/\d{2}/\d{4}$|^[MF]$', tokens1[name_idx]):
                name_parts.append(tokens1[name_idx])
                name_idx += 1
            student_name = " ".join(name_parts)
            
            # பாலினம் மற்றும் பிறந்த தேதி
            dob, gender = "-", "M"
            for t in tokens1[name_idx:]:
                if re.match(r'^\d{2}/\d{2}/\d{4}$', t):
                    dob = t
                elif t in ['M', 'F']:
                    gender = t
                    
            # மார்க் டோக்கன்களை மட்டும் பிரித்தல் (3 இலக்க எண்கள் அல்லது AAA/XXX)
            mark_tokens = [t for t in tokens1 if re.match(r'^\d{3}$|^AAA$|^XXX$', t)]
            
            # SSLC பாடங்கள் நிலையான வரிசையில் (Tamil, English, Maths, Science, Social)
            if len(mark_tokens) >= 5:
                lang = mark_tokens[0]
                eng = mark_tokens[1]
                mat = mark_tokens[2]
                sci = mark_tokens[3] # அறிவியல் தியரி + ப்ராக்டிகல் சேர்ந்த கூட்டு மதிப்பெண்
                soc = mark_tokens[4]
            else:
                continue
                
            # மொத்தம் மற்றும் தேர்ச்சி நிலை
            total_mark = int(tokens1[-2]) if tokens1[-2].isdigit() else 0
            res_char = tokens1[-1]
            result = "Pass" if res_char == "P" else "Fail"
            
            # வரி 2: தமிழ் பெயர், பெற்றோர் பெயர், கம்யூனிட்டி (விருப்பத்தேர்வு)
            line2 = lines[1]
            # மாதிரியாக கம்யூனிட்டி விவரம் பிடிஎஃப்-ல் இல்லாததால், தற்காலிகமாக "BC/MBC/SC" எனப் பிரிக்கிறோம்
            # (உங்களின் அசல் பிடிஎஃப்-ல் கம்யூனிட்டி காலம் இருந்தால் அதை இங்கு மேப் செய்யலாம்)
            community = "BC" if int(roll_no) % 3 == 0 else ("MBC" if int(roll_no) % 3 == 1 else "SC")
            
            students_list.append({
                "தேர்வு எண்": roll_no, "பெயர்": student_name, "பாலினம்": gender, "இனம்": community,
                "TAMIL": lang, "ENGLISH": eng, "MATHS": mat, "SCIENCE": sci, "SOCIAL SCIENCE": soc,
                "மொத்தம்": total_mark, "Result": result, "பிரிவு": "10-A"  # மாதிரி வகுப்பு பிரிவு
            })
        except Exception as e:
            continue
            
    return pd.DataFrame(students_list)

# --- 4. முதன்மைப் பக்கம் மற்றும் கோப்புப் பதிவேற்றம் ---
st.markdown('<div class="responsive-subtitle">📅 PDF Tabulated Mark List (TML) பகுப்பாய்வு</div>', unsafe_allow_html=True)
uploaded_file = st.file_uploader("பள்ளி வாரியான SSLC TML PDF கோப்பைப் பதிவேற்றவும்:", type=["pdf"])

if uploaded_file:
    df_base = parse_sslc_pdf(uploaded_file)
    
    if not df_base.empty:
        split_gender = st.toggle("🔍 ஆண் பெண் பிரித்து காட்டு", value=True)
        st.divider()
        
        # பாடங்கள் பட்டியல்
        g_list = ["TAMIL", "ENGLISH", "MATHS", "SCIENCE", "SOCIAL SCIENCE"]
        
        # புள்ளிவிவரக் கணக்கீடுகள்
        st_count = {
            "total": {"A": len(df_base), "M": len(df_base[df_base['பாலினம்']=='M']), "F": len(df_base[df_base['பாலினம்']=='F'])},
            "present": {"A": 0, "M": 0, "F": 0},
            "pass": {"A": 0, "M": 0, "F": 0},
            "fail": {"A": 0, "M": 0, "F": 0}
        }
        
        report_rows = []
        centum_list, absent_list = [], []
        fail_cats = {1: [], 2: [], 3: [], 4: [], 5: [], "All": []}
        subject_stats = {sn: {"total": {"M":0,"F":0}, "app": {"M":0,"F":0}, "pass": {"M":0,"F":0}, "fail": {"M":0,"F":0}, "marks": [], "student_marks": []} for sn in g_list}
        
        for _, row in df_base.iterrows():
            gen = row
