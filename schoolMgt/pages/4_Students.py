import streamlit as st
import requests
import pandas as pd

STUDENT_API = "https://sheetdb.io/api/v1/sb3mxuvdynqos?sheet=Students"
CLASS_API = "https://sheetdb.io/api/v1/sb3mxuvdynqos?sheet=Classes"

st.set_page_config(page_title="Students", layout="wide")

# மொபைல் கச்சிதமான தோற்றம் (CSS)
st.markdown("""
    <style>
    .student-table { width: 100%; border-collapse: collapse; font-size: 13px; table-layout: fixed; }
    .student-table th, .student-table td { 
        border-bottom: 1px solid #eee; padding: 10px 4px; text-align: left; 
        overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
    }
    .student-table th { background-color: #f1f3f5; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

st.title("👨‍🎓 மாணவர் மேலாண்மை")

# 1. வகுப்புகளின் பட்டியலைப் பெறுதல்
try:
    classes = requests.get(CLASS_API).json()
    class_list = [c['class_name'] for c in classes] if isinstance(classes, list) else []
except: class_list = []

# 2. மாணவர் சேர்க்கை (Entry)
with st.expander("➕ புதிய மாணவர் / Excel பதிவேற்றம்", expanded=False):
    tab1, tab2 = st.tabs(["தனிச் சேர்க்கை", "Excel மூலம்"])
    
    with tab1:
        s_name = st.text_input("மாணவர் பெயர்")
        c1, c2 = st.columns(2)
        s_emis = c1.text_input("EMIS எண்")
        s_gen = c2.selectbox("பாலினம்", ["மாணவர்", "மாணவி", "இதர"])
        
        c3, c4 = st.columns(2)
        s_phone = c3.text_input("போன் எண்")
        s_class = c4.selectbox("வகுப்பு", class_list, key="single_entry")
        
        if st.button("💾 மாணவரைச் சேமி", use_container_width=True):
            if s_name and s_class:
                payload = {
                    "emis_no": s_emis, "student_name": s_name, 
                    "Gender": s_gen, "class_name": s_class, "phone_no": s_phone
                }
                requests.post(STUDENT_API, json={"data": [payload]})
                st.success("மாணவர் சேர்க்கப்பட்டார்!")
                st.rerun()

    with tab2:
        st.info("Excel-ல் 'emis_no', 'student_name', 'Gender', 'phone_no' தலைப்புகள் இருக்க வேண்டும்.")
        upl_class = st.selectbox("எந்த வகுப்புக்கு ஏற்ற வேண்டும்?", class_list, key="bulk_entry")
        uploaded_file = st.file_uploader("கோப்பைத் தேர்ந்தெடுக்கவும்", type=['csv', 'xlsx'])
        if uploaded_file and st.button("🚀 மொத்தமாகப் பதிவேற்று"):
            df = pd.read_csv(uploaded_file) if uploaded_file.name.endswith('.csv') else pd.read_excel(uploaded_file)
            df['class_name'] = upl_class
            requests.post(STUDENT_API, json={"data": df.to_dict(orient='records')})
            st.success("அனைத்து மாணவர்களும் சேர்க்கப்பட்டனர்!")
            st.rerun()

st.divider()

# 3. மாணவர் பட்டியல்
st.subheader("📋 மாணவர் பட்டியல்")
view_cls = st.selectbox("வகுப்பைத் தேர்வு செய்க", ["அனைத்தும்"] + class_list)

try:
    students = requests.get(STUDENT_API).json()
    if students:
        html_code = """
        <table class="student-table">
            <tr>
                <th style="width: 45%;">பெயர்</th>
                <th style="width: 20%;">பாலினம்</th>
                <th style="width: 20%;">EMIS</th>
                <th style="width: 15%;">நீக்க</th>
            </tr>"""
        
        for s in students:
            if view_cls == "அனைத்தும்" or s.get('class_name') == view_cls:
                n_val = s.get('student_name', '')
                g_val = s.get('Gender', '')
                e_val = s.get('emis_no', '')
                
                html_code += f"""
                <tr>
                    <td><b>{n_val}</b></td>
                    <td>{g_val}</td>
                    <td><small>{e_val}</small></td>
                    <td>
                        <a href="?delete_std={e_val}" target="_self" 
                           style="text-decoration:none; background:#ff4b4b; color:white; padding:3px 8px; border-radius:4px; font-size:10px;">🗑️</a>
                    </td>
                </tr>"""
        
        html_code += "</table>"
        st.markdown(html_code, unsafe_allow_html=True)

        if "delete_std" in st.query_params:
            requests.delete(f"{STUDENT_API}/emis_no/{st.query_params['delete_std']}")
            st.query_params.clear()
            st.rerun()
except: st.info("மாணவர்கள் இல்லை.")
