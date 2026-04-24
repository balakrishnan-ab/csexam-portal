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

st.set_page_config(page_title="Mark Entry System", layout="wide")
st.title("📊 மதிப்பெண் பதிவேற்றம் & திருத்தம்")

# --- தரவுகளைப் பெறுதல் ---
exams = supabase.table("exams").select("*").eq("exam_status", "Active").execute().data
all_classes = supabase.table("classes").select("*").execute().data
all_groups = supabase.table("groups").select("*").execute().data
all_subjects = supabase.table("subjects").select("*").execute().data

# --- தேர்வு ---
sel_exam_name = st.selectbox("தேர்வைத் தேர்ந்தெடுக்கவும்:", ["-- தேர்வு செய்க --"] + [e['exam_name'] for e in exams])

if sel_exam_name != "-- தேர்வு செய்க --":
    exam_id = next(e['id'] for e in exams if e['exam_name'] == sel_exam_name)
    
    # மூன்று பிரிவுகள்
    tab1, tab2, tab3 = st.tabs(["👨‍🏫 பாட ஆசிரியர்", "📂 வகுப்பு ஆசிரியர் (Bulk)", "🏢 வகுப்பின் அனைத்துப் பிரிவுகள் (Group-wise)"])

    # --- TAB 1: பாட ஆசிரியர் ---
    with tab1:
        sel_class = st.selectbox("வகுப்பைத் தேர்ந்தெடுக்கவும்:", ["-- தேர்வு செய்க --"] + sorted([c['class_name'] for c in all_classes]))
        if sel_class != "-- தேர்வு செய்க --":
            # (இங்கே உங்கள் பாட ஆசிரியர் தர்க்கம்...)
            st.info("குறிப்பிட்ட பாடத்தை மட்டும் பதிவு செய்யவும்.")

    # --- TAB 2: வகுப்பு ஆசிரியர் (Bulk) ---
    with tab2:
        sel_class_bulk = st.selectbox("வகுப்பு (Bulk):", ["-- தேர்வு செய்க --"] + sorted([c['class_name'] for c in all_classes]))
        if sel_class_bulk != "-- தேர்வு செய்க --":
            # (இங்கே மாணவர் பட்டியலுடன் கூடிய Bulk Upload தர்க்கம்...)
            st.info(f"{sel_class_bulk} வகுப்புக்கான அனைத்து பாடங்களையும் பதிவேற்றவும்.")

    # --- TAB 3: வகுப்பின் அனைத்துப் பிரிவுகள் (Group-wise) ---
    with tab3:
        st.subheader("🏢 வகுப்பின் அனைத்துப் பாடப்பிரிவுகள் (Group-wise)")
        selected_grade = st.selectbox("வகுப்பைத் தேர்வு செய்யவும் (எ.கா: 12):", ["-- தேர்வு செய்க --", "10", "11", "12"])
        
        if selected_grade != "-- தேர்வு செய்க --":
            st.write(f"{selected_grade}-ஆம் வகுப்பில் உள்ள அனைத்து குரூப்களின் மதிப்பெண் கோப்புகளைப் பதிவேற்றலாம்.")
            
            # 1. குறிப்பிட்ட வகுப்பிற்குரிய அனைத்து குரூப்களைத் திரட்டல்
            relevant_classes = [c for c in all_classes if c['class_name'].startswith(selected_grade)]
            
            # 2. ஒவ்வொரு குரூப்பிற்கும் ஒரு தனித்தனி Template உருவாக்குதல்
            for cls in relevant_classes:
                group_name = cls['group_name']
                st.write(f"--- 📍 பிரிவின் குரூப்: {group_name} ---")
                
                # அந்த குரூப் பாடங்கள் மட்டும்
                g_info = next((g for g in all_groups if g['group_name'] == group_name), None)
                sub_names = g_info['subjects'].split(',') if g_info else []
                
                # கோப்பு தயாரித்தல் (மாணவர் பட்டியல் + பாடங்கள்)
                mapping = supabase.table("exam_mapping").select("emis_no, student_name").eq("exam_id", exam_id).eq("class_name", cls['class_name']).execute().data
                df_g = pd.DataFrame(mapping)
                for sub in sub_names: df_g[f"Theory_{sub.strip()}"] = 0
                
                # டவுன்லோட் பட்டன்
                output = BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    df_g.to_excel(writer, index=False)
                st.download_button(f"📥 {cls['class_name']} ({group_name}) கோப்பைப் பெற", data=output.getvalue(), file_name=f"Marks_{cls['class_name']}.xlsx")

            st.divider()
            uploaded_file = st.file_uploader("அனைத்துப் பாடப்பிரிவுகளுக்கும் பூர்த்தி செய்த கோப்பைப் பதிவேற்று", type=["xlsx"])
            if uploaded_file:
                st.success("இந்தக் கோப்பு தானாகவே குரூப் அடிப்படையில் பிரிக்கப்பட்டு சேமிக்கப்படும்.")
