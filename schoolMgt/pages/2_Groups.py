import streamlit as st
import requests
import pandas as pd

SUB_API = "https://sheetdb.io/api/v1/sb3mxuvdynqos?sheet=Subjects"
GROUP_API = "https://sheetdb.io/api/v1/sb3mxuvdynqos?sheet=Groups"

st.title("🧬 பாடப்பிரிவு உருவாக்கம் (Group Master)")

# பாடங்களைப் பெறுதல்
sub_data = requests.get(SUB_API).json()
sub_list = [s['subject_name'] for s in sub_data] if isinstance(sub_data, list) else []

with st.expander("➕ புதிய பாடப்பிரிவை உருவாக்கு", expanded=True):
    g_name = st.text_input("பிரிவின் பெயர்", placeholder="எ.கா: கணித-கணினி")
    selected_subs = st.multiselect("6 பாடங்களைத் தேர்ந்தெடுக்கவும்", sub_list)
    
    if st.button("📝 பிரிவைச் சேமி"):
        if g_name and len(selected_subs) > 0:
            payload = {"group_name": g_name, "subjects": ", ".join(selected_subs)}
            requests.post(GROUP_API, json={"data": [payload]})
            st.success(f"{g_name} பிரிவு உருவாக்கப்பட்டது!")
            st.rerun()

# பட்டியல்
st.subheader("📂 உள்ள பாடப்பிரிவுகள்")
g_res = requests.get(GROUP_API)
g_data = g_res.json() if g_res.status_code == 200 else []

if g_data:
    st.table(pd.DataFrame(g_data))
    del_grp = st.selectbox("🗑️ நீக்க வேண்டிய பிரிவைத் தேர்வு செய்க:", [g['group_name'] for g in g_data])
    if st.button("🗑️ பிரிவை நீக்கு"):
        requests.delete(f"{GROUP_API}/group_name/{del_grp}")
        st.rerun()
