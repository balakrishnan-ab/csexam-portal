import streamlit as st
import pandas as pd
from supabase import create_client, Client

# 1. Supabase இணைப்பு
try:
    url: str = st.secrets["SUPABASE_URL"]
    key: str = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(url, key)
except Exception as e:
    st.error("Secrets விவரங்கள் சரியாக இல்லை!")
    st.stop()

st.set_page_config(page_title="Staff Management", layout="wide")
st.title("👨‍🏫 ஆசிரியர் அடிப்படை விவரங்கள்")

# ⚡ தரவுகளைப் பெறுதல்
@st.cache_data(ttl=60)
def fetch_teachers():
    try:
        # சுருக்கப் பெயரின் அடிப்படையில் வரிசைப்படுத்துதல்
        response = supabase.table("staff_details").select("*").order("short_name").execute()
        return response.data
    except:
        return []

# --- 1. புதிய ஆசிரியரைச் சேர்த்தல் ---
with st.container(border=True):
    with st.form("add_teacher_form", clear_on_submit=True):
        st.subheader("🆕 புதிய ஆசிரியர் பதிவு")
        
        col1, col2, col3 = st.columns([2, 3, 1])
        t_id = col1.text_input("Teacher ID / EMIS ID", placeholder="எ.கா: 332...").strip()
        t_name = col2.text_input("ஆசிரியர் பெயர்").upper().strip()
        t_short = col3.text_input("சுருக்கம் (Short Name)", placeholder="KRA").upper().strip()

        if st.form_submit_button("💾 ஆசிரியரைச் சேமி"):
            if t_id and t_name and t_short:
                try:
                    supabase.table("staff_details").insert({
                        "teacher_id": t_id,
                        "teacher_name": t_name,
                        "short_name": t_short
                    }).execute()
                    st.success(f"ஆசிரியர் '{t_short}' விவரங்கள் சேமிக்கப்பட்டது!")
                    st.cache_data.clear()
                    st.rerun()
                except Exception as e:
                    st.error(f"பிழை: {e}")
            else:
                st.warning("ID, பெயர் மற்றும் சுருக்கப் பெயர் ஆகிய மூன்றையும் உள்ளிடவும்.")

st.divider()

# --- 2. ஆசிரியர் பட்டியல் ---
teacher_data = fetch_teachers()

if teacher_data:
    st.subheader("📋 ஆசிரியர்கள் பட்டியல்")
    df = pd.DataFrame(teacher_data)
    
    # தேவையற்ற காலம்களைத் தவிர்த்துவிட்டு காட்டுதல்
    display_df = df[['teacher_id', 'teacher_name', 'short_name']]
    display_df.columns = ['ID / EMIS', 'ஆசிரியர் பெயர்', 'சுருக்கப் பெயர்']
    
    st.dataframe(display_df, use_container_width=True, hide_index=True)

    st.divider()

    # --- 3. நீக்குதல் அல்லது திருத்துதல் ---
    st.subheader("⚙️ மேலாண்மை")
    t_options = {f"{t['short_name']} - {t['teacher_name']}": t['teacher_id'] for t in teacher_data}
    selected_t = st.selectbox("நிர்வகிக்க வேண்டிய ஆசிரியரைத் தேர்வு செய்க:", ["-- தேர்வு செய்க --"] + list(t_options.keys()))

    if selected_t != "-- தேர்வு செய்க --":
        t_to_manage = t_options[selected_t]
        
        if st.button(f"❌ {selected_t}-ஐ நீக்கு", type="primary"):
            try:
                supabase.table("staff_details").delete().eq("teacher_id", t_to_manage).execute()
                st.warning("நீக்கப்பட்டது!")
                st.cache_data.clear()
                st.rerun()
            except Exception as e:
                st.error(f"நீக்குவதில் பிழை: {e}")
else:
    st.info("ஆசிரியர்கள் விவரம் இன்னும் சேர்க்கப்படவில்லை.")
