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

# --- ⚡ FETCH DATA FUNCTIONS ---

# பாடங்கள் அட்டவணையில் இருந்து பாடங்களை எடுக்க
@st.cache_data(ttl=60)
def fetch_subjects_list():
    try:
        # subjects அட்டவணையில் இருந்து அனைத்து பாடங்களையும் எடுத்தல்
        response = supabase.table("subjects").select("subject_name").order("subject_name").execute()
        # பாடப் பெயர்களை மட்டும் ஒரு பட்டியலாக (List) மாற்றுதல்
        return [item['subject_name'] for item in response.data]
    except Exception as e:
        return ["Tamil", "English", "Maths"] # பிழை ஏற்பட்டால் அடிப்படை பாடங்கள்

@st.cache_data(ttl=60)
def fetch_teachers():
    try:
        response = supabase.table("teachers").select("*").order("full_name").execute()
        return response.data
    except Exception as e:
        return []

# --- UI START ---
st.title("👨‍🏫 ஆசிரியர் விவரங்கள் மேலாண்மை")

# பாடங்களின் பட்டியலைப் பெறுதல்
available_subjects = fetch_subjects_list()

# --- 2. ADD NEW TEACHER FORM ---
with st.form("add_teacher_form", clear_on_submit=True):
    st.subheader("🆕 புதிய ஆசிரியரைப் பதிவு செய்தல்")
    
    col1, col2 = st.columns(2)
    
    with col1:
        e_id = st.text_input("EMIS ID", max_chars=11)
        f_name = st.text_input("முழுப் பெயர் (Full Name)")
        s_name = st.text_input("சுருக்கப் பெயர் (Short Name)")
    
    with col2:
        desig = st.selectbox("பதவி (Designation)", 
                             ["HM", "PG Assistant", "BT Assistant", "Computer Instructor", "SG Teacher", "PET"])
        
        # முக்கிய மாற்றம்: இங்கே பாடங்கள் subjects table-ல் இருந்து வருகின்றன
        sub = st.selectbox("முதன்மைப் பாடம் (Subject)", available_subjects)

    if st.form_submit_button("💾 விவரங்களைச் சேமி"):
        if e_id and f_name and s_name:
            try:
                supabase.table("teachers").insert({
                    "emis_id": e_id,
                    "full_name": f_name.upper(),
                    "short_name": s_name.upper(),
                    "designation": desig,
                    "subject": sub
                }).execute()
                
                st.success(f"✅ '{s_name.upper()}' சேமிக்கப்பட்டது!")
                st.cache_data.clear()
                st.rerun()
            except Exception as e:
                st.error(f"பிழை: {e}")
        else:
            st.warning("அனைத்து விவரங்களையும் உள்ளிடவும்.")

# --- 3. DISPLAY & DELETE SECTION (முந்தைய குறியீட்டில் உள்ளது போல...) ---
# ... (பட்டியல் காட்டும் பகுதி)
