import streamlit as st
import requests

CLASS_API = "https://sheetdb.io/api/v1/sb3mxuvdynqos?sheet=Classes"
GROUP_API = "https://sheetdb.io/api/v1/sb3mxuvdynqos?sheet=Groups"

st.set_page_config(page_title="Classes", layout="wide")

# --- மொபைலில் ஒரே வரியில் தெரிய வைக்கும் CSS ---
st.markdown("""
    <style>
    /* முழு அட்டவணை அமைப்பு */
    .mobile-fixed-table {
        width: 100%;
        border-collapse: collapse;
        font-family: Arial, sans-serif;
        font-size: 13px;
    }
    .mobile-fixed-table th, .mobile-fixed-table td {
        border-bottom: 1px solid #eee;
        padding: 10px 4px;
        text-align: left;
    }
    .mobile-fixed-table th { background-color: #f1f3f5; font-weight: bold; }
    
    /* பட்டன் ஸ்டைல் */
    .del-btn {
        background-color: #ff4b4b;
        color: white;
        border: none;
        padding: 5px 8px;
        border-radius: 5px;
        cursor: pointer;
        font-size: 12px;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("🏫 வகுப்பு மேலாண்மை")

# 1. புதிய வகுப்புச் சேர்க்கை
with st.expander("➕ புதிய வகுப்பு", expanded=False):
    c_name = st.text_input("வகுப்பு பெயர்")
    try:
        groups = requests.get(GROUP_API).json()
        group_list = [g['group_name'] for g in groups]
    except: group_list = []
    c_group = st.selectbox("பிரிவு", group_list)
    c_med = st.radio("மொழி", ["தமிழ்", "ஆங்கிலம்"], horizontal=True)
    if st.button("💾 சேமி", use_container_width=True):
        if c_name:
            requests.post(CLASS_API, json={"data": [{"class_name": c_name, "group_name": c_group, "medium": c_med}]})
            st.rerun()

st.divider()

# 2. அட்டவணைப் பகுதி
st.subheader("📋 வகுப்புகள்")

try:
    c_data = requests.get(CLASS_API).json()
    if c_data:
        # முழு அட்டவணையை HTML மூலம் உருவாக்குகிறோம்
        # இதுதான் தகவல்களை ஒரே வரியில் வைக்கும்
        table_html = """
        <table class="mobile-fixed-table">
            <tr>
                <th style="width: 25%;">வகுப்பு</th>
                <th style="width: 35%;">பிரிவு</th>
                <th style="width: 25%;">மொழி</th>
                <th style="width: 15%;">நீக்க</th>
            </tr>
        """
        
        for cls in c_data:
            c_name_val = cls.get('class_name', '')
            g_name_val = cls.get('group_name', '')
            m_name_val = cls.get('medium', '')
            
            # ஒவ்வொரு வரிசையும் ஒரு <tr> - இதுதான் உங்கள் 'ஒரே வரிசை' கோரிக்கை
            table_html += f"""
            <tr>
                <td><b>{c_name_val}</b></td>
                <td><small>{g_name_val}</small></td>
                <td>{m_name_val}</td>
                <td>
                    <a href="?delete={c_name_val}" target="_self" 
                       style="text-decoration:none; background:#ff4b4b; color:white; padding:2px 8px; border-radius:4px; font-size:10px;">🗑️</a>
                </td>
            </tr>
            """
        
        table_html += "</table>"
        st.markdown(table_html, unsafe_allow_html=True)

        # நீக்குதல் லாஜிக் (URL Query Param மூலம்)
        query_params = st.query_params
        if "delete" in query_params:
            del_id = query_params["delete"]
            requests.delete(f"{CLASS_API}/class_name/{del_id}")
            st.query_params.clear() # Query பாராமிட்டரை நீக்க
            st.rerun()

    else:
        st.info("வகுப்புகள் ஏதுமில்லை.")
except Exception as e:
    st.error(f"பிழை: {e}")
