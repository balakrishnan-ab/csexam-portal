import re
import pdfplumber
import pandas as pd

def clean_timetable_pdf(pdf_path, output_csv_path):
    all_data = []
    current_class = "Unknown"
    
    # வார நாட்களின் சுருக்கம் (இதைக் கொண்டு புதிய வரிகளைக் கண்டறியலாம்)
    days_match = ['Mo', 'Tu', 'We', 'Th', 'Fr']
    
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if not text:
                continue
                
            lines = text.split('\n')
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # வகுப்பின் பெயரைக் கண்டறிதல் (உதாரணம்: 12-A, 11-B, 10-C)
                class_check = re.search(r'\b\d{1,2}-[A-D1]{1,2}\b', line)
                if class_check:
                    current_class = class_check.group()
                    continue
                
                # வரியானது ஒரு வார நாளில் தொடங்குகிறதா என்று பார்த்தல்
                tokens = line.split()
                if tokens and tokens[0] in days_match:
                    day = tokens[0]
                    
                    # மீதமுள்ள பாடவேளைத் தரவுகளைச் சுத்தப்படுத்துதல்
                    periods_raw = tokens[1:]
                    periods = []
                    
                    # இரண்டு எழுத்து குறியீடுகளை இணைத்தல் (உதாரணம்: 'E', 'MA' -> 'E MA')
                    i = 0
                    while i < len(periods_raw):
                        if i + 1 < len(periods_raw) and len(periods_raw[i]) <= 3 and len(periods_raw[i+1]) <= 3:
                            periods.append(f"{periods_raw[i]} {periods_raw[i+1]}")
                            i += 2
                        else:
                            periods.append(periods_raw[i])
                            i += 1
                    
                    # ஒவ்வொரு நாளும் சரியாக 8 பாடவேளைகள் இருப்பதை உறுதி செய்தல்
                    while len(periods) < 8:
                        periods.append("")
                    periods = periods[:8] # 8-க்கு மேல் இருந்தால் கவாத்து செய்தல்
                    
                    # இறுதித் தரவுப் பட்டியலில் சேர்த்தல்
                    all_data.append([current_class, day] + periods)

    # தரவுகளை DataFrame-ஆக மாற்றி CSV கோப்பில் எழுதுதல்
    columns = ["Class", "Day", "P1", "P2", "P3", "P4", "P5", "P6", "P7", "P8"]
    df = pd.DataFrame(all_data, columns=columns)
    
    # ஒவ்வொரு வகுப்புக்கும் சரியாக 5 வரிகள் (Mo முதல் Fr வரை) இருப்பதை உறுதி செய்ய வடிகட்டுதல்
    df = df[df['Day'].isin(days_match)]
    
    # CSV கோப்பாகச் சேமித்தல்
    df.to_csv(output_csv_path, index=False, encoding='utf-8-sig')
    print(f"வெற்றிகரமாக CSV கோப்பு உருவாக்கப்பட்டது: {output_csv_path}")

# நிரலை இயக்குதல்
# 'time table 2026 class.pdf' என்ற கோப்பை உள்ளீடாகக் கொடுக்கவும் 
pdf_filename = "time table 2026 class.pdf" 
output_csv = "cleaned_timetable.csv"

clean_timetable_pdf(pdf_filename, output_csv)
