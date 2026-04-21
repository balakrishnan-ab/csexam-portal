import streamlit as st
import pandas as pd
from supabase import create_client, Client

# --- 1. SUPABASE CONNECTION ---
try:
    url, key = st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(url, key)
except:
    st.error("Connection Error!")
    st.stop()

st.set_page_config(page_title="Timetable Reports", layout="wide")

@st.cache_data(ttl=10)
def get_data():
    allot = supabase.table("staff_allotment").select("*").execute().data
    time_db = supabase.table("weekly_timetable").select("*").execute().data
    return allot, time_db

allot_data, time_data = get_data()
allot_df = pd.DataFrame(allot_data)
time_df = pd.DataFrame(time_data)

st.title("📊 கால அட்டவணை மற்றும் ஒதுக்கீடு அறிக்கைகள்")

# Tabs உருவாக்குதல்
tab1, tab2, tab3 = st.tabs(["👨‍🏫 ஆசிரியர் ஒதுக்கீடு", "🏫 வகுப்பு ஒதுக்கீடு", "⚖️ சமநிலை அறிக்கை"])

with tab1:
    st.subheader("ஆசிரியர் வாரியான ஒதுக்கீடு")
    # ஆசிரியரின் பெயர் மற்றும் வகுப்பைக் குழுவாக்குதல்
    teacher_group = allot_df.groupby(['teacher_name', 'class_name', 'subject_name'])['periods_per_week'].sum().reset_index()
    st.dataframe(teacher_group, use_container_width=True)

with tab2:
    st.subheader("வகுப்பு வாரியான ஒதுக்கீடு")
    # வகுப்பின் பெயர் வாரியாக குழுவாக்குதல்
    class_group = allot_df.groupby(['class_name', 'subject_name', 'teacher_name'])['periods_per_week'].sum().reset_index()
    st.dataframe(class_group, use_container_width=True)

with tab3:
    st.subheader("ஒதுக்கீடு சமநிலை அறிக்கை")
    report_data = []
    for _, row in allot_df.iterrows():
        t_id = row['teacher_id']
        cls = row['class_name']
        needed = row['periods_per_week']
        
        # உண்மையாக ஒதுக்கப்பட்ட பாடவேளைகளை எண்ணுதல்
        actual = len(time_df[(time_df['teacher_id'] == t_id) & (time_df['class_name'] == cls)])
        
        report_data.append({
            "ஆசிரியர்": row.get('teacher_name', 'Unknown'),
            "வகுப்பு": cls,
            "தேவைப்பட்டவை": needed,
            "ஒதுக்கப்பட்டது": actual,
            "நிலை": "✅ சமன்" if needed == actual else "❌ சமமற்றது"
        })
    
    report_df = pd.DataFrame(report_data)
    
    # வடிகட்டி மற்றும் அட்டவணை
    status_filter = st.multiselect("நிலையைத் தேர்வு செய்க:", options=["✅ சமன்", "❌ சமமற்றது"], default=["✅ சமன்", "❌ சமமற்றது"])
    filtered_df = report_df[report_df["நிலை"].isin(status_filter)]
    st.dataframe(filtered_df, use_container_width=True)

    # சுருக்க அறிக்கை
    col1, col2 = st.columns(2)
    with col1: st.metric("மொத்த தேவை", report_df["தேவைப்பட்டவை"].sum())
    with col2: st.metric("மொத்த ஒதுக்கீடு", report_df["ஒதுக்கப்பட்டது"].sum())
    
    if "❌ சமமற்றது" in report_df["நிலை"].values:
        st.warning("⚠️ சில ஒதுக்கீடுகள் சமன் செய்யப்படவில்லை!")
    else:
        st.success("🎉 அனைத்து ஒதுக்கீடுகளும் சரியாகச் சமன் செய்யப்பட்டுள்ளன!")
