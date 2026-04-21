import streamlit as st
import pandas as pd
from supabase import create_client, Client

# --- SUPABASE CONNECTION ---
try:
    url, key = st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(url, key)
except:
    st.error("Connection Error!")
    st.stop()

st.set_page_config(page_title="Timetable Balance Report", layout="wide")

st.title("📊 ஆசிரியர் மற்றும் வகுப்பு ஒதுக்கீடு சமநிலை அறிக்கை")
st.info("ஆசிரியர் ஒதுக்கீடு மற்றும் வகுப்பு தேவை சமன் செய்யப்பட்டுள்ளதா என்பதை இங்கே சரிபார்க்கவும்.")

@st.cache_data(ttl=10)
def get_reports():
    allot = supabase.table("staff_allotment").select("*").execute().data
    time_db = supabase.table("weekly_timetable").select("*").execute().data
    return allot, time_db

allot_data, time_data = get_reports()

# தரவை DataFrame-க்கு மாற்றுதல்
allot_df = pd.DataFrame(allot_data)
time_df = pd.DataFrame(time_data)

# சமநிலை அறிக்கை கணக்கீடு
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

# வடிகட்டுதல் (Filter)
status_filter = st.multiselect("நிலையைத் தேர்வு செய்க:", options=["✅ சமன்", "❌ சமமற்றது"], default=["✅ சமன்", "❌ சமமற்றது"])
filtered_df = report_df[report_df["நிலை"].isin(status_filter)]

# அறிக்கையைக் காட்டுதல்
st.dataframe(filtered_df, use_container_width=True)

# சுருக்க அறிக்கை (Summary)
col1, col2 = st.columns(2)
with col1:
    total_needed = report_df["தேவைப்பட்டவை"].sum()
    st.metric("மொத்த தேவை", total_needed)
with col2:
    total_assigned = report_df["ஒதுக்கப்பட்டது"].sum()
    st.metric("மொத்த ஒதுக்கீடு", total_assigned)

if "❌ சமமற்றது" in report_df["நிலை"].values:
    st.warning("⚠️ கவனத்திற்கு: சில ஒதுக்கீடுகள் இன்னும் சமன் செய்யப்படவில்லை! தயவுசெய்து அட்டவணைப் பக்கத்திற்குச் சென்று சரிசெய்யவும்.")
else:
    st.success("🎉 அனைத்து ஒதுக்கீடுகளும் சரியாகச் சமன் செய்யப்பட்டுள்ளன!")
