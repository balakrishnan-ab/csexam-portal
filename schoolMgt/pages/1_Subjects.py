import streamlit as st
from supabase import create_client, Client
import pandas as pd

# 1. Supabase இணைப்பு
url: str = st.secrets["SUPABASE_URL"]
key: str = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

st.set_page_config(page_title="Subjects Management", layout="wide")
st.title("📚 பாடங்கள் மேலாண்மை (Supabase)")

# ⚡ தரவை வேகமெடுக்க
@st.cache_data(ttl=60)
def fetch_subjects():
    try:
        # இப்போது subject_code படி வரிசைப்படுத்துகிறோம்
        response = supabase.table("subjects").select("*").order("subject_code").execute()
        return response.data
    except Exception as e:
        st.error(f"தொடர்பு பிழை: {e}")
        return []

# 2. புதிய பாடம் சேர்க்கும் படிவம்
with st.form("add_subject_form", clear_on_submit=True):
    st.subheader("🆕 புதிய பாடம்")
    col1, col2, col3 = st.columns([1, 2, 2])
    scode = col1.text_input("Code", placeholder="001").strip()
    sname = col2.text_input("பாடம் பெயர்").upper().strip()
    etype = col3.selectbox("மதிப்பீட்டு முறை", ["90 + 10", "70 + 20 + 10","100","60+40"])
    
    if st.form_submit_button("💾 பாடத்தைச் சேமி"):
        if scode and sname:
            try:
                supabase.table("subjects").insert({
                    "subject_code": scode, 
                    "subject_name": sname, 
                    "eval_type": etype
                }).execute()
                st.success(f"பாடம் '{sname}' சேர்க்கப்பட்டது!")
                st.cache_data.clear()
                st.rerun()
            except Exception as e:
                st.error(f"பிழை: {e}")
        else:
            st.warning("Code மற்றும் பெயர் இரண்டையும் உள்ளிடவும்.")

st.divider()

# 3. பாடங்கள் பட்டியல்
subjects_data = fetch_subjects()

if subjects_data:
    df = pd.DataFrame(subjects_data)
    
    st.subheader("📋 பாடங்கள் பட்டியல்")
    # அட்டவணையில் காட்ட வேண்டிய காலம்கள்
    display_df = df[['subject_code', 'subject_name', 'eval_type']].copy()
    display_df.columns = ['Code', 'பாடத்தின் பெயர்', 'மதிப்பீட்டு முறை']
    st.dataframe(display_df, use_container_width=True, hide_index=True)

    st.divider()

    # 4. திருத்துதல் மற்றும் நீக்குதல்
    st.subheader("⚙️ மேலாண்மை")
    sub_list = df['subject_name'].tolist()
    selected_sub = st.selectbox("பாடத்தைத் தேர்வு செய்க:", ["-- தேர்வு செய்க --"] + sub_list)

    if selected_sub != "-- தேர்வு செய்க --":
        row = df[df['subject_name'] == selected_sub].iloc[0]
        
        col1, col2 = st.columns(2)
        with col1:
            new_name = st.text_input("பெயர் மாற்று:", value=row['subject_name']).upper()
            new_etype = st.selectbox("முறை மாற்று:", ["90 + 10", "70 + 20 + 10"], 
                                   index=0 if row['eval_type'] == "90 + 10" else 1)
            
            if st.button("🆙 இற்றைப்படுத்து (Update)"):
                supabase.table("subjects").update({
                    "subject_name": new_name, 
                    "eval_type": new_etype
                }).eq("subject_code", row['subject_code']).execute()
                st.success("மாற்றப்பட்டது!")
                st.cache_data.clear()
                st.rerun()

        with col2:
            st.write("⚠️ நீக்க வேண்டுமா?")
            if st.button(f"❌ {selected_sub}-ஐ நீக்கு", type="primary"):
                supabase.table("subjects").delete().eq("subject_code", row['subject_code']).execute()
                st.warning("நீக்கப்பட்டது!")
                st.cache_data.clear()
                st.rerun()
else:
    st.info("பாடங்கள் இன்னும் சேர்க்கப்படவில்லை.")
