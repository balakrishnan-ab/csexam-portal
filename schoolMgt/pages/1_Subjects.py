import streamlit as st
import requests

SUB_API = "https://sheetdb.io/api/v1/sb3mxuvdynqos?sheet=Subjects"
GROUP_API = "https://sheetdb.io/api/v1/sb3mxuvdynqos?sheet=Groups"

st.set_page_config(page_title="Groups", layout="wide")

st.markdown("""
    <style>
    .fixed-table { width: 100%; border-collapse: collapse; font-size: 14px; table-layout: fixed; }
    .fixed-table th, .fixed-table td { 
        border-bottom: 1px solid #eee; 
        padding: 10px 5px; 
        text-align: left; 
        word-wrap: break-word; /* பாடங்கள் மடிந்து வர இது உதவும் */
        vertical-align: middle;
    }
    .fixed-table th { background-color: #f1f3f5; font-weight: bold; }
    .sub-list { font-size: 12px; color: #333; line-height: 1.4; }
    </style>
    """, unsafe_allow_html=True)

st.title("🧬 பாடப்பிரிவு மேலாண்மை")

# புதிய பிரிவு சேர்க்கை
try:
    subs = requests.get(SUB_API).json()
    sub_list = [s['subject_name'] for s in subs]
except: sub_list = []

with st.expander("➕ புதிய பிரிவு உருவாக்க", expanded=False):
    g_name = st.text_input("பிரிவு பெயர்")
    selected_subs = st.multiselect("பாடங்களைத் தேர்ந்தெடுக்கவும்", sub_list)
    if st.button("💾 பிரிவைச் சேமி", use_container_width=True):
        if g_name and selected_subs:
            requests.post(GROUP_API, json={"data": [{"group_name": g_name, "subjects": ", ".join(selected_subs)}]})
            st.rerun()

st.divider()

# அட்டவணை
try:
    g_data = requests.get(GROUP_API).json()
    if g_data:
        # பாடங்களுக்கு அதிக இடம் (60%) ஒதுக்கப்பட்டுள்ளது
        html = """<table class="fixed-table">
            <tr>
                <th style="width: 25%;">பிரிவு</th>
                <th style="width: 60%;">பாடங்கள்</th>
                <th style="width: 15%;">நீக்க</th>
            </tr>"""
        for g in g_data:
            gn = g.get('group_name', '')
            gs = g.get('subjects', '')
            html += f"""
            <tr>
                <td><b>{gn}</b></td>
                <td><span class="sub-list">{gs}</span></td>
                <td style="text-align:center;">
                    <a href="?del_grp={gn}" target="_self" style="text-decoration:none; background:#ff4b4b; color:white; padding:5px 10px; border-radius:4px; font-size:12px;">🗑️</a>
                </td>
            </tr>"""
        html += "</table>"
        st.markdown(html, unsafe_allow_html=True)

        if "del_grp" in st.query_params:
            requests.delete(f"{GROUP_API}/group_name/{st.query_params['del_grp']}")
            st.query_params.clear()
            st.rerun()
except: st.info("பிரிவுகள் ஏதுமில்லை.")
