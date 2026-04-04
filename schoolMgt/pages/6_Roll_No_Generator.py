import streamlit as st
import pandas as pd
from supabase import create_client, Client

# 1. Supabase இணைப்பு - இதைச் சரியாகச் சரிபார்க்கவும்
try:
    if "supabase" not in st.session_state:
        url: str = st.secrets["SUPABASE_URL"]
        key: str = st.secrets["SUPABASE_KEY"]
        st.session_state.supabase = create_client(url, key)
    supabase = st.session_state.supabase
except Exception as e:
    st.error(f"Supabase உடன் இணைக்க முடியவில்லை: {e}")
    st.stop()

st.set_page_config(page_title="Roll No Generator", layout="wide")
st.title("🔢 தேர்வு எண் உருவாக்கம் (Roll No Generator)")

# ⚡ தரவுகளைப் பெறுதல்
def fetch_data(table_name):
    res = supabase.table(table_name).select("*").execute()
    return res.data

# --- தரவுகளைத் தயார் செய்தல் ---
exams = fetch_data("exams")
students = fetch_data("students")

if not exams:
    st.warning("⚠️ முதலில் '5_Exam_Creation' பக்கத்தில் ஒரு தேர்வை உருவாக்கவும்.")
    st.stop()

# 1. தேர்வைத் தேர்ந்தெடுக்கும் பகுதி
exam_options = {f"{e['exam_name']} ({e['academic_year']})": e['id'] for e in exams if e['exam_status'] == 'Active'}
selected_exam_label = st.selectbox("எந்தத் தேர்விற்கு எண்களை உருவாக்க வேண்டும்?", ["-- தேர்வு செய்க --"] + list(exam_options.keys()))

if selected_exam_label != "-- தேர்வு செய்க --":
    selected_exam_id = exam_options[selected_exam_label]
    
    # ஏற்கனவே எண்கள் உருவாக்கப்பட்டுள்ளதா எனச் சரிபார்க்க
    existing_mapping = supabase.table("exam_mapping").eq("exam_id", selected_exam_id).execute()
    
    if existing_mapping.data:
        st.success(f"✅ இந்தத் தேர்விற்கு ஏற்கனவே {len(existing_mapping.data)} மாணவர்களுக்கு எண்கள் ஒதுக்கப்பட்டுள்ளன.")
        df_existing = pd.DataFrame(existing_mapping.data)
        st.dataframe(df_existing[['exam_no', 'student_name', 'class_name', 'emis_no']].sort_values('exam_no'), use_container_width=True, hide_index=True)
        
        if st.button("♻️ அனைத்தையும் நீக்கிவிட்டு மீண்டும் உருவாக்கு (Regenerate)", type="secondary"):
            supabase.table("exam_mapping").delete().eq("exam_id", selected_exam_id).execute()
            st.rerun()
    else:
        st.info("இந்தத் தேர்விற்கு இன்னும் எண்கள் உருவாக்கப்படவில்லை.")
        
        if st.button("🚀 தேர்வு எண்களை இப்போதே உருவாக்கு (Generate Now)", type="primary"):
            if not students:
                st.error("மாணவர்கள் பட்டியல் காலியாக உள்ளது!")
            else:
                with st.spinner("மாணவர்கள் வரிசைப்படுத்தப்பட்டு எண்கள் ஒதுக்கப்படுகின்றன..."):
                    df_st = pd.DataFrame(students)
                    
                    # 1. வரிசைப்படுத்துதல் (Class > Gender > Name)
                    # Gender: Female (F) முதலில் வர True, True, True என அமைக்கலாம்
                    df_st = df_st.sort_values(by=['class_name', 'gender', 'student_name'], ascending=[True, True, True])
                    
                    new_mappings = []
                    
                    # 2. வகுப்பு வாரியாக எண்களை ஒதுக்குதல்
                    for class_name in df_st['class_name'].unique():
                        class_df = df_st[df_st['class_name'] == class_name]
                        
                        # தர்க்கம்: 6-A -> 6101, 6-B -> 6201
                        # வகுப்பின் முதல் எண்ணை எடுத்தல் (எ.கா: 10-A இலிருந்து 10)
                        class_num = "".join(filter(str.isdigit, class_name))
                        
                        # பிரிவை எடுத்தல் (A=1, B=2, C=3...)
                        section = class_name.split("-")[-1].upper()
                        sec_code = 1 # Default
                        if 'A' in section or 'அ' in section: sec_code = 1
                        elif 'B' in section or 'ஆ' in section: sec_code = 2
                        elif 'C' in section or 'இ' in section: sec_code = 3
                        elif 'D' in section or 'ஈ' in section: sec_code = 4
                        
                        # தொடக்க எண் (எ.கா: 6 + 1 + 00 = 6100)
                        base_no = int(f"{class_num}{sec_code}00")
                        
                        for i, (idx, row) in enumerate(class_df.iterrows(), 1):
                            new_mappings.append({
                                "exam_id": selected_exam_id,
                                "emis_no": row['emis_no'],
                                "exam_no": base_no + i,
                                "class_name": class_name,
                                "student_name": row['student_name']
                            })
                    
                    # 3. Supabase-ல் மொத்தமாகச் சேர்த்தல் (Bulk Insert)
                    try:
                        # 1000 பேராகப் பிரித்து அனுப்புவது நல்லது (பெரிய தரவு எனில்)
                        supabase.table("exam_mapping").insert(new_mappings).execute()
                        st.success(f"வாழ்த்துக்கள்! {len(new_mappings)} மாணவர்களுக்குத் தேர்வு எண்கள் உருவாக்கப்பட்டன.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"சேமிப்பதில் பிழை: {e}")

else:
    st.info("மேலே உள்ள பட்டியலில் இருந்து ஒரு தேர்வைத் தேர்ந்தெடுக்கவும்.")
