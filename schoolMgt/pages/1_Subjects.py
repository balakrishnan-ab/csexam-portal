import streamlit as st
import requests

API_URL = "https://sheetdb.io/api/v1/sb3mxuvdynqos?sheet=Subjects"

st.set_page_config(page_title="Subjects", layout="wide")

# மொபைல் மற்றும் டெஸ்க்டாப் இரண்டிற்கும் ஏற்ற CSS
st.markdown("""
    <style>
    .fixed-table { width: 100%; border-collapse: collapse; font-size: 14px; table-layout: fixed; }
    .fixed-table th, .fixed-table td { border-bottom: 1px solid #eee; padding: 12px 5px; text-align: left; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
    .fixed-table th { background-color: #f1f3f5; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

st.title("📚 பாடங்கள் மேலாண்மை")

# புதிய பாடம் சேர்க்கை
with st.expander("➕ புதிய பாடம் சேர்க்க", expanded=False):
    sub_name = st.text_input("பாடத்தின் பெயர்")
    eval_type = st.selectbox("மதிப்பீட்டு முறை", ["Internal & External", "Only Internal"])
    if st.button("💾 பாடத்தைச் சேமி", use_container_width=True):
        if sub_name:
            requests.post(API_URL, json={"data": [{"subject_name": sub_name, "eval_type": eval_type}]})
            st.rerun()

st.divider()

# அட்டவணை
try:
    data = requests.get(API_URL).json()
    if data:
        html = """<table class="fixed-table"><tr><th style="width: 50%;">பாடம்</th><th style="width: 35%;">முறை</th><th style="width: 15%;">நீக்க</th></tr>"""
        for item in data:
            s_val = item.get('subject_name', '')
            e_val = item.get('eval_type', '').split()[0] # 'Internal' எனச் சுருக்க
            html += f"""<tr><td><b>{s_val}</b></td><td>{e_val}</td>
            <td><a href="?delete_sub={s_val}" target="_self" style="text-decoration:none; background:#ff4b4b; color:white; padding:3px 8px; border-radius:4px; font-size:11px;">🗑️</a></td></tr>"""
        html += "</table>"
        st.markdown(html, unsafe_allow_html=True)

        # நீக்குதல் லாஜிக்
        if "delete_sub" in st.query_params:
            requests.delete(f"{API_URL}/subject_name/{st.query_params['delete_sub']}")
            st.query_params.clear()
            st.rerun()
except: st.info("பாடங்கள் ஏதுமில்லை.")
