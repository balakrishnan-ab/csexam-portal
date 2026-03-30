import streamlit as st
import requests

CLASS_API = "https://sheetdb.io/api/v1/sb3mxuvdynqos?sheet=Classes"
GROUP_API = "https://sheetdb.io/api/v1/sb3mxuvdynqos?sheet=Groups"

st.set_page_config(page_title="Classes", layout="wide")

# --- மொபைல் திரைக்கு ஏற்ற CSS திருத்தங்கள் ---
st.markdown("""
    <style>
    /* செல்கள் மற்றும் வரிகளுக்கு இடையே இடைவெளியைக் குறைக்க */
    [data-testid="column"] {
        padding: 0px 5px !important;
        flex-direction: column;
        display: flex;
        justify-content: center;
    }
    .stVerticalBlock {
        gap: 0.2rem !important; /* வரிகளுக்கு இடையே இடைவெளி */
    }
    /* பட்டன் அளவைச் சிறியதாக்க */
    button[kind="secondary"] {
        padding: 0px 10px !important;
        height: 30px !important;
        line-height: 1 !important;
    }
    /* உரை அளவு */
    p, span {
        font-size: 14px !important;
        margin-bottom: 0px !important;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("🏫 வகுப்பு மேலாண்மை")

# 1. பிரிவுகளைப் பெறுதல்
try:
    groups = requests.get(GROUP_API).json()
    group_list = [g['group_name'] for g in groups] if isinstance(groups, list) else []
except:
    group_list = []

# 2. புதிய வகுப்பைச் சேர்க்க
with st.expander("➕ புதிய வகுப்பு", expanded=False):
    c_name = st.text_input("வகுப்பு (எ.கா: 12-A1)")
    c_group = st.selectbox("பிரிவு", group_list)
    c_med = st.radio("மொழி", ["தமிழ்", "ஆங்கிலம்"], horizontal=True)
    if st.button("➕ சேமி", use_container_width=True):
        if c_name:
            payload = {"class_name": c_name, "group_name": c_group, "medium": c_med}
            requests.post(CLASS_API, json={"data": [payload]})
            st.rerun()

st.divider()

# 3. நெருக்கமான அட்டவணை (Compact Table)
st.subheader("📋 வகுப்புகள்")

try:
    c_data = requests.get(CLASS_API).json()
    if c_data:
        # தலைப்புகள்
        h1, h2, h3, h4 = st.columns([2, 4, 3, 1])
        h1.caption("**வகுப்பு**")
        h2.caption("**பிரிவு**")
        h3.caption("**மொழி**")
        h4.caption("**நீக்க**")
        st.markdown("<hr style='margin: 5px 0px'>", unsafe_allow_html=True)

        for cls in c_data:
            col1, col2, col3, col4 = st.columns([2, 4, 3, 1])
            
            col1.write(cls.get('class_name', ''))
            col2.write(cls.get('group_name', ''))
            col3.write(cls.get('medium', ''))
            
            # 🗑️ மிகச் சிறிய நீக்குதல் பட்டன்
            if col4.button("🗑️", key=f"del_{cls['class_name']}"):
                requests.delete(f"{CLASS_API}/class_name/{cls['class_name']}")
                st.rerun()
            
            st.markdown("<hr style='margin: 2px 0px; opacity: 0.2'>", unsafe_allow_html=True)
    else:
        st.info("வகுப்புகள் ஏதுமில்லை.")
except:
    st.error("தரவு பிழை!")
