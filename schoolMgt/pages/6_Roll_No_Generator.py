import streamlit as st
import pandas as pd
from supabase import create_client, Client
from io import BytesIO

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

st.set_page_config(page_title="Roll No Generator Pro", layout="wide")
st.title("📝 தேர்வு எண் மேலாண்மை")

if not supabase:
    st.error("Supabase இணைப்பு இல்லை!")
    st.stop()

# ⚡ தரவுகளைப் பெறுதல்
@st.cache_data(ttl=600)
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
    
    # தேர்ந்தெடுக்கப்பட்ட வகுப்புகளின் மாணவர்கள் மட்டும்
    filtered_df = df_stu[df_stu['class_name'].isin(sel_classes)].sort_values(['class_name', 'gender', 'student_name'])

    st.divider()

    # --- Tabs உருவாக்கம் ---
    tab1, tab2 = st.tabs(["🔢 தானியங்கி எண் உருவாக்கம்", "📂 எக்செல் மூலம் பதிவேற்றம் (External)"])

    # --- TAB 1: Automatic Generation ---
    with tab1:
        mode = st.radio(
            "எண் ஒதுக்கும் முறை:",
            ["தொடர்ச்சியாக (Continuous)", "பிரிவுக்கு வேறாக (Section-wise Break)"],
            horizontal=True
        )
        
        all_new_mappings = []
        start_val = st.number_input("ஆரம்ப எண்:", min_value=1, value=1001, key="auto_start")
        current_num = start_val

        for cls in sel_classes:
            with st.expander(f"📍 {cls} விபரங்கள்", expanded=False):
                if mode == "பிரிவுக்கு வேறாக (Section-wise Break)":
                    current_num = st.number_input(f"{cls} ஆரம்ப எண்:", min_value=1, value=int(current_num), key=f"inp_{cls}")
                
                f_students = filtered_df[(filtered_df['class_name'] == cls) & (filtered_df['gender'] == 'Female')].sort_values('student_name')
                m_students = filtered_df[(filtered_df['class_name'] == cls) & (filtered_df['gender'] == 'Male')].sort_values('student_name')

                # எண்களை ஒதுக்குதல்
                for _, row in pd.concat([f_students, m_students]).iterrows():
                    all_new_mappings.append({
                        "exam_id": selected_exam_id, 
                        "emis_no": row['emis_no'], 
                        "exam_no": current_num, 
                        "class_name": cls, 
                        "student_name": row['student_name']
                    })
                    current_num += 1
                st.write(f"இந்த வகுப்பிற்கு ஒதுக்கப்பட்ட எண்கள்: {current_num - len(f_students) - len(m_students)} - {current_num - 1}")

        if all_new_mappings:
            if st.button("🚀 தானியங்கி எண்களைச் சேமி", use_container_width=True, type="primary"):
                try:
                    supabase.table("exam_mapping").delete().eq("exam_id", selected_exam_id).execute()
                    supabase.table("exam_mapping").insert(all_new_mappings).execute()
                    st.success("வெற்றிகரமாகச் சேமிக்கப்பட்டது!")
                    st.balloons()
                except Exception as e: st.error(f"பிழை: {e}")

    # --- TAB 2: Excel Upload ---
    with tab2:
        st.subheader("📤 எக்செல் வழிமுறை")
        st.write("1. முதலில் கீழே உள்ள பட்டனை அழுத்தி மாணவர் பட்டியலைத் தரவிறக்கவும்.")
        st.write("2. எக்செல் கோப்பில் உள்ள 'exam_no' பகுதியில் தேர்வு எண்களை நிரப்பவும்.")
        st.write("3. பின் பூர்த்தி செய்த கோப்பை இங்கே பதிவேற்றவும்.")

        # பதிவிறக்கத் தயார் செய்தல்
        df_for_download = filtered_df[['emis_no', 'student_name', 'class_name']].copy()
        df_for_download['exam_no'] = "" # காலி கட்டம்
        
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df_for_download.to_excel(writer, index=False, sheet_name='Exam_Roll_List')
        
        st.download_button(
            label="📥 மாணவர் பட்டியலை (Excel) தரவிறக்கு",
            data=output.getvalue(),
            file_name=f"Students_List_{selected_exam_label}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

        st.divider()

        uploaded_file = st.file_uploader("பூர்த்தி செய்த எக்செல் கோப்பைப் பதிவேற்றவும்", type=["xlsx"])

        if uploaded_file:
            try:
                df_upload = pd.read_excel(uploaded_file)
                st.write("பதிவேற்றப்பட்ட தரவு முன்னோட்டம்:")
                st.dataframe(df_upload.head(), use_container_width=True)

                if st.button("🚀 எக்செல் எண்களை உறுதி செய்து சேமி", type="primary", use_container_width=True):
                    # காலி எண்களை நீக்குதல்
                    df_upload = df_upload.dropna(subset=['exam_no'])
                    
                    upload_mappings = []
                    for _, row in df_upload.iterrows():
                        upload_mappings.append({
                            "exam_id": selected_exam_id,
                            "emis_no": str(row['emis_no']),
                            "exam_no": int(row['exam_no']),
                            "class_name": row['class_name'],
                            "student_name": row['student_name']
                        })

                    supabase.table("exam_mapping").delete().eq("exam_id", selected_exam_id).execute()
                    supabase.table("exam_mapping").insert(upload_mappings).execute()
                    st.success("எக்செல் தரவுகள் வெற்றிகரமாகச் சேமிக்கப்பட்டன!")
                    st.balloons()
            except Exception as e:
                st.error(f"கோப்பை வாசிப்பதில் பிழை: {e}. கோப்பில் 'emis_no' மற்றும் 'exam_no' இருப்பதை உறுதி செய்யவும்.")

else:
    st.info("மேலே தேர்வை (Exam) மற்றும் வகுப்புகளைத் (Classes) தேர்ந்தெடுக்கவும்.")
