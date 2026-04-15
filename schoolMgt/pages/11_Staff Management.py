import streamlit as st
import pandas as pd
from supabase import create_client, Client

# 1. Supabase இணைப்பு
try:
    url: str = st.secrets["SUPABASE_URL"]
    key: str = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(url, key)
except Exception as e:
    st.error("Secrets-ல் Supabase விவரங்கள் சரியாக இல்லை!")
    st.stop()

st.set_page_config(page_title="Teacher Management", layout="wide")
st.title("👨‍🏫 ஆசிரியர் மேலாண்மை (Teacher Management)")

# ⚡ தரவுகளைப் பெறுதல் (Caching)
@st.cache_data(ttl=60)
def fetch_teachers():
    try:
        response = supabase.table("teachers").select("*").order("full_name").execute()
        return response.data
    except Exception as e:
        return []

# --- 1. புதிய ஆசிரியரைச் சேர்த்தல் ---
with st.form("add_teacher_form", clear_on_submit=True):
    st.subheader("🆕 புதிய ஆசிரியரைப் பதிவு செய்தல்")
    
    col1, col2 = st.columns(2)
    with col1:
        e_id = st.text_input("EMIS ID", placeholder="11 இலக்க எண்", max_chars=11)
        name = st.text_input("முழுப் பெயர் (Full Name)")
    with col2:
        s_id = st.text_input("பள்ளி ID (School ID)")
        desig = st.selectbox("பதவி (Designation)", 
                             ["HM", "PG Assistant", "BT Assistant", "Computer Instructor", "SG Teacher"])
    
    sub = st.selectbox("முதன்மைப் பாடம் (Primary Subject)", 
                       ["Tamil", "English", "Maths", "Physics", "Chemistry", "Biology", "CS", "History", "Other"])

    if st.form_submit_button("💾 ஆசிரியரைச் சேமி"):
        if e_id and name and s_id:
            try:
                supabase.table("teachers").insert({
                    "emis_id": e_id,
                    "school_id": s_id,
                    "full_name": name,
                    "designation": desig,
                    "subject": sub
                }).execute()
                
                st.success(f"'{name}' அவர்களின் விவரங்கள் சேமிக்கப்பட்டது!")
                st.cache_data.clear()
                st.rerun()
            except Exception as e:
                st.error(f"பிழை: {e}")
        else:
            st.warning("அனைத்து கட்டாய விவரங்களையும் பூர்த்தி செய்யவும்.")

st.divider()

# --- 2. ஆசிரியர்கள் பட்டியல் ---
teachers_data = fetch_teachers()

if teachers_data:
    st.subheader("📋 ஆசிரியர்கள் பட்டியல்")
    df_teachers = pd.DataFrame(teachers_data)
    
    # காலம்களைத் தெளிவாகக் காட்டுதல்
    display_df = df_teachers[['emis_id', 'school_id', 'full_name', 'designation', 'subject']]
    display_df.columns = ['EMIS ID', 'School ID', 'ஆசிரியர் பெயர்', 'பதவி', 'பாடம்']
    
    st.dataframe(display_df, use_container_width=True, hide_index=True)

    st.divider()

    # --- 3. ஆசிரியர் விவரங்களை நீக்குதல் ---
    st.subheader("⚙️ ஆசிரியர் விவரங்களை நிர்வகி")
    
    teacher_options = {f"{t['full_name']} ({t['emis_id']})": t['id'] for t in teachers_data}
    selected_label = st.selectbox("ஆசிரியரைத் தேர்வு செய்க:", ["-- தேர்வு செய்க --"] + list(teacher_options.keys()))
    
    if selected_label != "-- தேர்வு செய்க --":
        t_uuid = teacher_options[selected_label]
        
        if st.button(f"❌ {selected_label}-ஐ நீக்கு", type="primary"):
            supabase.table("teachers").delete().eq("id", t_uuid).execute()
            st.error("விவரங்கள் நீக்கப்பட்டது!")
            st.cache_data.clear()
            st.rerun()
else:
    st.info("ஆசிரியர்கள் இன்னும் பதிவு செய்யப்படவில்லை.")
