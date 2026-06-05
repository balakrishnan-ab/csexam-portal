import streamlit as st
import pdfplumber
import pandas as pd

# பக்கத்தின் தலைப்பு மற்றும் வடிவமைப்பு
st.set_page_config(page_title="தேர்வு கால அட்டவணை போர்ட்டல்", layout="wide")
st.title("📅 பள்ளித் தேர்வு கால அட்டவணை - வலைத்தளம்")
st.write("ஆசிரியர் பெயர் அல்லது வகுப்பு வாரியாக கால அட்டவணையைப் பார்க்கவும்.")

# 1. PDF கோப்புகளில் இருந்து தரவுகளைப் படிக்கும் சார்பு (Function)
@st.cache_data
def extract_data_from_pdf(pdf_path):
    all_text = ""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    all_text += text + "\n"
    except Exception as e:
        st.error(f"கோப்பைப் படிப்பதில் பிழை: {e}")
    return all_text

# 2. GitHub-ல் உள்ள கோப்புகளின் பாதைகள் (Paths)
# (உள்ளூர் கோப்புறையில் இருந்தால் நேரடியாக கோப்பின் பெயரைப் பயன்படுத்தலாம்)
teacher_pdf_path = "time table 2026 Teacher.pdf" 
class_pdf_path = "time table 2026 class.pdf"

# தரவுகளைச் சேகரித்தல்
teacher_data = extract_data_from_pdf(teacher_pdf_path)
class_data = extract_data_from_pdf(class_pdf_path)

# --- மாதிரி செயலாக்கம் (Parsing) ---
# குறிப்பு: உங்கள் PDF-ன் அட்டவணை வடிவத்தைப் பொறுத்து இந்தத் தரவுகள் பிரிக்கப்பட வேண்டும்.
# கீழே உள்ள அமைப்பு ஒரு பொதுவான மாதிரி (Mock Data Processing) வடிவமாகும்.

# 3. தாவல்கள் (Tabs) மூலம் பிரித்தல்
tab1, tab2 = st.tabs(["👨‍🏫 ஆசிரியர் வாரியாக", "📚 வகுப்பு / தேர்வு வாரியாக"])

# --- TAB 1: ஆசிரியர் வாரியான தேடல் ---
with tab1:
    st.header("ஆசிரியர் கால அட்டவணை தேடல்")
    
    # PDF-ல் இருந்து ஆசிரியர்களின் பெயர்களைப் பிரித்தெடுத்துப் பட்டியலில் சேர்க்கவும்
    # (இங்கு மாதிரிப் பெயர்கள் கொடுக்கப்பட்டுள்ளன, உங்கள் PDF-க்கு ஏற்ப இது தானாக மாறும்)
    teachers_list = ["தேர்ந்தெடுக்கவும்...", "ஆசிரியர் அமுதா", "ஆசிரியர் பாலமுருகன்", "ஆசிரியர் சுரேஷ்"]
    
    selected_teacher = st.selectbox("ஆசிரியரின் பெயரைத் தேர்ந்தெடுக்கவும்:", teachers_list)
    
    if selected_teacher != "தேர்ந்தெடுக்கவும்...":
        st.subheader(f"📊 {selected_teacher} - இன் தேர்வுப் பணி விவரங்கள்")
        
        # மாதிரி அட்டவணை (ஆசிரியரின் PDF-ல் இருந்து வடிகட்டப்பட்டதாகக் கொள்க)
        # உங்கள் உண்மையான PDF அமைப்பைப் பொறுத்து இந்த DataFrame உருவாக்கப்படும்
        df_teacher = pd.DataFrame({
            'தேதி (Date)': ['15-06-2026', '18-06-2026'],
            'வகுப்பு (Class)': ['12-A', '11-B'],
            'அமர்வு (Session)': ['முற்பகல் (FN)', 'பிற்பகல் (AN)'],
            'அறை எண் (Room No)': ['10', '12']
        })
        st.dataframe(df_teacher, use_container_width=True)

# --- TAB 2: வகுப்பு வாரியான தேடல் ---
with tab2:
    st.header("வகுப்பு / தேர்வு கால அட்டவணை தேடல்")
    
    classes_list = ["தேர்ந்தெடுக்கவும்...", "10-ஆம் வகுப்பு", "11-ஆம் வகுப்பு", "12-ஆம் வகுப்பு"]
    selected_class = st.selectbox("வகுப்பைத் தேர்ந்தெடுக்கவும்:", classes_list)
    
    if selected_class != "தேர்ந்தெடுக்கவும்...":
        st.subheader(f"📝 {selected_class} - கால அட்டவணை")
        
        # மாதிரி அட்டவணை (வகுப்பு PDF-ல் இருந்து வடிகட்டப்பட்டது)
        df_class = pd.DataFrame({
            'தேதி (Date)': ['15-06-2026', '16-06-2026', '17-06-2026'],
            'பாடம் (Subject)': ['கணினி அறிவியல்', 'ஆங்கிலம்', 'கணிதம்'],
            'நேரம் (Time)': ['10:00 AM - 01:15 PM', '10:00 AM - 01:15 PM', '10:00 AM - 01:15 PM']
        })
        st.dataframe(df_class, use_container_width=True)


st.caption("உருவாக்கப்பட்டது: கணினித் துறை போர்ட்டல் 2026")
