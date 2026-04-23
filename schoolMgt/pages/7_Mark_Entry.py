import streamlit as st
import pandas as pd
from supabase import create_client
from io import BytesIO

# --- Supabase இணைப்பு ---
def get_supabase_client():
    if "supabase_instance" not in st.session_state:
        st.session_state.supabase_instance = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
    return st.session_state.supabase_instance

supabase = get_supabase_client()

st.set_page_config(page_title="Mark Entry", layout="wide")
st.title("📊 மதிப்பெண் பதிவேற்றம் & திருத்தம்")

# தரவுகள் பெறுதல்
exams = supabase.table("exams").select("*").eq("exam_status", "Active").execute().data
all_classes = supabase.table("classes").select("*").execute().data
all_subjects = supabase.table("subjects").select("*").execute().data

# 1. தேர்வு மற்றும் வகுப்புத் தேர்வு
c1, c2 = st.columns(2)
sel_exam_name = c1.selectbox("தேர்வு:", ["-- தேர்வு செய்க --"] + [e['exam_name'] for e in exams])

if sel_exam_name != "-- தேர்வு செய்க --":
    exam_id = next(e['id'] for e in exams if e['exam_name'] == sel_exam_name)
    class_names = [c.get('class_n') or c.get('class_name') for c in all_classes]
    sel_class = c2.selectbox("வகுப்பு:", ["-- தேர்வு செய்க --"] + sorted(class_names))

    if sel_class != "-- தேர்வு செய்க --":
        st.divider()
        st.subheader("📥 வகுப்பு ஆசிரியர் பகுதி: ஒட்டுமொத்த பதிவேற்றம்")

        # அந்த வகுப்பிற்குரிய மாணவர் மற்றும் தேர்வு எண் பட்டியல்
        mapping_data = supabase.table("exam_mapping").select("exam_no, emis_no, student_name").eq("exam_id", exam_id).eq("class_name", sel_class).execute().data
        df_students = pd.DataFrame(mapping_data)

        if not df_students.empty:
            # கோப்பிற்கான Template தயாரித்தல்
            df_template = df_students.copy()
            # பாடங்களை இணைத்தல் (ஒவ்வொரு பாடத்திற்கும் Theory, Internal)
            for sub in all_subjects:
                s_name = sub['subject_name']
                df_template[f"Theory_{s_name}"] = ""
                df_template[f"Internal_{s_name}"] = ""
            
            # எக்செல் டவுன்லோட் பட்டன்
            output = BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df_template.to_excel(writer, index=False, sheet_name='Marks_Entry')
            
            st.download_button(
                label="📥 மாணவர் பட்டியல் மற்றும் தேர்வு எண்ணுடன் கோப்பைத் தரவிறக்கு",
                data=output.getvalue(),
                file_name=f"Marks_Entry_{sel_class}_{sel_exam_name}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

            st.divider()
            st.info("பூர்த்தி செய்த கோப்பைப் பதிவேற்றவும்:")
            uploaded_file = st.file_uploader("Excel கோப்பு", type=["xlsx"])

            if uploaded_file:
                df_upload = pd.read_excel(uploaded_file)
                if st.button("🚀 அனைத்து மதிப்பெண்களையும் தரவுத்தளத்தில் சேமி"):
                    bulk_list = []
                    for _, row in df_upload.iterrows():
                        emis = str(row['emis_no'])
                        for col in df_upload.columns:
                            if "_" in col:
                                parts = col.split("_")
                                m_type = parts[0] # Theory / Internal
                                s_name = parts[1]
                                s_info = next((s for s in all_subjects if s['subject_name'] == s_name), None)
                                
                                if s_info:
                                    val = int(row[col]) if pd.notnull(row[col]) else 0
                                    # List-ல் ஏற்கனவே உள்ளதா எனப் பார்த்து அப்டேட் செய்தல்
                                    item = next((i for i in bulk_list if i['emis_no'] == emis and i['subject_id'] == s_info['subject_code']), None)
                                    if not item:
                                        item = {"exam_id": exam_id, "emis_no": emis, "subject_id": s_info['subject_code'], "theory_mark": 0, "internal_mark": 0, "total_mark": 0}
                                        bulk_list.append(item)
                                    
                                    if m_type == "Theory": item["theory_mark"] = val
                                    elif m_type == "Internal": item["internal_mark"] = val
                                    item["total_mark"] = item["theory_mark"] + item["internal_mark"]
                    
                    supabase.table("marks").upsert(bulk_list, on_conflict="exam_id, emis_no, subject_id").execute()
                    st.success("✅ மதிப்பெண்கள் வெற்றிகரமாகச் சேமிக்கப்பட்டன!")
        else:
            st.warning("இந்த வகுப்பிற்கு இன்னும் தேர்வு எண்கள் ஒதுக்கப்படவில்லை.")
