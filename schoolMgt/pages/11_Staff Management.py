import streamlit as st
import pandas as pd
from supabase import create_client, Client

# --- 1. SUPABASE CONNECTION ---
try:
    # streamlit/secrets.toml-ல் உள்ள விவரங்களைப் பயன்படுத்துகிறது
    url: str = st.secrets["SUPABASE_URL"]
    key: str = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(url, key)
except Exception as e:
    st.error("❌ Secrets-ல் Supabase விவரங்கள் சரியாக இல்லை! .streamlit/secrets.toml கோப்பைச் சரிபார்க்கவும்.")
    st.stop()

# --- PAGE CONFIG ---
st.set_page_config(page_title="Teacher Registry", layout="wide", page_icon="👨‍🏫")
st.title("👨‍🏫 ஆசிரியர் விவரங்கள் மேலாண்மை (Teacher Registry)")

# --- ⚡ FETCH DATA (Caching for Performance) ---
@st.cache_data(ttl=60)
def fetch_teachers():
    try:
        # பெயரின் அடிப்படையில் வரிசைப்படுத்தி (Alphabetical Order) தரவுகளை எடுத்தல்
        response = supabase.table("teachers").select("*").order("full_name").execute()
        return response.data
    except Exception as e:
        st.error(f"தரவுகளை எடுப்பதில் பிழை: {e}")
        return []

# --- 2. ADD NEW TEACHER FORM ---
with st.form("add_teacher_form", clear_on_submit=True):
    st.subheader("🆕 புதிய ஆசிரியரைப் பதிவு செய்தல்")
    
    col1, col2 = st.columns(2)
    
    with col1:
        e_id = st.text_input("EMIS ID", placeholder="11 இலக்க எண்", max_chars=11)
        f_name = st.text_input("முழுப் பெயர் (Full Name)", placeholder="எ.கா: BALAKRISHNAN A")
        s_name = st.text_input("சுருக்கப் பெயர் (Short Name)", placeholder="எ.கா: A. BALA")
    
    with col2:
        desig = st.selectbox("பதவி (Designation)", 
                             ["HM", "PG Assistant", "BT Assistant", "Computer Instructor", "SG Teacher", "PET"])
        sub = st.selectbox("முதன்மைப் பாடம் (Subject)", 
                           ["Tamil", "English", "Maths", "Physics", "Chemistry", "Biology", "Computer Science", "History", "Geography", "Economics", "Other"])

    submit_btn = st.form_submit_button("💾 விவரங்களைச் சேமி")

    if submit_btn:
        if e_id and f_name and s_name:
            try:
                # தரவுதளத்தில் சேர்த்தல்
                supabase.table("teachers").insert({
                    "emis_id": e_id,
                    "full_name": f_name.upper(),
                    "short_name": s_name.upper(),
                    "designation": desig,
                    "subject": sub
                }).execute()
                
                st.success(f"✅ '{s_name.upper()}' அவர்களின் விவரங்கள் வெற்றிகரமாகச் சேமிக்கப்பட்டது!")
                st.cache_data.clear() # பழைய கேச் தரவை நீக்க
                st.rerun() # பக்கத்தைப் புதுப்பிக்க
            except Exception as e:
                st.error(f"❌ பிழை: EMIS ID ஏற்கனவே பதிவாகியிருக்கலாம் அல்லது தரவுதள இணைப்புச் சிக்கல். ({e})")
        else:
            st.warning("⚠️ தயவுசெய்து EMIS ID, முழுப் பெயர் மற்றும் சுருக்கப் பெயரைத் தவறாமல் உள்ளிடவும்.")

st.divider()

# --- 3. DISPLAY TEACHERS LIST ---
teachers_data = fetch_teachers()

if teachers_data:
    st.subheader(f"📋 ஆசிரியர்கள் பட்டியல் ({len(teachers_data)})")
    
    # DataFrame-ஆக மாற்றுதல்
    df_teachers = pd.DataFrame(teachers_data)
    
    # காட்ட வேண்டிய காலம்கள் மற்றும் அவற்றின் தமிழ் பெயர்கள்
    display_df = df_teachers[['emis_id', 'full_name', 'short_name', 'designation', 'subject']]
    display_df.columns = ['EMIS ID', 'முழுப் பெயர்', 'சுருக்கப் பெயர்', 'பதவி', 'பாடம்']
    
    # அட்டவணையாகக் காட்டுதல்
    st.dataframe(display_df, use_container_width=True, hide_index=True)

    st.divider()

    # --- 4. MANAGE / DELETE TEACHERS ---
    st.subheader("⚙️ விவரங்களை நீக்க (Delete)")
    
    # பெயர் மற்றும் EMIS ஐடியை வைத்துத் தேடுதல்
    teacher_options = {f"{t['short_name']} - {t['full_name']} ({t['emis_id']})": t['id'] for t in teachers_data}
    selected_label = st.selectbox("நீக்க வேண்டிய ஆசிரியரைத் தேர்வு செய்க:", 
                                     ["-- தேர்வு செய்க --"] + list(teacher_options.keys()))
    
    if selected_label != "-- தேர்வு செய்க --":
        t_uuid = teacher_options[selected_label]
        
        if st.button(f"🗑️ {selected_label}-ஐ நீக்கு", type="primary"):
            try:
                supabase.table("teachers").delete().eq("id", t_uuid).execute()
                st.warning(f"⚠️ {selected_label} நீக்கப்பட்டது.")
                st.cache_data.clear()
                st.rerun()
            except Exception as e:
                st.error(f"நீக்குவதில் பிழை ஏற்பட்டது: {e}")
else:
    st.info("ℹ️ ஆசிரியர்கள் விவரம் இன்னும் சேர்க்கப்படவில்லை. மேலே உள்ள படிவத்தைப் பயன்படுத்திச் சேர்க்கவும்.")

# --- FOOTER ---
st.sidebar.markdown("---")
st.sidebar.info("💡 **குறிப்பு:** பெயர்கள் அனைத்தும் தானாகவே பெரிய எழுத்துக்களில் (CAPITAL LETTERS) சேமிக்கப்படும்.")
