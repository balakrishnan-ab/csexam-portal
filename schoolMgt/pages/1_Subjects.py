import streamlit as st
from supabase import create_client, Client
import pandas as pd

# 1. Supabase இணைப்பு தகவல்கள்
# உங்கள் Streamlit Secrets-ல் SUPABASE_URL மற்றும் SUPABASE_KEY இருப்பதை உறுதி செய்யவும்
try:
 #   url: str = st.secrets["SUPABASE_URL"]
    url: str = st.secrets["SUPABASE_URL"].strip()
    key: str = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(url, key)
except Exception as e:
    st.error("Secrets-ல் Supabase தகவல்கள் இல்லை. தயவுசெய்து சரிபார்க்கவும்.")
    st.stop()

st.set_page_config(page_title="Subjects Management", layout="wide")
st.title("📚 பாடங்கள் மேலாண்மை (Supabase)")

# ⚡ தரவை வேகமெடுக்க (Caching)
@st.cache_data(ttl=60)
def fetch_subjects():
    try:
        # 'subjects' டேபிளில் இருந்து அனைத்து பாடங்களையும் பெயர்வாரியாக எடுக்கும்
        response = supabase.table("subjects").select("*").order("subject_name").execute()
        return response.data
    except Exception as e:
        st.error(f"தரவைப் பெறுவதில் சிக்கல்: {e}")
        return []

# 2. புதிய பாடம் சேர்க்கும் படிவம்
with st.form("add_subject_form", clear_on_submit=True):
    st.subheader("🆕 புதிய பாடம்")
    name = st.text_input("பாடம் பெயர் (எ.கா: TAMIL)").upper().strip()
    etype = st.selectbox("மதிப்பீட்டு முறை", ["90 + 10", "70 + 20 + 10"])
    
    if st.form_submit_button("💾 பாடத்தைச் சேமி"):
        if name:
            try:
                # Supabase-ல் தகவலைச் சேர்த்தல்
                supabase.table("subjects").insert({
                    "subject_name": name, 
                    "eval_type": etype
                }).execute()
                
                st.success(f"பாடம் '{name}' வெற்றிகரமாகச் சேர்க்கப்பட்டது!")
                st.cache_data.clear() # பழைய Cache-ஐ நீக்க
                st.rerun() # திரையைப் புதுப்பிக்க
            except Exception as e:
                # பிழை எதனால் வருகிறது என்பதைத் துல்லியமாகக் காட்ட
                error_msg = str(e)
                if "duplicate key value" in error_msg:
                    st.error(f"பிழை: '{name}' என்ற பாடம் ஏற்கனவே பட்டியலில் உள்ளது!")
                else:
                    st.error(f"பதிவு செய்வதில் பிழை: {error_msg}")
        else:
            st.warning("தயவுசெய்து பாடத்தின் பெயரை உள்ளிடவும்.")

st.divider()

# 3. பாடங்கள் பட்டியல்
subjects_data = fetch_subjects()

if subjects_data:
    df = pd.DataFrame(subjects_data)
    
    st.subheader("📋 பாடங்கள் பட்டியல்")
    # பயனருக்குத் தேவையான காலம்களை மட்டும் அழகான அட்டவணையாகக் காட்டுதல்
    display_df = df[['subject_name', 'eval_type']].copy()
    display_df.columns = ['பாடத்தின் பெயர்', 'மதிப்பீட்டு முறை']
    st.table(display_df)

    st.divider()

    # 4. திருத்துதல் மற்றும் நீக்குதல் (Edit & Delete)
    st.subheader("⚙️ பாடத்தை மாற்றியமைக்க / நீக்க")
    
    sub_names = df['subject_name'].tolist()
    selected_sub = st.selectbox("மேலாண்மை செய்ய வேண்டிய பாடம்:", ["-- தேர்வு செய்க --"] + sub_names)

    if selected_sub != "-- தேர்வு செய்க --":
        # தேர்ந்தெடுக்கப்பட்ட பாடத்தின் தற்போதைய தகவல்கள்
        row = df[df['subject_name'] == selected_sub].iloc[0]
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("#### 🆙 திருத்து (Update)")
            new_name = st.text_input("புதிய பெயர்:", value=row['subject_name']).upper().strip()
            new_etype = st.selectbox("புதிய மதிப்பீட்டு முறை:", ["90 + 10", "70 + 20 + 10"], 
                                   index=0 if row['eval_type'] == "90 + 10" else 1)
            
            if st.button("நிச்சயமாக மாற்று"):
                try:
                    supabase.table("subjects").update({
                        "subject_name": new_name, 
                        "eval_type": new_etype
                    }).eq("id", row['id']).execute()
                    
                    st.success("வெற்றிகரமாக மாற்றப்பட்டது!")
                    st.cache_data.clear()
                    st.rerun()
                except Exception as e:
                    st.error(f"மாற்றுவதில் பிழை: {e}")

        with col2:
            st.markdown("#### ❌ நீக்கு (Delete)")
            st.info(f"பாடம்: **{selected_sub}**")
            confirm_del = st.checkbox(f"நான் இப்பாடத்தை நீக்க ஒப்புக்கொள்கிறேன்")
            if confirm_del:
                if st.button(f"உறுதியாக நீக்கு", type="primary"):
                    try:
                        supabase.table("subjects").delete().eq("id", row['id']).execute()
                        st.warning("பாடம் நீக்கப்பட்டது!")
                        st.cache_data.clear()
                        st.rerun()
                    except Exception as e:
                        st.error(f"நீக்குவதில் பிழை: {e}")
else:
    st.info("பாடங்கள் இன்னும் சேர்க்கப்படவில்லை. மேலேயுள்ள படிவத்தைப் பயன்படுத்தி முதல் பாடத்தைச் சேர்க்கவும்.")
