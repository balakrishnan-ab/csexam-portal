import streamlit as st
import requests

CLASS_API = "https://sheetdb.io/api/v1/sb3mxuvdynqos?sheet=Classes"
GROUP_API = "https://sheetdb.io/api/v1/sb3mxuvdynqos?sheet=Groups"

st.set_page_config(page_title="Classes", layout="wide")

# --- போனுக்கான மிக நெருக்கமான CSS ---
st.markdown("""
    <style>
    /* அட்டவணை ஸ்டைல் */
    .mobile-table { width: 100%; border-collapse: collapse; font-size: 13px; }
    .mobile-table th { background-color: #f0f2f6; text-align: left; padding: 5px; border-bottom: 2px solid #ddd; }
    .mobile-table td { padding: 8px 5px; border-bottom: 1px solid #eee; vertical-align: middle; }
    
    /* பட்டன் உள்ள கட்டம் */
    .del-btn-container { display: flex; justify-content: center; }
    
    /* இதர இடைவெளிகள் */
    .stMainBlockContainer { padding: 1rem !important; }
    </style>
    """, unsafe_allow_html=True)

st.title("🏫 வகுப்பு மேலாண்மை")

# 1. புதிய வகுப்பைச் சேர்க்கும் பகுதி (Compact Expander)
with st.expander("➕ புதிய வகுப்பு", expanded=False):
    c_name = st.text_input("வகுப்பு")
    
    # பிரிவுகளைப் பெறுதல்
    try:
        groups = requests.get(GROUP_API).json()
        group_list = [g['group_name'] for g in groups]
    except:
        group_list = []
        
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
        # நாம் HTML மூலமாக தலைப்பை மட்டும் உருவாக்குகிறோம்
        st.markdown("""
            <table class="mobile-table">
                <tr>
                    <th style="width: 25%;">வகுப்பு</th>
                    <th style="width: 35%;">பிரிவு</th>
                    <th style="width: 25%;">மொழி</th>
                    <th style="width: 15%;">நீக்க</th>
                </tr>
            </table>
        """, unsafe_allow_html=True)

        for cls in c_data:
            # ஒவ்வொரு வரிசைக்கும் 4 காலம்கள்
            col1, col2, col3, col4 = st.columns([2.5, 3.5, 2.5, 1.5])
            
            with col1: st.write(cls.get('class_name', ''))
            with col2: st.write(f"<small>{cls.get('group_name', '')}</small>", unsafe_allow_html=True)
            with col3: st.write(cls.get('medium', ''))
            with col4:
                # 🗑️ மிகச் சிறிய பட்டன்
                if st.button("🗑️", key=f"del_{cls['class_name']}"):
                    requests.delete(f"{CLASS_API}/class_name/{cls['class_name']}")
                    st.rerun()
            
            st.markdown("<hr style='margin: 0px; opacity: 0.1'>", unsafe_allow_html=True)
    else:
        st.info("வகுப்புகள் ஏதுமில்லை.")
except:
    st.error("தரவு பிழை!")
