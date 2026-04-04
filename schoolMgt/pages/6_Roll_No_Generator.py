import streamlit as st
import pandas as pd
from supabase import create_client, Client

# --- 1. Supabase இணைப்பு ---
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

if not supabase:
    st.stop()

# ⚡ தரவுகளைப் பெறும் செயல்பாடுகள்
def fetch_exams():
    res = supabase.table("exams").select("*").execute()
    return res.data

def fetch_students():
    res = supabase.table("students").select("*").execute()
    return res.data

exams_list = fetch_exams()
students_list = fetch_students()

if not exams_list:
    st.warning("⚠️ முதலில் ஒரு தேர்வை உருவாக்கவும்.")
    st.stop()

# 1. தேர்வைத் தேர்ந்தெடுத்தல்
exam_options = {f"{e['exam_name']} ({e['academic_year']})": e['id'] for e in exams_list if e['exam_status'] == 'Active'}
selected_exam_label = st.selectbox("தேர்வைத் தேர்ந்தெடுக்கவும்:", ["-- தேர்வு செய்க --"] + list(exam_options.keys()))

if selected_exam_label != "-- தேர்வு செய்க --":
    selected_exam_id = exam_options[selected_exam_label]
    
    # 🔍 பிழை திருத்தப்பட்ட பகுதி: முதலில் select() செய்துவிட்டு அப்புறம் eq() செய்ய வேண்டும்
    try:
        existing_res = supabase.table("exam_mapping").select("*").eq("exam_id", selected_exam_id).execute()
        existing_data = existing_res.data
    except Exception as e:
        st.error(f"பிழை: {e}")
        st.stop()
    
    if existing_data:
        st.success(f"✅ ஏற்கனவே {len(existing_data)} பேருக்கு எண்கள் உள்ளன.")
        df_view = pd.DataFrame(existing_data)
        st.dataframe(df_view[['exam_no', 'student_name', 'class_name', 'emis_no']].sort_values('exam_no'), use_container_width=True, hide_index=True)
        
        if st.button("♻️ எண்களை நீக்கிவிட்டு மீண்டும் உருவாக்கு"):
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
                    df_st = df_st.sort_values(by=['class_name', 'gender', 'student_name'], ascending=[True, True, True])
                    
                    new_rows = []
                    for c_name in df_st['class_name'].unique():
                        c_df = df_st[df_st['class_name'] == c_name]
                        
                        # வகுப்பு எண் பிரித்தல் (எ.கா: 11-A -> 11)
                        import re
                        c_num_match = re.search(r'\d+', c_name)
                        c_num = c_num_match.group() if c_num_match else "0"
                        
                        section = c_name.split("-")[-1].upper()
                        s_code = 1
                        if any(x in section for x in ['A', 'அ']): s_code = 1
                        elif any(x in section for x in ['B', 'ஆ']): s_code = 2
                        elif any(x in section for x in ['C', 'இ']): s_code = 3
                        elif any(x in section for x in ['D', 'ஈ']): s_code = 4
                        
                        base = int(f"{c_num}{s_code}00")
                        
                        for i, (idx, row) in enumerate(c_df.iterrows(), 1):
                            new_rows.append({
                                "exam_id": selected_exam_id,
                                "emis_no": str(row['emis_no']),
                                "exam_no": int(base + i),
                                "class_name": str(c_name),
                                "student_name": str(row['student_name'])
                            })
                    
                    try:
                        supabase.table("exam_mapping").insert(new_rows).execute()
                        st.success("வெற்றிகரமாக எண்கள் உருவாக்கப்பட்டன!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"சேமிப்பதில் பிழை: {e}")
