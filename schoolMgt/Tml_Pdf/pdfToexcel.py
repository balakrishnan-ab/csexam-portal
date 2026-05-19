import pdfplumber
import pandas as pd

def pdf_to_excel(pdf_path, excel_path):
    try:
        # PDF கோப்பைத் திறக்கவும்
        with pdfplumber.open(pdf_path) as pdf:
            # Excel கோப்பை உருவாக்க ExcelWriter-ஐப் பயன்படுத்தவும்
            with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
                table_count = 0
                
                # PDF-ன் ஒவ்வொரு பக்கத்தையும் வரிசையாக ஆய்வு செய்யவும்
                for page_num, page in enumerate(pdf.pages, start=1):
                    # பக்கத்தில் உள்ள அட்டவணைகளைப் பிரித்தெடுக்கவும்
                    tables = page.extract_tables()
                    
                    for table_idx, table in enumerate(tables, start=1):
                        table_count += 1
                        # தரவை Pandas DataFrame ஆக மாற்றவும்
                        df = pd.DataFrame(table)
                        
                        # Excel தாளின் பெயர் (அதிகபட்சம் 31 எழுத்துக்கள் இருக்க வேண்டும்)
                        sheet_name = f"Page_{page_num}_Table_{table_idx}"
                        
                        # எக்ஸ்ெல் கோப்பில் தனித்தனி தாள்களாக (Sheets) சேமிக்கவும்
                        df.to_excel(writer, sheet_name=sheet_name[:31], index=False, header=False)
                
                # PDF-ல் அட்டவணைகள் எதுவும் இல்லை என்றால் உரையாக (Text) மாற்றும் முறை
                if table_count == 0:
                    print("PDF-ல் எந்த அட்டவணையும் (Tables) கண்டறியப்படவில்லை. உரையை (Text) மட்டும் எக்ஸ்ெல்லுக்கு மாற்றுகிறது...")
                    extract_text_to_excel(pdf, writer)
                else:
                    print(f"வெற்றிகரமாக {table_count} அட்டவணைகள் Excel கோப்பில் சேமிக்கப்பட்டன!")
                    
    except Exception as e:
        print(f"பிழை ஏற்பட்டது: {e}")

def extract_text_to_excel(pdf, writer):
    text_data = []
    # ஒவ்வொரு பக்கத்தில் உள்ள உரையை வரிகளாகப் பிரித்தல்
    for page in pdf.pages:
        text = page.extract_text()
        if text:
            for line in text.split('\n'):
                text_data.append([line])
                
    # தரவை எக்ஸ்ெல் கோப்பாகச் சேமித்தல்
    df = pd.DataFrame(text_data, columns=["PDF Content"])
    df.to_excel(writer, sheet_name="PDF Text", index=False)
    print("PDF-ல் உள்ள உரை Excel கோப்பாக மாற்றப்பட்டது.")

# --- நிரலை இயக்கும் முறை ---
# உங்கள் PDF கோப்பின் பெயரை இங்கே குறிப்பிடவும்
pdf_file_name = "sample.pdf"  

# உருவாக்கப்பட வேண்டிய Excel கோப்பின் பெயர்
excel_file_name = "output_file.xlsx"  

# செயல்பாட்டைத் தொடங்கவும்
pdf_to_excel(pdf_file_name, excel_file_name)
