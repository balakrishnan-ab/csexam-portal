import streamlit as st
import requests
import pandas as pd

# SheetDB API URL (Classes தாளுக்கானது)
API_URL = "https://sheetdb.io/api/v1/sb3mxuvdynqos?sheet=Classes"

st.set_page_config(page_title="GHSS Class Manager", layout="wide")

st.title("🏫 வகுப்பு மேலாண்மை (Class Master)")

# 1. தரவுகளைப் பெறுதல்
def fetch_data():
    response = requests.get(API_URL)
    return response.json() if response.status_code == 200 else []

# 2. உள்ளீடு பகுதி
with st.expander("➕ புதிய வகுப்பைச் சேர்க்க / திருத்த", expanded=True):
    col1, col2, col3 = st.columns(3)
    
    with col1:
        c_name = st.text_input("வகுப்பு பெயர்", placeholder="எ.கா: 12-A1")
    with col2:
        g_name = st.selectbox("பாடப்பிரிவு", ["உயிர்-கணிதம்", "கணித-கணினி", "கலை-கணினி", "கலை-வரலாறு"])
    with col3:
        medium = st.radio("பயிற்று மொழி", ["தமிழ் வழி", "ஆங்கில வழி"], horizontal=True)

    if st.button("வகுப்பைச் சேமி"):
        if c_name:
            new_data = {"class_id": c_name, "class_name": c_name, "group_name": g_name, "medium": medium}
            requests.post(API_URL, json={"data": [new_data]})
            st.success("வகுப்பு சேமிக்கப்பட்டது!")
            st.rerun()
        else:
            st.error("வகுப்பு பெயரை உள்ளிடவும்!")

# 3. அட்டவணை மற்றும் பதிப்பாய்வு பகுதி
st.subheader("📚 தற்போதுள்ள வகுப்புகள்")
data = fetch_data()

if data:
    df = pd.DataFrame(data)
    # தேவையில்லாத காலம்களை நீக்க
    display_df = df[['class_name', 'group_name', 'medium']]
    st.table(display_df)

    # நீக்குதல் வசதி (Delete)
    del_class = st.selectbox("நீக்க வேண்டிய வகுப்பைத் தேர்வு செய்க:", df['class_name'].tolist())
    if st.button("தேர்வு செய்த வகுப்பை நீக்கு", type="primary"):
        requests.delete(f"{API_URL}/class_id/{del_class}")
        st.warning(f"{del_class} நீக்கப்பட்டது!")
        st.rerun()
else:
    st.info("வகுப்புகள் ஏதும் இன்னும் சேர்க்கப்படவில்லை.")
