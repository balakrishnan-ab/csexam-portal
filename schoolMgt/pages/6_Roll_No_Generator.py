import streamlit as st
import pandas as pd
from supabase import create_client, Client

# --- Supabase இணைப்பு ---
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
st.title("📝 தேர்வு எண் மேலாண்மை (தொடர்ச்சி / தனித்தனி)")

if not supabase:
    st.error("Supabase இணைப்பு இல்லை!")
    st.stop()

# ⚡ தரவுகளைப் பெறுதல்
def fetch_data(table):
    res = supabase.table(table).select("*").execute()
    return res.data

exams_list = fetch_data("exams")
students_list = fetch_data("students")
classes_list = fetch_data("classes")

# --- 1. தேர்வு மற்றும் வகுப்புகளைத் தேர்ந்தெடுத்தல் ---
active_exams = {f"{e['exam_name']} ({e['academic_year']})": e['id'] for e in exams_list if e['exam_status'] == 'Active'}
selected_exam_label = st.selectbox("தேர்வைத் தேர்ந்தெடுக்கவும்:", ["-- தேர்வு செய்க --"] + list(active_exams.keys()))

all_class_names = sorted([c['class_name'] for c in classes_list])
sel_classes = st.multiselect("வரிசைப்படி வகுப்புகளைத் தேர்ந்தெடுக்கவும்:", all_class_names)

if selected_exam_label != "-- தேர்வு செய்க --" and sel_classes:
    selected_exam_id = active_exams[selected_exam_label]
    df_stu = pd.DataFrame(students_list)
    
    st.divider()
    
    # 🔘 ரேடியோ பட்டன் - தேர்வு எண் முறை
    mode = st.radio(
        "எண் ஒதுக்கும் முறை:",
        ["தொடர்ச்சியாக (Continuous)", "பிரிவுக்கு வேறாக (Section-wise Break)"],
        horizontal=True
    )
    
    st.subheader("🔢 எண் ஒதுக்கீடு")
    
    all_new_mappings = []
    # முதல் வகுப்பிற்கான பொதுவான ஆரம்ப எண்
    start_val = st.number_input("ஆரம்ப எண்:", min_value=1, value=1001)
    
    current_num = start_val

    for i, cls in enumerate(sel_classes):
        with st.expander(f"📍 {cls} - விபரங்கள்", expanded=True):
            
            # 'பிரிவுக்கு வேறாக' எனில் மட்டும் ஒவ்வொரு வகுப்பிற்கும் எண்களை மாற்ற அனுமதித்தல்
            if mode == "பிரிவுக்கு வேறாக (Section-wise Break)":
                current_num = st.number_input(f"{cls} ஆரம்ப எண்:", min_value=1, value=int(current_num), key=f"inp_{cls}")
            else:
                st.info(f"{cls} வகுப்பிற்கான ஆரம்ப எண்: **{current_num}** (தொடர்ச்சி)")

            f_students = df_stu[(df_stu['class_name'] == cls) & (df_stu['gender'] == 'Female')].sort_values('student_name')
            m_students = df_stu[(df_stu['class_name'] == cls) & (df_stu['gender'] == 'Male')].sort_values('student_name')
            
            # --- எண்களை ஒதுக்கும் பகுதி ---
            # மாணவிகள்
            f_s = current_num
            for _, row in f_students.iterrows():
                all_new_mappings.append({"exam_id": selected_exam_id, "emis_no": row['emis_no'], "exam_no": current_num, "class_name": cls, "student_name": row['student_name']})
                current_num += 1
            f_e = current_num - 1

            # மாணவர்கள்
            m_s = current_num
            for _, row in m_students.iterrows():
                all_new_mappings.append({"exam_id": selected_exam_id, "emis_no": row['emis_no'], "exam_no": current_num, "class_name": cls, "student_name": row['student_name']})
                current_num += 1
            m_e = current_num - 1
            
            col_f, col_m = st.columns(2)
            with col_f: st.success(f"👩‍🎓 மாணவிகள் ({len(f_students)}): {f_s}-{f_e}" if not f_students.empty else "👩‍🎓 மாணவிகள்: இல்லை")
            with col_m: st.info(f"👨‍🎓 மாணவர்கள் ({len(m_students)}): {m_s}-{m_e}" if not m_students.empty else "👨‍🎓 மாணவர்கள்: இல்லை")

    # --- இறுதிச் சேமிப்பு ---
    if all_new_mappings:
        st.divider()
        st.subheader("📋 இறுதிப் பார்வை")
        df_preview = pd.DataFrame(all_new_mappings)
        st.dataframe(df_preview[['exam_no', 'student_name', 'class_name']].sort_values('exam_no'), use_container_width=True, hide_index=True)
        
        if st.button("🚀 எண்களை உறுதி செய்து சேமி", use_container_width=True, type="primary"):
            try:
                # பழைய எண்களை நீக்கிவிட்டுப் புதியவற்றைச் சேர்த்தல்
                supabase.table("exam_mapping").delete().eq("exam_id", selected_exam_id).execute()
                supabase.table("exam_mapping").insert(all_new_mappings).execute()
                st.success("வெற்றிகரமாகச் சேமிக்கப்பட்டது!")
                st.balloons()
            except Exception as e:
                st.error(f"பிழை: {e}")
else:
    st.info("வகுப்புகளைத் தேர்ந்தெடுத்து எண்களைச் சரிபார்க்கவும்.")
