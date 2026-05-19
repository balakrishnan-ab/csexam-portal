import streamlit as st
import pdfplumber
import pandas as pd
import io

def show_pdf_to_excel_page():
    # பக்கத்தின் முக்கிய தலைப்புகள் (Custom CSS உடன் பள்ளி நிறங்களுக்கு ஏற்ப)
    st.markdown("""
        <style>
        .main-title {
            font-size:28px !important;
            font-weight: bold;
            color: #1E3A8A;
            text-align: center;
            margin-bottom: 20px;
        }
        .sub-text {
            font-size:16px !important;
            color: #4B5563;
            text-align: center;
            margin-bottom: 30px;
        }
        </style>
        """, unsafe_allow_html=True)
    
    st.markdown('<p class="main-title">📊 PDF to Excel மாற்றி (Tml pdf Anlysis)</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-text">பள்ளித் தரவுகள், மதிப்பெண் பட்டியல்கள் அல்லது அட்டவணைகள் அடங்கிய PDF கோப்புகளை எளிதாக எக்ஸ்ெல் (Excel) கோப்பாக மாற்றிக் கொள்ளலாம்.</p>', unsafe_allow_html=True)
    
    st.divider() # ஒரு கோடு மூலம் பிரித்தல்

    # இரண்டு பத்திகளாகப் பிரித்து UI-ஐ அழகாக்குதல்
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # கோப்பைப் பதிவேற்றும் பகுதி
        uploaded_file = st.file_uploader(
            "மாற்ற வேண்டிய PDF கோப்பைத் தேர்ந்தெடுக்கவும் (Drag and Drop PDF here)", 
            type=["pdf"],
            key="pdf_uploader"
        )
    
    with col2:
        # சிறிய வழிகாட்டி குறிப்பு
        st.info("""
        💡 **குறிப்பு:**
        * PDF-ல் அட்டவணைகள் (Tables) இருந்தால், அவை எக்ஸ்ெல்லில் தனித்தனி ஷீட்களாக (Sheets) மாறும்.
        * வெறும் வரிகள் (Text) மட்டும் இருந்தால், அவை வரிசையாக எக்ஸ்ெல்லில் சேமிக்கப்படும்.
        """)

    # கோப்பு பதிவேற்றப்பட்ட பின் நடக்கும் செயல்பாடுகள்
    if uploaded_file is not None:
        st.success("✅ PDF கோப்பு வெற்றிகரமாகப் பதிவேற்றப்பட்டது!")
        
        # கோப்பை மாற்றுவதற்கான பொத்தான்
        if st.button("மாற்றத்தைத் தொடங்கு (Convert to Excel)", type="primary"):
            
            # லோடிங் அனிமேஷன் (Spinner)
            with st.spinner("PDF கோப்பு பகுப்பாய்வு செய்யப்பட்டு எக்ஸ்ெல்லாக மாற்றப்படுகிறது... தயவுசெய்து காத்திருக்கவும்..."):
                try:
                    # PDF கோப்பை நினைவகத்தில் படிக்க BytesIO பயன்பாடு
                    pdf_bytes = io.BytesIO(uploaded_file.read())
                    
                    with pdfplumber.open(pdf_bytes) as pdf:
                        # எக்ஸ்ெல் கோப்பை தற்காலிக நினைவகத்தில் (Buffer) உருவாக்க
                        excel_buffer = io.BytesIO()
                        
                        # ExcelWriter அமைப்பு
                        with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
                            table_count = 0
                            
                            # ஒவ்வொரு பக்கமாக ஆய்வு செய்தல்
                            for page_num, page in enumerate(pdf.pages, start=1):
                                tables = page.extract_tables()
                                
                                for table_idx, table in enumerate(tables, start=1):
                                    table_count += 1
                                    
                                    # தரவை DataFrame ஆக மாற்றுதல்
                                    df = pd.DataFrame(table)
                                    
                                    # காலியாக உள்ள வரிசைகளை நீக்குதல் (Data Cleaning)
                                    df.dropna(how='all', inplace=True)
                                    
                                    # எக்ஸ்ெல் தாளின் பெயர் (அதிகபட்சம் 31 எழுத்துக்கள்)
                                    sheet_name = f"Page_{page_num}_Table_{table_idx}"
                                    df.to_excel(writer, sheet_name=sheet_name[:31], index=False, header=False)
                            
                            # PDF-ல் அட்டவணைகள் எதுவும் இல்லையெனில் உரையாக (Text) மாற்றுதல்
                            if table_count == 0:
                                text_data = []
                                for page in pdf.pages:
                                    text = page.extract_text()
                                    if text:
                                        for line in text.split('\n'):
                                            if line.strip(): # காலியான வரிகளைத் தவிர்த்தல்
                                                text_data.append([line.strip()])
                                
                                df = pd.DataFrame(text_data, columns=["PDF Content / Text"])
                                df.to_excel(writer, sheet_name="PDF Text Content", index=False)
                        
                        # எக்ஸ்ெல் பைனரி தரவை தயார் செய்தல்
                        processed_data = excel_buffer.getvalue()
                        
                        st.balloons() # வெற்றிகரமாக முடிந்ததும் பலூன் அனிமேஷன்
                        st.subheader("🎉 செயல்முறை வெற்றிகரமாக முடிந்தது!")
                        
                        # முடிவுகளைக் காட்டுதல்
                        c1, c2 = st.columns(2)
                        if table_count > 0:
                            c1.metric(label="கண்டறியப்பட்ட அட்டவணைகள்", value=f"{table_count} Tables")
                        else:
                            c1.metric(label="கண்டறியப்பட்ட தரவு வகை", value="Plain Text / உரை")
                            
                        c2.metric(label="மொத்த பக்கங்கள்", value=f"{len(pdf.pages)} Pages")
                        
                        st.markdown("### 📥 கோப்பைப் பதிவிறக்கம் செய்ய கீழே உள்ள பொத்தானைக் கிளிக் செய்யவும்:")
                        
                        # மாற்றி அமைக்கப்பட்ட கோப்பை டவுன்லோட் செய்ய வைக்கும் பொத்தான்
                        st.download_button(
                            label="🟢 Excel கோப்பைப் பதிவிறக்கு (Download Excel)",
                            data=processed_data,
                            file_name=f"Converted_{uploaded_file.name.rsplit('.', 1)[0]}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            use_container_width=True
                        )
                        
                except Exception as e:
                    st.error(f"❌ கோப்பை மாற்றுவதில் பிழை ஏற்பட்டுள்ளது: {e}")
                    st.info("குறிப்பு: உங்கள் PDF கோப்பு ஸ்கேன் செய்யப்பட்ட படமாக (Scanned Image) இருந்தால் தரவை பிரித்தெடுப்பதில் சிரமம் ஏற்படலாம்.")

# உங்கள் முதன்மை கோப்பில் (Main App) இயக்குவதற்காக இந்த பங்க்ஷனை அழைக்க வேண்டும்
if __name__ == "__main__":
    show_pdf_to_excel_page()
