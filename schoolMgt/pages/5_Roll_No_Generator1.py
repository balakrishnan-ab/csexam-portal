import streamlit as st
import pandas as pd
from supabase import create_client

def get_supabase_client():
    if "supabase_instance" not in st.session_state:
        try:
            url: str = st.secrets["SUPABASE_URL"]
            key: str = st.secrets["SUPABASE_KEY"]
            st.session_state.supabase_instance = create_client(url, key)
        except: return None
    return st.session_state.supabase_instance

supabase = get_supabase_client()

st.set_page_config(page_title="Roll No Generator", layout="wide")
st.title("📝 தேர்வு எண் மற்றும் பாலின மேலாண்மை")

if not supabase:
    st.error("Supabase இணைப்பு இல்லை!")
    st.stop()

def fetch_data(table):
    res = supabase.table(table).select("*").execute()
    return res.data

exams_list = fetch_data("exams")
students_list = fetch_data("students")
classes_list = fetch_data("classes")

active_exams = {f"{e['exam_name']} ({e['academic_year']})": e['id'] for e in exams_list if e['exam_status'] == 'Active'}
selected_exam_label = st.selectbox("1. தேர்வைத் தேர்ந்தெடுக்கவும்:", ["-- தேர்வு செய்க --"] + list(active_exams.keys()))

all_class_names = sorted([c['class_name'] for c in classes_list])
sel_classes = st.multiselect("2. வரிசைப்படி வகுப்புகளைத் தேர்ந்தெடுக்கவும்:", all_class_names)

if selected_exam_label != "-- தேர்வு செய்க --":
    selected_exam_id = active_exams[selected_exam_label]
    
    # ஏற்கனவே உள்ள விவரங்கள்
    existing_data = supabase.table("exam_mapping").select("*").eq("exam_id", selected_exam_id).execute().data
    if existing_data:
        with st.expander("🔔 இந்தத் தேர்விற்கு ஏற்கனவே பதியப்பட்ட விவரங்கள்", expanded=False):
            st.dataframe(pd.DataFrame(existing_data)[['exam_no', 'student_name', 'class_name', 'gender']].sort_values('exam_no'), use_container_width=True, hide_index=True)

    if sel_classes:
        df_stu = pd.DataFrame(students_list)
        df_stu['emis_no'] = df_stu['emis_no'].astype(str).str.strip()
        df_stu['gender_clean'] = df_stu['gender'].astype(str).str.strip().str.upper()
        
        st.divider()
        mode = st.radio("எண் ஒதுக்கும் முறை:", ["தொடர்ச்சியாக (Continuous)", "பிரிவுக்கு வேறாக (Section-wise Break)"], horizontal=True)
        
        all_new_mappings = []
        start_val = st.number_input("ஆரம்ப எண்:", min_value=1, value=211001)
        current_num = start_val

        for cls in sel_classes:
            with st.expander(f"📍 {cls} - எண் ஒதுக்கீடு விபரம்", expanded=True):
                if mode == "பிரிவுக்கு வேறாக (Section-wise Break)":
                    current_num = st.number_input(f"{cls} ஆரம்ப எண்:", min_value=1, value=int(current_num), key=f"inp_{cls}")
                
                # மாணவர்களைப் பிரித்தல்
                f_students = df_stu[(df_stu['class_name'] == cls) & (df_stu['gender_clean'].str.startswith('F'))].sort_values('student_name')
                m_students = df_stu[(df_stu['class_name'] == cls) & (df_stu['gender_clean'].str.startswith('M'))].sort_values('student_name')

                # --- பெண் எண்கள் கணக்கீடு ---
                f_start = current_num if not f_students.empty else None
                for _, row in f_students.iterrows():
                    all_new_mappings.append({"exam_id": selected_exam_id, "emis_no": str(row['emis_no']), "exam_no": current_num, "class_name": cls, "student_name": row['student_name'], "gender": "Female"})
                    current_num += 1
                f_end = current_num - 1 if f_start else None

                # --- ஆண் எண்கள் கணக்கீடு ---
                m_start = current_num if not m_students.empty else None
                for _, row in m_students.iterrows():
                    all_new_mappings.append({"exam_id": selected_exam_id, "emis_no": str(row['emis_no']), "exam_no": current_num, "class_name": cls, "student_name": row['student_name'], "gender": "Male"})
                    current_num += 1
                m_end = current_num - 1 if m_start else None

                # 📊 அட்டவணை வடிவில் விபரங்களைக் காட்டுதல்
                col1, col2 = st.columns(2)
                with col1:
                    if f_start:
                        st.markdown(f"""
                        <div style="background-color: #fdf2f8; padding: 10px; border-radius: 5px; border-left: 5px solid #ec4899;">
                            <b style="color: #ec4899;">👩 பெண் (Female)</b><br>
                            எண்ணிக்கை: {len(f_students)}<br>
                            தொடக்கம்: <b>{f_start}</b> | முடிவு: <b>{f_end}</b>
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.write("பெண் மாணவர்கள் இல்லை")

                with col2:
                    if m_start:
                        st.markdown(f"""
                        <div style="background-color: #eff6ff; padding: 10px; border-radius: 5px; border-left: 5px solid #3b82f6;">
                            <b style="color: #3b82f6;">👨 ஆண் (Male)</b><br>
                            எண்ணிக்கை: {len(m_students)}<br>
                            தொடக்கம்: <b>{m_start}</b> | முடிவு: <b>{m_end}</b>
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.write("ஆண் மாணவர்கள் இல்லை")

        if all_new_mappings:
            st.divider()
            df_preview = pd.DataFrame(all_new_mappings)
            st.subheader("📋 புதிய ஒதுக்கீடு பார்வை (Preview)")
            st.dataframe(df_preview[['exam_no', 'student_name', 'class_name', 'gender']], use_container_width=True, hide_index=True)
            
            if st.button("🚀 எண்களை உறுதி செய்து சேமி", use_container_width=True, type="primary"):
                try:
                    supabase.table("exam_mapping").delete().eq("exam_id", selected_exam_id).execute()
                    supabase.table("exam_mapping").insert(all_new_mappings).execute()
                    st.success("வெற்றிகரமாகச் சேமிக்கப்பட்டது!")
                    st.balloons()
                except Exception as e:
                    st.error(f"பிழை: {e}")
