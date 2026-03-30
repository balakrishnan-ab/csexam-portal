import streamlit as st
import requests
import pandas as pd

STUDENT_API = "https://sheetdb.io/api/v1/sb3mxuvdynqos?sheet=Students"
CLASS_API = "https://sheetdb.io/api/v1/sb3mxuvdynqos?sheet=Classes"

st.set_page_config(page_title="Students", layout="wide")

# மொபைல் திரையில் ஒரே வரியில் தெரிய CSS
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
    classes_res = requests.get(CLASS_API).json()
    class_list = [c['class_name'] for c in classes_res] if isinstance(classes_res, list) else []
except: class_list = []

# 2. மாணவர் சேர்க்கை (Entry)
with st.expander("➕ புதிய மாணவர் / Excel பதிவேற்றம்", expanded=False):
    tab1, tab2 = st.tabs(["தனிச் சேர்க்கை", "Excel மூலம் மொத்தமாக"])
    
    with tab1:
        s_name = st.text_input("மாணவர் பெயர்")
        c1, c2 = st.columns(2)
        s_emis = c1.text_input("EMIS எண்")
        
        # பாலினம் தேர்வு (ஆங்கிலத்தில் சேமிக்கப்படும்)
        gender_map = {"மாணவர்": "Male", "மாணவி": "Female"}
        s_gen_display = c2.selectbox("பாலினம்", list(gender_map.keys()))
        s_gen_value = gender_map[s_gen_display]
        
        c3, c4 = st.columns(2)
        s_phone = c3.text_input("போன் எண்")
        s_class = c4.selectbox("வகுப்பு", class_list, key="single_entry")
        
        if st.button("💾 மாணவரைச் சேமி", use_container_width=True):
            if s_name and s_class:
                payload = {
                    "emis_no": s_emis, "student_name": s_name, 
                    "Gender": s_gen_value, "class_name": s_class, "phone_no": s_phone
                }
                requests.post(STUDENT_API, json={"data": [payload]})
                st.success("மாணவர் சேர்க்கப்பட்டார்!")
                st.rerun()

    with tab2:
        st.info("Excel-ல் 'emis_no', 'student_name', 'Gender' (Male/Female), 'class_name', 'phone_no' இருக்க வேண்டும்.")
        uploaded_file = st.file_uploader("அனைத்து வகுப்பு மாணவர் பட்டியலை பதிவேற்றவும்", type=['csv', 'xlsx'])
        
        if uploaded_file and st.button("🚀 மொத்தமாகப் பதிவேற்று"):
            try:
                # கோப்பைப் படித்தல்
                df = pd.read_csv(uploaded_file) if uploaded_file.name.endswith('.csv') else pd.read_excel(uploaded_file)
                
                # --- மிக முக்கியம்: காலி இடங்களை (NaN) நீக்குதல் ---
                df = df.fillna("") 
                
                # தரவை JSON-ஆக மாற்றி அனுப்புதல்
                data_to_send = df.to_dict(orient='records')
                res = requests.post(STUDENT_API, json={"data": data_to_send})
                
                if res.status_code == 201:
                    st.success(f"வெற்றிகரமாக {len(df)} மாணவர் விவரங்கள் பதிவேற்றப்பட்டன!")
                    st.rerun()
                else:
                    st.error(f"பிழை: {res.text}")
            except Exception as e:
                st.error(f"பிழை ஏற்பட்டது: {e}")

st.divider()

# 3. மாணவர் பட்டியல்
st.subheader("📋 மாணவர் பட்டியல்")
view_cls = st.selectbox("வகுப்பைத் தேர்வு செய்க", ["அனைத்து வகுப்புகள்"] + class_list)

try:
    students = requests.get(STUDENT_API).json()
    if students and isinstance(students, list):
        html_code = """
        <table class="student-table">
            <tr>
                <th style="width: 45%;">பெயர்</th>
                <th style="width: 20%;">பாலினம்</th>
                <th style="width: 20%;">வகுப்பு</th>
                <th style="width: 15%;">நீக்க</th>
            </tr>"""
        
        for s in students:
            if view_cls == "அனைத்து வகுப்புகள்" or s.get('class_name') == view_cls:
                n_val = s.get('student_name', '')
                g_raw = s.get('Gender', '')
                g_display = "மாணவர்" if g_raw == "Male" else "மாணவி" if g_raw == "Female" else g_raw
                c_val = s.get('class_name', '')
                e_val = s.get('emis_no', '')
                
                html_code += f"""
                <tr>
                    <td><b>{n_val}</b></td>
                    <td>{g_display}</td>
                    <td>{c_val}</td>
                    <td>
                        <a href="?delete_std={e_val}" target="_self" 
                           style="text-decoration:none; background:#ff4b4b; color:white; padding:3px 8px; border-radius:4px; font-size:10px;">🗑️</a>
                    </td>
                </tr>"""
        
        html_code += "</table>"
        st.markdown(html_code, unsafe_allow_html=True)

        # நீக்குதல் லாஜிக்
        query_params = st.query_params
        if "delete_std" in query_params:
            requests.delete(f"{STUDENT_API}/emis_no/{query_params['delete_std']}")
            st.query_params.clear()
            st.rerun()
    else:
        st.info("மாணவர் விவரங்கள் ஏதுமில்லை.")
except:
    st.error("தரவுகளைப் பெறுவதில் சிக்கல்!")
