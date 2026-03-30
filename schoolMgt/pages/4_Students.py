import streamlit as st
import requests
import pandas as pd

STUDENT_API = "https://sheetdb.io/api/v1/sb3mxuvdynqos?sheet=Students"
CLASS_API = "https://sheetdb.io/api/v1/sb3mxuvdynqos?sheet=Classes"

st.set_page_config(page_title="Students", layout="wide")

st.markdown("""
    <style>
    .student-table { width: 100%; border-collapse: collapse; font-size: 13px; table-layout: fixed; }
    .student-table th, .student-table td { border-bottom: 1px solid #eee; padding: 10px 4px; text-align: left; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
    .student-table th { background-color: #f1f3f5; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

st.title("👨‍🎓 மாணவர் மேலாண்மை")

# 1. வகுப்புகளைப் பெறுதல்
try:
    classes = requests.get(CLASS_API).json()
    class_list = [c['class_name'] for c in classes]
except: class_list = []

# 2. மாணவர் சேர்க்கை
with st.expander("➕ புதிய மாணவர் / Excel பதிவேற்றம்", expanded=False):
    tab1, tab2 = st.tabs(["தனிச் சேர்க்கை", "Excel மூலம்"])
    with tab1:
        s_name = st.text_input("மாணவர் பெயர்")
        c1, c2 = st.columns(2)
        s_emis = c1.text_input("EMIS எண்")
        s_phone = c2.text_input("போன் எண்")
        s_class = st.selectbox("வகுப்பு", class_list, key="single")
        if st.button("💾 சேமி", use_container_width=True):
            if s_name and s_class:
                requests.post(STUDENT_API, json={"data": [{"student_name": s_name, "emis_no": s_emis, "phone_no": s_phone, "class_name": s_class}]})
                st.rerun()
    with tab2:
        file = st.file_uploader("Excel/CSV கோப்பு", type=['csv', 'xlsx'])
        upl_class = st.selectbox("வகுப்பு", class_list, key="bulk")
        if file and st.button("🚀 பதிவேற்று"):
            df = pd.read_csv(file) if file.name.endswith('.csv') else pd.read_excel(file)
            df['class_name'] = upl_class
            requests.post(STUDENT_API, json={"data": df.to_dict(orient='records')})
            st.rerun()

st.divider()

# 3. பட்டியல்
st.subheader("📋 மாணவர் பட்டியல்")
view_cls = st.selectbox("வகுப்பைத் தேர்வு செய்க", ["அனைத்தும்"] + class_list)

try:
    students = requests.get(STUDENT_API).json()
    if students:
        html = """<table class="student-table"><tr><th style="width: 50%;">பெயர்</th><th style="width: 35%;">EMIS</th><th style="width: 15%;">நீக்க</th></tr>"""
        for s in students:
            if view_cls == "அனைத்தும்" or s.get('class_name') == view_cls:
                n = s.get('student_name', '')
                e = s.get('emis_no', '')
                html += f"<tr><td><b>{n}</b></td><td>{e}</td><td><a href='?delete_std={e}' target='_self' style='text-decoration:none; background:#ff4b4b; color:white; padding:3px 8px; border-radius:4px; font-size:10px;'>🗑️</a></td></tr>"
        html += "</table>"
        st.markdown(html, unsafe_allow_html=True)
        if "delete_std" in st.query_params:
            requests.delete(f"{STUDENT_API}/emis_no/{st.query_params['delete_std']}")
            st.query_params.clear()
            st.rerun()
except: st.info("மாணவர்கள் இல்லை.")
