import streamlit as st
import pandas as pd
from supabase import create_client, Client

# --- 1. Supabase இணைப்பு (பிழை வராமல் இருக்க Session State பயன்படுத்துகிறோம்) ---
def get_supabase_client():
    if "supabase_instance" not in st.session_state:
        try:
            url: str = st.secrets["SUPABASE_URL"]
            key: str = st.secrets["SUPABASE_KEY"]
            st.session_state.supabase_instance = create_client(url, key)
        except Exception as e:
            st.error(f"Supabase இணைப்பு பிழை: {e}")
            return None
    return st.session_state.supabase_instance

supabase = get_supabase_client()

st.set_page_config(page_title="Roll No Generator", layout="wide")
st.title("🔢 தேர்வு எண் உருவாக்கம் (Roll No Generator)")

# ⚡ தரவுகளைப் பெறும் செயல்பாடுகள்
def fetch_exams():
    if supabase:
        res = supabase.table("exams").select("*").execute()
        return res.data
    return []

def fetch_students():
    if supabase:
        res = supabase.table("students").select("*").execute()
        return res.data
    return []

# --- பிரதான பகுதி ---
if not supabase:
    st.stop()

exams_list = fetch_exams()
students_list = fetch_students()

if not exams_list:
    st.warning("⚠️ முதலில் '5_Exam_Creation' பக்கத்தில் ஒரு தேர்வை உருவாக்கவும்.")
    st.stop()

# 1. தேர்வைத் தேர்ந்தெடுத்தல்
exam_options = {f"{e['exam_name']} ({e['academic_year']})": e['id'] for e in exams_list if e['exam_status'] == 'Active'}
selected_exam_label = st.selectbox("எந்தத் தேர்விற்கு எண்களை உருவாக்க வேண்டும்?", ["-- தேர்வு செய்க --"] + list(exam_options.keys()))

if selected_exam_label != "-- தேர்வு செய்க --":
    selected_exam_id = exam_options[selected_exam_label]
    
    # 2. ஏற்கனவே எண்கள் உள்ளதா எனச் சரிபார்த்தல்
    try:
        existing_res = supabase.table("exam_mapping").eq("exam_id", selected_exam_id).execute()
        existing_data = existing_res.data
    except Exception as e:
        st.error(f"அட்டவணை 'exam_mapping' கண்டறியப்படவில்லை. Supabase-ல் அட்டவணையை உருவாக்கியதை உறுதி செய்யவும். பிழை: {e}")
        st.stop()
    
    if existing_data:
        st.success(f"✅ ஏற்கனவே {len(existing_data)} மாணவர்களுக்கு எண்கள் உள்ளன.")
        df_view = pd.DataFrame(existing_data)
        st.dataframe(df_view[['exam_no', 'student_name', 'class_name', 'emis_no']].sort_values('exam_no'), use_container_width=True, hide_index=True)
        
        if st.button("♻️ பழைய எண்களை நீக்கிவிட்டு மீண்டும் உருவாக்கு"):
            supabase.table("exam_mapping").delete().eq("exam_id", selected_exam_id).execute()
            st.rerun()
    else:
        st.info("இந்தத் தேர்விற்கு இன்னும் எண்கள் ஒதுக்கப்படவில்லை.")
        
        if st.button("🚀 எண்களை உருவாக்கு (Generate Now)", type="primary"):
            if not students_list:
                st.error("மாணவர்கள் பட்டியல் இல்லை!")
            else:
                with st.spinner("வகைப்படுத்தப்படுகிறது..."):
                    df_st = pd.DataFrame(students_list)
                    
                    # வரிசைப்படுத்துதல்: Class > Gender > Name
                    # Gender: Female (F) முதலில் வர ascending=True (F < M)
                    df_st = df_st.sort_values(by=['class_name', 'gender', 'student_name'], ascending=[True, True, True])
                    
                    new_rows = []
                    for c_name in df_st['class_name'].unique():
                        c_df = df_st[df_st['class_name'] == c_name]
                        
                        # 6-A -> 6101 தர்க்கம்
                        c_num = "".join(filter(str.isdigit, c_name))
                        section = c_name.split("-")[-1].upper()
                        
                        # பிரிவு குறியீடு (A=1, B=2, C=3, D=4...)
                        s_code = 1
                        if any(x in section for x in ['A', 'அ']): s_code = 1
                        elif any(x in section for x in ['B', 'ஆ']): s_code = 2
                        elif any(x in section for x in ['C', 'இ']): s_code = 3
                        elif any(x in section for x in ['D', 'ஈ']): s_code = 4
                        
                        base = int(f"{c_num}{s_code}00")
                        
                        for i, (idx, row) in enumerate(c_df.iterrows(), 1):
                            new_rows.append({
                                "exam_id": selected_exam_id,
                                "emis_no": row['emis_no'],
                                "exam_no": base + i,
                                "class_name": c_name,
                                "student_name": row['student_name']
                            })
                    
                    try:
                        supabase.table("exam_mapping").insert(new_rows).execute()
                        st.success("வெற்றிகரமாக எண்கள் உருவாக்கப்பட்டன!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"சேமிப்பதில் பிழை: {e}")
