import streamlit as st
import requests
import pandas as pd

# கூகுள் ஸ்கிரிப்ட் URL
BASE_URL = st.secrets["BASE_URL"]st.set_page_config(page_title="Groups Management", layout="wide")

# ⚡ தரவுகளை வேகமாகப் பெறுதல் (Caching)
@st.cache_data(ttl=300)
def fetch_data(sheet_name):
    try:
        res = requests.get(f"{BASE_URL}?sheet={sheet_name}", allow_redirects=True)
        return res.json()
    except:
        return []

st.title("👥 பாடப்பிரிவுகள் மேலாண்மை")

# தேவையான தரவுகளைப் பெறுதல்
groups_data = fetch_data("Groups")
subjects_data = fetch_data("Subjects")

# பாடங்களை மட்டும் ஒரு பட்டியலாக மாற்றுதல்
all_subjects = [s['subject_name'] for s in subjects_data] if subjects_data else []

# 1. புதிய பாடப்பிரிவு சேர்க்கும் படிவம்
with st.form("add_group_form", clear_on_submit=True):
    st.subheader("🆕 புதிய பாடப்பிரிவு")
    gname = st.text_input("பாடப்பிரிவு பெயர் (Group Name)").upper().strip()
    
    # பாடங்களைத் தேர்வு செய்யும் வசதி (Multi-select)
    selected_subs = st.multiselect("பாடங்களைத் தேர்வு செய்யவும் (Select Subjects):", all_subjects)
    
    if st.form_submit_button("💾 பாடப்பிரிவைச் சேமி"):
        if gname and selected_subs:
            # தேர்வு செய்த பாடங்களை கமா (,) மூலம் பிரித்து ஒரு வரியாக மாற்றுதல்
            subs_string = ", ".join(selected_subs)
            payload = {"group_name": gname, "subjects": subs_string}
            
            try:
                requests.post(f"{BASE_URL}?sheet=Groups", json={"data": [payload]}, allow_redirects=True)
                st.success(f"பாடப்பிரிவு '{gname}' வெற்றிகரமாகச் சேர்க்கப்பட்டது!")
                st.cache_data.clear()
                st.rerun()
            except Exception as e:
                st.error(f"பிழை: {e}")
        else:
            st.warning("பாடப்பிரிவு பெயர் மற்றும் பாடங்களைத் தேர்வு செய்யவும்.")

st.divider()

# 2. பாடப்பிரிவுகள் பட்டியல் (ID மறைக்கப்பட்டது)
if groups_data:
    df = pd.DataFrame(groups_data)
    df_sorted = df.sort_values(by='group_name').reset_index(drop=True)
    df_sorted.index = df_sorted.index + 1
    
    st.subheader("📋 பாடப்பிரிவுகள் பட்டியல்")
    st.dataframe(df_sorted[['group_name', 'subjects']], use_container_width=True)

    st.divider()

    # 3. திருத்துதல் மற்றும் நீக்குதல்
    st.subheader("⚙️ பாடப்பிரிவை மாற்றியமைக்க / நீக்க")
    
    g_list = ["-- பாடப்பிரிவைத் தேர்வு செய்க --"] + df_sorted['group_name'].tolist()
    sel_group = st.selectbox("நிர்வகிக்க வேண்டிய பாடப்பிரிவு:", g_list)

    if sel_group != "-- பாடப்பிரிவைத் தேர்வு செய்க --":
        old_data = df[df['group_name'] == sel_group].iloc[0]
        # பழைய பாடங்களைப் பட்டியலாக மாற்றுதல்
        current_subs = [s.strip() for s in str(old_data['subjects']).split(',')] if old_data['subjects'] else []
        
        col1, col2 = st.columns(2)
        with col1:
            st.write("📝 திருத்துதல்")
            new_gname = st.text_input("புதிய பெயர்:", value=old_data['group_name']).upper()
            # திருத்தும்போது புதிய பாடங்களைச் சேர்க்க/நீக்க வசதி
            new_subs = st.multiselect("பாடங்களைப் புதுப்பிக்கவும்:", all_subjects, default=current_subs)
            
            if st.button("🆙 திருத்து (Update)"):
                new_subs_str = ", ".join(new_subs)
                update_url = f"{BASE_URL}?sheet=Groups&action=update&old_group={sel_group}"
                requests.post(update_url, json={"data": [{"group_name": new_gname, "subjects": new_subs_str}]}, allow_redirects=True)
                st.success("மாற்றப்பட்டது!")
                st.cache_data.clear()
                st.rerun()

        with col2:
            st.write("⚠️ நீக்குதல்")
            if st.checkbox(f"நான் {sel_group}-ஐ நீக்க விரும்புகிறேன்"):
                if st.button(f"❌ {sel_group}-ஐ நீக்கு"):
                    del_url = f"{BASE_URL}?sheet=Groups&action=delete&group_name={sel_group}"
                    requests.post(del_url, allow_redirects=True)
                    st.warning("நீக்கப்பட்டது!")
                    st.cache_data.clear()
                    st.rerun()
else:
    st.info("தரவுகள் இல்லை.")
