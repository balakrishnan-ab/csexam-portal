import streamlit as st
from supabase import create_client, Client
import pandas as pd

# 1. Supabase இணைப்பு
url: str = st.secrets["SUPABASE_URL"]
key: str = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

st.set_page_config(page_title="Groups Management", layout="wide")
st.title("👥 பாடப்பிரிவுகள் மேலாண்மை (Supabase)")

# ⚡ தரவுகளைப் பெறுதல்
@st.cache_data(ttl=60)
def fetch_data(table_name):
    try:
        response = supabase.table(table_name).select("*").execute()
        return response.data
    except:
        return []

# தேவையான தரவுகளைப் பெறுதல்
groups_data = fetch_data("groups")
subjects_data = fetch_data("subjects")

# பாடங்களை மட்டும் ஒரு பட்டியலாக மாற்றுதல்
all_subjects = [s['subject_name'] for s in subjects_data] if subjects_data else []

# 1. புதிய பாடப்பிரிவு சேர்க்கும் படிவம்
with st.form("add_group_form", clear_on_submit=True):
    st.subheader("🆕 புதிய பாடப்பிரிவு")
    col1, col2 = st.columns([1, 3])
    gcode = col1.text_input("Group Code").strip()
    gname = col2.text_input("பாடப்பிரிவு பெயர் (Group Name)").upper().strip()
    
    selected_subs = st.multiselect("பாடங்களைத் தேர்வு செய்யவும்:", all_subjects)
    
    if st.form_submit_button("💾 பாடப்பிரிவைச் சேமி"):
        if gcode and gname and selected_subs:
            subs_string = ", ".join(selected_subs)
            try:
                supabase.table("groups").insert({
                    "group_code": gcode,
                    "group_name": gname, 
                    "subjects": subs_string
                }).execute()
                st.success(f"பாடப்பிரிவு '{gname}' சேர்க்கப்பட்டது!")
                st.cache_data.clear()
                st.rerun()
            except Exception as e:
                st.error(f"பிழை: {e}")
        else:
            st.warning("அனைத்து விபரங்களையும் பூர்த்தி செய்யவும்.")

st.divider()

# 2. பாடப்பிரிவுகள் பட்டியல்
if groups_data:
    df = pd.DataFrame(groups_data)
    st.subheader("📋 பாடப்பிரிவுகள் பட்டியல்")
    st.dataframe(df[['group_code', 'group_name', 'subjects']], use_container_width=True, hide_index=True)

    st.divider()

    # 3. திருத்துதல் மற்றும் நீக்குதல்
    st.subheader("⚙️ மேலாண்மை")
    g_codes = df['group_code'].tolist()
    sel_code = st.selectbox("நிர்வகிக்க வேண்டிய பாடப்பிரிவு கோட் (Group Code):", ["-- தேர்வு செய்க --"] + g_codes)

    if sel_code != "-- தேர்வு செய்க --":
        old_data = df[df['group_code'] == sel_code].iloc[0]
        current_subs = [s.strip() for s in str(old_data['subjects']).split(',')] if old_data['subjects'] else []
        
        col1, col2 = st.columns(2)
        with col1:
            st.write("📝 திருத்துதல்")
            new_gname = st.text_input("புதிய பெயர்:", value=old_data['group_name']).upper()
            new_subs = st.multiselect("பாடங்களைப் புதுப்பிக்கவும்:", all_subjects, default=current_subs)
            
            if st.button("🆙 இற்றைப்படுத்து (Update)"):
                new_subs_str = ", ".join(new_subs)
                supabase.table("groups").update({
                    "group_name": new_gname, 
                    "subjects": new_subs_str
                }).eq("group_code", sel_code).execute()
                st.success("மாற்றப்பட்டது!")
                st.cache_data.clear()
                st.rerun()

        with col2:
            st.write("⚠️ நீக்குதல்")
            if st.button(f"❌ {sel_code}-ஐ நீக்கு", type="primary"):
                supabase.table("groups").delete().eq("group_code", sel_code).execute()
                st.warning("நீக்கப்பட்டது!")
                st.cache_data.clear()
                st.rerun()
else:
    st.info("பாடப்பிரிவுகள் இன்னும் சேர்க்கப்படவில்லை.")
