import streamlit as st
import requests
import pandas as pd

# கூகுள் ஸ்கிரிப்ட் URL
BASE_URL = "https://script.google.com/macros/s/AKfycbzgqCZ6f-kwO46eZPWb_Tr7gz-JdLQSSOL8kVLzRbhPIrinmdQrGiNjNHYIYANNPO8xYg/exec"

st.set_page_config(page_title="Classes Management", layout="wide")

# ⚡ தரவுகளை வேகமாகப் பெறுதல் (Caching)
@st.cache_data(ttl=300)
def fetch_data(sheet_name):
    try:
        res = requests.get(f"{BASE_URL}?sheet={sheet_name}", allow_redirects=True)
        return res.json()
    except:
        return []

st.title("🏫 வகுப்புகள் மேலாண்மை")

# தேவையான தரவுகளைப் பெறுதல்
classes_data = fetch_data("Classes")
groups_data = fetch_data("Groups")

# பாடப்பிரிவுகளை மட்டும் ஒரு பட்டியலாக மாற்றுதல்
group_list = [g['group_name'] for g in groups_data] if groups_data else []

# 1. புதிய வகுப்பு சேர்க்கும் படிவம்
with st.form("add_class_form", clear_on_submit=True):
    st.subheader("🆕 புதிய வகுப்பு சேர்க்கை")
    cname = st.text_input("வகுப்பு பெயர் (எ.கா: 12-A1)").upper().strip()
    
    # பாடப்பிரிவைத் தேர்வு செய்யும் வசதி (Dropdown)
    selected_group = st.selectbox("பாடப்பிரிவைத் தேர்ந்தெடுக்கவும் (Select Group):", group_list)
    
    if st.form_submit_button("💾 வகுப்பைச் சேமி"):
        if cname and selected_group:
            payload = {"class_name": cname, "group_name": selected_group}
            try:
                requests.post(f"{BASE_URL}?sheet=Classes", json={"data": [payload]}, allow_redirects=True)
                st.success(f"வகுப்பு '{cname}' வெற்றிகரமாகச் சேர்க்கப்பட்டது!")
                st.cache_data.clear()
                st.rerun()
            except Exception as e:
                st.error(f"பிழை: {e}")
        else:
            st.warning("வகுப்பு பெயர் மற்றும் பாடப்பிரிவைத் தேர்ந்தெடுக்கவும்.")

st.divider()

# 2. வகுப்புகள் பட்டியல் (ID மறைக்கப்பட்டது)
if classes_data:
    df = pd.DataFrame(classes_data)
    # அகர வரிசைப்படி அடுடுதல்
    df_sorted = df.sort_values(by='class_name').reset_index(drop=True)
    df_sorted.index = df_sorted.index + 1
    df_sorted.index.name = "S.No"
    
    st.subheader("📋 வகுப்புகள் பட்டியல்")
    # 🛡️ 'id' காலத்தை மறைத்துவிட்டுத் தேவையானவற்றை மட்டும் காட்டுதல்
    st.dataframe(df_sorted[['class_name', 'group_name']], use_container_width=True)

    st.divider()

    # 3. திருத்துதல் மற்றும் நீக்குதல் (Edit & Delete)
    st.subheader("⚙️ வகுப்பை மாற்றியமைக்க / நீக்க")
    
    c_list = ["-- வகுப்பைத் தேர்வு செய்க --"] + df_sorted['class_name'].tolist()
    sel_class = st.selectbox("நிர்வகிக்க வேண்டிய வகுப்பு:", c_list)

    if sel_class != "-- வகுப்பைத் தேர்வு செய்க --":
        old_data = df[df['class_name'] == sel_class].iloc[0]
        
        col1, col2 = st.columns(2)
        with col1:
            st.write("📝 திருத்துதல் (Edit)")
            new_cname = st.text_input("புதிய வகுப்பு பெயர்:", value=old_data['class_name']).upper()
            new_gname = st.selectbox("புதிய பாடப்பிரிவு:", group_list, 
                                    index=group_list.index(old_data['group_name']) if old_data['group_name'] in group_list else 0)
            
            if st.button("🆙 திருத்து (Update)"):
                update_url = f"{BASE_URL}?sheet=Classes&action=update&old_class={sel_class}"
                payload = {"class_name": new_cname, "group_name": new_gname}
                requests.post(update_url, json={"data": [payload]}, allow_redirects=True)
                st.success("வகுப்பு விவரங்கள் மாற்றப்பட்டது!")
                st.cache_data.clear()
                st.rerun()

        with col2:
            st.write("⚠️ நீக்குதல் (Delete)")
            if st.checkbox(f"நான் {sel_class}-ஐ நீக்க விரும்புகிறேன்"):
                if st.button(f"❌ {sel_class}-ஐ நீக்கு", type="primary"):
                    del_url = f"{BASE_URL}?sheet=Classes&action=delete&class_name={sel_class}"
                    requests.post(del_url, allow_redirects=True)
                    st.warning("வகுப்பு நீக்கப்பட்டது!")
                    st.cache_data.clear()
                    st.rerun()
else:
    st.info("வகுப்புகள் இன்னும் சேர்க்கப்படவில்லை.")
