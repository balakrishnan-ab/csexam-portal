import streamlit as st
import requests
import pandas as pd

EXAM_API = "https://sheetdb.io/api/v1/sb3mxuvdynqos?sheet=Exams"

st.set_page_config(page_title="Exams", layout="wide")

# CSS - மொபைல் கச்சிதமான தோற்றம்
st.markdown("""
    <style>
    .fixed-table { width: 100%; border-collapse: collapse; font-size: 14px; table-layout: fixed; }
    .fixed-table th, .fixed-table td { 
        border-bottom: 1px solid #eee; padding: 12px 5px; text-align: left; 
    }
    .fixed-table th { background-color: #f1f3f5; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

st.title("📝 தேர்வு மேலாண்மை")

# 1. புதிய தேர்வை உருவாக்குதல்
with st.expander("➕ புதிய தேர்வை உருவாக்க", expanded=False):
    e_name = st.text_input("தேர்வின் பெயர் (எ.கா: First Revision)")
    e_year = st.selectbox("கல்வியாண்டு", ["2025-26", "2026-27"])
    
    if st.button("💾 தேர்வைச் சேமி", use_container_width=True):
        if e_name:
            # exam_id-யும் பெயரையும் ஒன்றாகவே வைக்கிறோம்
            payload = {"exam_id": e_name, "exam_name": e_name, "academic_year": e_year}
            requests.post(EXAM_API, json={"data": [payload]})
            st.success("தேர்வு உருவாக்கப்பட்டது!")
            st.rerun()

st.divider()

# 2. தேர்வுகளின் பட்டியல்
st.subheader("📋 உருவாக்கப்பட்ட தேர்வுகள்")

try:
    exams = requests.get(EXAM_API).json()
    if exams and isinstance(exams, list):
        html_code = """
        <table class="fixed-table">
            <tr>
                <th style="width: 50%;">தேர்வு பெயர்</th>
                <th style="width: 35%;">கல்வியாண்டு</th>
                <th style="width: 15%;">நீக்க</th>
            </tr>"""
        
        for e in exams:
            en = e.get('exam_name', '')
            ey = e.get('academic_year', '')
            
            html_code += f"""
            <tr>
                <td><b>{en}</b></td>
                <td>{ey}</td>
                <td style="text-align:center;">
                    <a href="?delete_exam={en}" target="_self" 
                       style="text-decoration:none; background:#ff4b4b; color:white; padding:4px 8px; border-radius:4px; font-size:10px;">🗑️</a>
                </td>
            </tr>"""
        
        html_code += "</table>"
        st.markdown(html_code, unsafe_allow_html=True)

        # நீக்குதல் லாஜிக்
        if "delete_exam" in st.query_params:
            requests.delete(f"{EXAM_API}/exam_name/{st.query_params['delete_exam']}")
            st.query_params.clear()
            st.rerun()
    else:
        st.info("தேர்வுகள் ஏதுமில்லை.")
except:
    st.error("தரவுகளைப் பெறுவதில் சிக்கல்!")
