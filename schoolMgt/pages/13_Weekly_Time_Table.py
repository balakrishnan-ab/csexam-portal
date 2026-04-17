import streamlit as st
import pandas as pd
from supabase import create_client, Client

# --- 1. SUPABASE CONNECTION ---
try:
    url: str = st.secrets["SUPABASE_URL"]
    key: str = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(url, key)
except Exception as e:
    st.error("Secrets விவரங்கள் சரியாக இல்லை!")
    st.stop()

st.set_page_config(page_title="Weekly Time Table", layout="wide", page_icon="📅")

# --- ⚡ FETCH DATA ---
@st.cache_data(ttl=60)
def fetch_base_data():
    classes = supabase.table("classes").select("class_name").order("class_name").execute()
    # ஒதுக்கீடு செய்யப்பட்ட ஆசிரியர்களை மட்டும் எடுக்கிறோம்
    allotments = supabase.table("staff_allotment").select("*").execute()
    return [c['class_name'] for c in classes.data], allotments.data

class_list, allotment_data = fetch_base_data()

st.title("📅 வாராந்திர கால அட்டவணை உருவாக்கம்")

# --- 📋 SELECTION ---
col1, col2 = st.columns(2)
with col1:
    selected_class = st.selectbox("வகுப்பைத் தேர்வு செய்க:", ["-- Select --"] + class_list)

if selected_class != "-- Select --":
    # அந்த வகுப்புக்கு ஒதுக்கப்பட்ட ஆசிரியர்கள் மற்றும் பாடங்கள்
    class_staff = [a for a in allotment_data if a['class_name'] == selected_class]
    
    if not class_staff:
        st.warning(f"இந்த வகுப்பிற்கு ({selected_class}) இன்னும் ஆசிரியர்கள் ஒதுக்கப்படவில்லை. Staff Allotment பக்கம் செல்லவும்.")
    else:
        st.subheader(f"🏫 {selected_class} - கால அட்டவணை அமைப்பு")
        
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
        periods = range(1, 9) # 1 முதல் 8 பீரியட்கள்
        
        # அட்டவணை வடிவம் (Grid)
        for day in days:
            st.markdown(f"#### {day}")
            cols = st.columns(8)
            for p in periods:
                with cols[p-1]:
                    # அந்தப் பீரியடிற்கு ஏற்கனவே யாராவது ஒதுக்கப்பட்டுள்ளார்களா எனப் பார்க்க (Database Fetch தேவை)
                    st.button(f"P{p}", key=f"{day}_{p}_{selected_class}", use_container_width=True)

st.info("குறிப்பு: இது தொடக்க நிலை மட்டுமே. அடுத்ததாக, ஒரு பட்டனை அழுத்தினால் ஆசிரியரைத் தேர்வு செய்யும் 'Popup' வசதியைச் சேர்ப்போம்.")
