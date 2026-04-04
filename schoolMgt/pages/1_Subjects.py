import streamlit as st
from supabase import create_client, Client
import pandas as pd

# 1. Supabase இணைப்பு
url: str = st.secrets["SUPABASE_URL"]
key: str = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

st.set_page_config(page_title="Subjects Management", layout="wide")

st.title("📚 பாடங்கள் மேலாண்மை (Supabase)")

# ⚡ வேகமான தரவு சேமிப்பு (Caching)
@st.cache_data(ttl=60)
def fetch_subjects():
    try:
        response = supabase.table("subjects").select("*").order("subject_name").execute()
        return response.data
    except:
        return []

# 2. புதிய பாடம் சேர்க்கும் படிவம்
with st.form("add_subject_form", clear_on_submit=True):
    st.subheader("🆕 புதிய பாடம்")
    name = st.text_input("பாடம் பெயர்").upper().strip()
    etype = st.selectbox("மதிப்பீட்டு முறை", ["90 + 10", "70 + 20 + 10"])
    
    if st.form_submit_button("💾 பாடத்தைச் சேமி"):
        if name:
            try:
                supabase.table("subjects").insert({"subject_name": name, "eval_type": etype}).execute()
                st.success(f"பாடம் '{name}' சேர்க்கப்பட்டது!")
                st.cache_data.clear()
                st.rerun()
            except Exception as e:
                st.error("இந்தப் பெயர் ஏற்கனவே இருக்கலாம் அல்லது பிழை ஏற்பட்டுள்ளது.")
        else:
            st.warning("பாடம் பெயரை உள்ளிடவும்.")

st.divider()

# 3. பாடங்கள் பட்டியல்
subjects_data = fetch_subjects()
if subjects_data:
    df = pd.DataFrame(subjects_data)
    
    st.subheader("📋 பாடங்கள் பட்டியல்")
    # பயனருக்குத் தேவையான காலம்களை மட்டும் காட்டுதல்
    st.dataframe(df[['subject_name', 'eval_type']], use_container_width=True)

    st.divider()

    # 4. திருத்துதல் மற்றும் நீக்குதல் (Edit & Delete)
    st.subheader("⚙️ பாடத்தை மாற்றியமைக்க / நீக்க")
    
    sub_names = df['subject_name'].tolist()
    selected_sub = st.selectbox("மேலாண்மை செய்ய வேண்டிய பாடம்:", ["-- தேர்வு செய்க --"] + sub_names)

    if selected_sub != "-- தேர்வு செய்க --":
        # தேர்ந்தெடுக்கப்பட்ட பாடத்தின் விபரங்களை எடுத்தல்
        row = df[df['subject_name'] == selected_sub].iloc[0]
        
        col1, col2 = st.columns(2)
        with col1:
            new_name = st.text_input("புதிய பெயர்:", value=row['subject_name']).upper()
            new_etype = st.selectbox("புதிய மதிப்பீட்டு முறை:", ["90 + 10", "70 + 20 + 10"], 
                                   index=0 if row['eval_type'] == "90 + 10" else 1)
            
            if st.button("🆙 திருத்து (Update)"):
                supabase.table("subjects").update({
                    "subject_name": new_name, 
                    "eval_type": new_etype
                }).eq("id", row['id']).execute()
                
                st.success("மாற்றப்பட்டது!")
                st.cache_data.clear()
                st.rerun()

        with col2:
            st.write("⚠️ **எச்சரிக்கை**")
            confirm_del = st.checkbox(f"நான் '{selected_sub}' பாடத்தை நீக்க விரும்புகிறேன்")
            if confirm_del:
                if st.button(f"❌ '{selected_sub}' நீக்கு", type="primary"):
                    supabase.table("subjects").delete().eq("id", row['id']).execute()
                    st.warning("நீக்கப்பட்டது!")
                    st.cache_data.clear()
                    st.rerun()
else:
    st.info("பாடங்கள் இன்னும் சேர்க்கப்படவில்லை.")
