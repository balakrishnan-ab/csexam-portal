import streamlit as st
from supabase import create_client, Client
import pandas as pd

# 1. Supabase இணைப்பு
url: str = st.secrets["SUPABASE_URL"]
key: str = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

st.set_page_config(page_title="Classes Management", layout="wide")
st.title("🏫 வகுப்புகள் மேலாண்மை (Supabase)")

# ⚡ தரவுகளைப் பெறுதல்
@st.cache_data(ttl=60)
def fetch_table_data(table_name):
    try:
        response = supabase.table(table_name).select("*").execute()
        return response.data
    except Exception as e:
        st.error(f"{table_name} தரவைப் பெறுவதில் பிழை: {e}")
        return []

# தேவையான தரவுகளைப் பெறுதல்
classes_data = fetch_table_data("classes")
groups_data = fetch_table_data("groups")

# பாடப்பிரிவுகளை மட்டும் பட்டியலாக மாற்றுதல்
group_list = [g['group_name'] for g in groups_data] if groups_data else []

# 1. புதிய வகுப்பு சேர்க்கும் படிவம்
with st.form("add_class_form", clear_on_submit=True):
    st.subheader("🆕 புதிய வகுப்பு சேர்க்கை")
    col1, col2 = st.columns(2)
    cname = col1.text_input("வகுப்பு பெயர் (எ.கா: 12-A1)").upper().strip()
    medium = col2.selectbox("பயிற்று மொழி (Medium):", ["Tamil", "English"])
    
    selected_group = st.selectbox("பாடப்பிரிவைத் தேர்ந்தெடுக்கவும்:", group_list)
    
    if st.form_submit_button("💾 வகுப்பைச் சேமி"):
        if cname and selected_group:
            try:
                supabase.table("classes").insert({
                    "class_name": cname, 
                    "group_name": selected_group, 
                    "medium": medium
                }).execute()
                st.success(f"வகுப்பு '{cname}' வெற்றிகரமாகச் சேர்க்கப்பட்டது!")
                st.cache_data.clear()
                st.rerun()
            except Exception as e:
                st.error(f"பிழை: {e}")
        else:
            st.warning("வகுப்பு பெயர் மற்றும் பாடப்பிரிவைத் தேர்ந்தெடுக்கவும்.")

st.divider()

# 2. வகுப்புகள் பட்டியல்
if classes_data:
    df = pd.DataFrame(classes_data)
    df_sorted = df.sort_values(by='class_name').reset_index(drop=True)
    
    st.subheader("📋 வகுப்புகள் பட்டியல்")
    st.dataframe(df_sorted[['class_name', 'medium', 'group_name']], 
                 use_container_width=True, hide_index=True)

    st.divider()

    # 3. திருத்துதல் மற்றும் நீக்குதல்
    st.subheader("⚙️ மேலாண்மை")
    c_names = df_sorted['class_name'].tolist()
    sel_class = st.selectbox("நிர்வகிக்க வேண்டிய வகுப்பு:", ["-- தேர்வு செய்க --"] + c_names)

    if sel_class != "-- தேர்வு செய்க --":
        old_data = df[df['class_name'] == sel_class].iloc[0]
        
        col1, col2 = st.columns(2)
        with col1:
            st.write("📝 திருத்துதல்")
            new_cname = st.text_input("புதிய பெயர்:", value=old_data['class_name']).upper()
            new_medium = st.selectbox("புதிய மொழி:", ["Tamil", "English"], 
                                   index=0 if old_data['medium'] == "Tamil" else 1)
            
            # பழைய குரூப் இன்டெக்ஸ் கண்டறிதல்
            g_idx = group_list.index(old_data['group_name']) if old_data['group_name'] in group_list else 0
            new_gname = st.selectbox("புதிய பாடப்பிரிவு:", group_list, index=g_idx)
            
            if st.button("🆙 இற்றைப்படுத்து (Update)"):
                supabase.table("classes").update({
                    "class_name": new_cname, 
                    "group_name": new_gname, 
                    "medium": new_medium
                }).eq("class_name", sel_class).execute()
                st.success("மாற்றப்பட்டது!")
                st.cache_data.clear()
                st.rerun()

        with col2:
            st.write("⚠️ நீக்குதல்")
            if st.button(f"❌ {sel_class}-ஐ நீக்கு", type="primary"):
                supabase.table("classes").delete().eq("class_name", sel_class).execute()
                st.warning("நீக்கப்பட்டது!")
                st.cache_data.clear()
                st.rerun()
else:
    st.info("வகுப்புகள் இன்னும் இல்லை.")
