import streamlit as st
import pandas as pd
from supabase import create_client

# --- Supabase இணைப்பு ---
def get_supabase_client():
    if "supabase_instance" not in st.session_state:
        st.session_state.supabase_instance = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
    return st.session_state.supabase_instance

supabase = get_supabase_client()

st.set_page_config(page_title="Class Report", layout="wide")

# ⚡ தடிமனான எழுத்துக்களுக்கான CSS
st.markdown("<style>.stDataFrame { font-size: 16px !important; font-weight: bold !important; }</style>", unsafe_allow_html=True)

st.title("📂 வகுப்பு வாரியான ஒருங்கிணைந்த மதிப்பெண் அறிக்கை")

# --- 1. அடிப்படைத் தரவுகள் ---
exams = supabase.table("exams").select("*").execute().data
all_classes = supabase.table("classes").select("*").execute().data
all_subjects = supabase.table("subjects").select("*").execute().data

# --- 2. வடிகட்டிகள் ---
c1, c2 = st.columns(2)
sel_exam = c1.selectbox("1. தேர்வைத் தேர்ந்தெடுக்கவும்:", [e['exam_name'] for e in exams])
class_names = sorted(list(set([c.get('class_n') or c.get('class_name') for c in all_classes])))
sel_class = c2.selectbox("2. வகுப்பைத் தேர்ந்தெடுக்கவும்:", class_names)

if sel_exam and sel_class:
    exam_id = next(e['id'] for e in exams if e['exam_name'] == sel_exam)
    
    # அ. அந்த வகுப்பில் உள்ள மாணவர்கள்
    students = supabase.table("exam_mapping").select("exam_no, student_name, emis_no").eq("exam_id", exam_id).eq("class_name", sel_class).order("exam_no").execute().data
    
    # ஆ. அந்த தேர்வில் உள்ள அனைத்து மதிப்பெண்கள்
    marks_data = supabase.table("marks").select("*").eq("exam_id", exam_id).execute().data
    
    if not students:
        st.warning("⚠️ இந்த வகுப்பில் மாணவர்கள் யாரும் இல்லை.")
    else:
        # இ. டேட்டாபிரேம் தயாரித்தல்
        report_list = []
        # அனைத்து பாடங்களின் பெயர்களையும் தலைப்பாக எடுக்க
        sub_list = sorted(list(set([s['subject_name'] for s in all_subjects])))
        
        for s in students:
            row = {"தேர்வு எண்": s['exam_no'], "மாணவர் பெயர்": s['student_name']}
            total_sum = 0
            absent_count = 0
            
            for sub in all_subjects:
                sub_name = sub['subject_name']
                sub_code = sub['subject_code']
                
                # அந்த மாணவர், அந்தப் பாடத்தில் எடுத்த மதிப்பெண்
                m = next((m for m in marks_data if m['emis_no'] == s['emis_no'] and m['subject_id'] == sub_code), None)
                
                if m:
                    if m.get('is_absent'):
                        row[sub_name] = "ABS"
                        absent_count += 1
                    else:
                        row[sub_name] = m.get('total_mark', 0)
                        total_sum += m.get('total_mark', 0)
                else:
                    row[sub_name] = "-" # மதிப்பெண் இன்னும் பதிவிடப்படவில்லை
            
            row["மொத்தம்"] = total_sum
            report_list.append(row)
        
        df_report = pd.DataFrame(report_list)
        
        # ⚡ 3. அட்டவணையைக் காட்டுதல்
        st.divider()
        st.subheader(f"📊 {sel_class} - {sel_exam} மதிப்பெண் பட்டியல்")
        
        # ரேங்க் வரிசைப்படுத்துதல் (மொத்த மதிப்பெண் அடிப்படையில்)
        df_report = df_report.sort_values(by="மொத்தம்", ascending=False).reset_index(drop=True)
        df_report.index += 1
        df_report.index.name = "தரம் (Rank)"
        
        st.dataframe(df_report, use_container_width=True)
        
        # ⚡ 4. எக்செல் தரவிறக்கம் (Download)
        st.divider()
        csv = df_report.to_csv(index=True).encode('utf-8-sig')
        st.download_button(
            label="📥 எக்செல் கோப்பாக தரவிறக்கம் செய் (Excel Download)",
            data=csv,
            file_name=f"{sel_class}_{sel_exam}_Report.csv",
            mime="text/csv",
        )
