import streamlit as st
import requests

CLASS_API = "https://sheetdb.io/api/v1/sb3mxuvdynqos?sheet=Classes"
GROUP_API = "https://sheetdb.io/api/v1/sb3mxuvdynqos?sheet=Groups"

st.set_page_config(page_title="Classes", layout="wide")

# --- மொபைலில் ஒரே வரியில் தெரிய வைக்கும் CSS ---
st.markdown("""
    <style>
    /* அட்டவணை அமைப்பு */
    .compact-table {
        width: 100%;
        border-collapse: collapse;
        font-size: 12px; /* சிறிய எழுத்துக்கள் */
        table-layout: fixed; /* கட்டாயமாக அகலத்தை வகுக்கும் */
    }
    .compact-table th, .compact-table td {
        border-bottom: 1px solid #eee;
        padding: 8px 2px;
        text-align: left;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap; /* எழுத்துக்களை அடுத்த வரிக்கு விடாது */
    }
    .compact-table th { background-color: #f8f9fa; font-weight: bold; }
    
    /* நீக்குதல் பட்டனைச் சிறியதாக்க */
    div.stButton > button {
        padding: 0px !important;
        height: 25px !important;
        width: 25px !important;
        min-width: 25px !important;
        border-radius: 5px;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("🏫 வகுப்பு மேலாண்மை")

# 1. புதிய வகுப்புச் சேர்க்கை
with st.expander("➕ புதிய வகுப்பு", expanded=False):
    c_name = st.text_input("வகுப்பு")
    try:
        groups = requests.get(GROUP_API).json()
        group_list = [g['group_name'] for g in groups]
    except: group_list = []
    c_group = st.selectbox("பிரிவு", group_list)
    c_med = st.radio("மொழி", ["தமிழ்", "ஆங்கிலம்"], horizontal=True)
    if st.button("➕ சேமி", use_container_width=True):
        if c_name:
            requests.post(CLASS_API, json={"data": [{"class_name": c_name, "group_name": c_group, "medium": c_med}]})
            st.rerun()

st.divider()

# 2. அட்டவணைப் பகுதி
st.subheader("📋 வகுப்புகள்")

try:
    c_data = requests.get(CLASS_API).json()
    if c_data:
        # HTML அட்டவணைத் தலைப்பு
        st.markdown(f"""
            <table class="compact-table">
                <tr>
                    <th style="width: 20%;">வகுப்பு</th>
                    <th style="width: 40%;">பிரிவு</th>
                    <th style="width: 25%;">மொழி</th>
                    <th style="width: 15%;">நீக்க</th>
                </tr>
            </table>
        """, unsafe_allow_html=True)

        for cls in c_data:
            # ஒவ்வொரு மாணவர்/வகுப்பு வரிசையும் ஒரே லைனில் இருக்க 4 காலம்கள்
            col1, col2, col3, col4 = st.columns([2, 4, 2.5, 1.5])
            
            with col1: st.write(f"**{cls.get('class_name', '')}**")
            with col2: st.caption(cls.get('group_name', '')) # சிறிய எழுத்து
            with col3: st.write(cls.get('medium', '').split()[0]) # 'தமிழ் வழி'யை 'தமிழ்' எனச் சுருக்க
            with col4:
                if st.button("🗑️", key=f"del_{cls['class_name']}"):
                    requests.delete(f"{CLASS_API}/class_name/{cls['class_name']}")
                    st.rerun()
            
            st.markdown("<hr style='margin: 0px; opacity: 0.1'>", unsafe_allow_html=True)
    else:
        st.info("வகுப்புகள் ஏதுமில்லை.")
except Exception as e:
    st.error("தரவு பிழை!")
