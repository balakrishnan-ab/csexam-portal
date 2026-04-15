import streamlit as st
import pandas as pd
from supabase import create_client, Client

# --- 1. SUPABASE CONNECTION ---
try:
    url: str = st.secrets["SUPABASE_URL"]
    key: str = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(url, key)
except Exception as e:
    st.error("Secrets-ல் Supabase விவரங்கள் சரியாக இல்லை!")
    st.stop()

st.set_page_config(page_title="Teacher Registry", layout="wide")
st.title("👨‍🏫 ஆசிரியர் விவரங்கள் மேலாண்மை (Teacher Registry)")

# --- ⚡ FETCH DATA (Caching) ---

@st.cache_data(ttl=60)
def fetch_subjects_list():
    """பாடங்கள் அட்டவணையில் இருந்து பாடப் பெயர்களை மட்டும் எடுக்கும்"""
    try:
        response = supabase.table("subjects").select("subject_name").order("subject_name").execute()
        return [item['subject_name'] for item in response.data]
    except Exception:
        return []

@st.cache_data(ttl=60)
def fetch_teachers():
    """ஆசிரியர்கள் பட்டியலை எடுக்கும்"""
    try:
        response = supabase.table("teachers").select("*").order("full_name").execute()
        return response.data
    except Exception:
        return []

# தேவையான தரவுகளைப் பெறுதல்
available_subjects = fetch_subjects_list()

# --- 2. புதிய ஆசிரியரைப் பதிவு செய்தல் ---
with st.form("add_teacher_form", clear_on_submit=True):
    st.subheader("🆕 புதிய ஆசிரியரைப் பதிவு செய்தல்")
    
    col1, col2 = st.columns(2)
    with col1:
        e_id = st.text_input("EMIS ID", placeholder="11 இலக்க எண்", max_chars=11)
        f_name = st.text_input("முழுப் பெயர் (Full Name)")
        s_name = st.text_input("சுருக்கப் பெயர் (Short Name)")
    
    with col2:
        desig = st.selectbox("பதவி (Designation)", 
                             ["HM", "PG Assistant", "BT Assistant", "Computer Instructor", "SG Teacher", "PET"])
        
        # பாடங்கள் அட்டவணையில் இருந்து பெறப்பட்ட பட்டியல்
        if available_subjects:
            sub = st.selectbox("முதன்மைப் பாடம் (Subject)", available_subjects)
        else:
            sub = st.text_input("பாடம் (குறிப்பு: பாடங்கள் அட்டவணையில் தரவு இல்லை)")

    if st.form_submit_button("💾 விவரங்களைச் சேமி"):
        if e_id and f_name and s_name and sub:
            try:
                supabase.table("teachers").insert({
                    "emis_id": e_id,
                    "full_name": f_name.upper(),
                    "short_name": s_name.upper(),
                    "designation": desig,
                    "subject": sub
                }).execute()
                
                st.success(f"✅ '{s_name.upper()}' விவரங்கள் சேமிக்கப்பட்டது!")
                st.cache_data.clear()
                st.rerun()
            except Exception as e:
                st.error(f"பிழை: {e}")
        else:
            st.warning("அனைத்து விவரங்களையும் பூர்த்தி செய்யவும்.")

st.divider()

# --- 3. ஆசிரியர்கள் பட்டியல் ---
teachers_data = fetch_teachers()

if teachers_data:
    st.subheader(f"📋 ஆசிரியர்கள் பட்டியல் ({len(teachers_data)})")
    df_teachers = pd.DataFrame(teachers_data)
    
    display_df = df_teachers[['emis_id', 'full_name', 'short_name', 'designation', 'subject']]
    display_df.columns = ['EMIS ID', 'முழுப் பெயர்', 'சுருக்கப் பெயர்', 'பதவி', 'பாடம்']
    
    st.dataframe(display_df, use_container_width=True, hide_index=True)

    st.divider()

    # --- 4. நீக்குதல் மேலாண்மை ---
    st.subheader("🗑️ விவரங்களை நீக்க")
    teacher_options = {f"{t['short_name']} - {t['full_name']}": t['id'] for t in teachers_data}
    selected_label = st.selectbox("ஆசிரியரைத் தேர்வு செய்க:", ["-- தேர்வு செய்க --"] + list(teacher_options.keys()))
    
    if selected_label != "-- தேர்வு செய்க --":
        t_uuid = teacher_options[selected_label]
        if st.button(f"❌ {selected_label}-ஐ நீக்கு", type="primary"):
            supabase.table("teachers").delete().eq("id", t_uuid).execute()
            st.warning("விவரங்கள் நீக்கப்பட்டது!")
            st.cache_data.clear()
            st.rerun()
else:
    st.info("ஆசிரியர்கள் விவரம் இன்னும் சேர்க்கப்படவில்லை.")
