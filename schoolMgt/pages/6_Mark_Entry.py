import streamlit as st
import requests
import pandas as pd

# 1. பக்க அமைப்பு
st.set_page_config(page_title="Mark Entry", layout="wide")

# 2. URL அமைப்புகள் (Streamlit Secrets-ல் BASE_URL இருக்க வேண்டும்)
try:
    BASE_URL = st.secrets["BASE_URL"]
except:
    st.error("BASE_URL கண்டறியப்படவில்லை!")
    st.stop()

# 3. ⚡ மின்னல் வேகத்தில் தரவுகளைப் பெறுதல் (Single Fetch)
@st.cache_data(ttl=300)
def fetch_everything():
    try:
        # நாம் புதிய ஸ்கிரிப்ட்டில் செய்தபடி அனைத்து சீட்களும் ஒரே முறையில் வரும்
        res = requests.get(BASE_URL).json()
        return res
    except Exception as e:
        st.error(f"தொடர்பு கொள்வதில் பிழை: {e}")
        return None

# தரவுகளை ஒருமுறை மட்டும் எடுத்தல்
all_data = fetch_everything()

if not all_data:
    st.warning("கூகுள் சீட்டில் இருந்து தகவல்கள் வரவில்லை. URL-ஐச் சரிபார்க்கவும்.")
    st.stop()

# தரவுகளை தனித்தனியாகப் பிரித்தல்
exams = all_data.get('exams', [])
classes = all_data.get('classes', [])
groups = all_data.get('groups', [])
subjects = all_data.get('subjects', [])
students = all_data.get('students', [])

# 4. மின்னல் வேக Sync லாஜிக்
def sync_all():
    m_tick = st.session_state.master_tick
    m_int = st.session_state.get('master_int', False)
    m_prac = st.session_state.get('master_prac', False)
    
    for key in list(st.session_state.keys()):
        if key.startswith("chk_"):
            st.session_state[key] = m_tick
            emis = key.split("_")[1]
            if m_tick:
                if m_int and f"i_{emis}" in st.session_state: st.session_state[f"i_{emis}"] = "10"
                if m_prac and f"p_{emis}" in st.session_state: st.session_state[f"p_{emis}"] = "20"

st.title("✍️ மதிப்பெண் உள்ளீடு")

# 5. தேர்வுகள் (Dropdowns)
c1, c2, c3 = st.columns(3)
sel_exam = c1.selectbox("தேர்வு", [e['exam_name'] for e in exams])
sel_class = c2.selectbox("வகுப்பு", [c['class_name'] for c in classes])

# வகுப்பு வாரியான பாடம் மற்றும் பிரிவு
target_group = next((c['group_name'] for c in classes if c['class_name'] == sel_class), "")
group_info = next((g for g in groups if g['group_name'] == target_group), None)

if group_info:
    sub_list = [s.strip() for s in str(group_info['subjects']).split(',')]
    sel_sub = c3.selectbox("பாடம்", sub_list)
    sub_idx = sub_list.index(sel_sub) + 1
    col_prefix = f"Sub{sub_idx}" # எ.கா: Sub1
    sub_info = next((s for s in subjects if s['subject_name'] == sel_sub), {"eval_type": "90+10"})
    eval_type = sub_info['eval_type']
else:
    st.error("பாடப்பிரிவு விவரங்கள் இல்லை.")
    st.stop()

st.divider()

# 6. மாணவர் பட்டியல் மற்றும் படிவம்
if students:
    df = pd.DataFrame(students)
    # அந்த வகுப்பு மாணவர்களை மட்டும் பிரித்தல்
    df_f = df[df['class_name'] == sel_class].sort_values(by='student_name')
    
    if not df_f.empty:
        # மாஸ்டர் கண்ட்ரோல்கள்
        m1, m2, m3 = st.columns(3)
        m1.checkbox("அனைவரையும் தேர்வு செய்", key="master_tick", on_change=sync_all)
        m2.checkbox("Internal (10) வழங்கு", key="master_int", on_change=sync_all)
        is_70 = "70" in eval_type
        if is_70: m3.checkbox("Practical (20) வழங்கு", key="master_prac", on_change=sync_all)

        with st.form("mark_form"):
            save_list = []
            # அட்டவணை தலைப்பு (Roll No சேர்க்கப்பட்டுள்ளது)
            h = st.columns([0.5, 1, 2, 1, 1, 1]) if is_70 else st.columns([0.5, 1, 2, 1, 1])
            h[0].write("Sel"); h[1].write("Roll No"); h[2].write("Name")
            
            for _, row in df_f.iterrows():
                emis = str(row['emis_no'])
                roll = str(row.get('roll_no', '-')) # சீட்டில் roll_no காலம் இருக்க வேண்டும்
                cols = st.columns([0.5, 1, 2, 1, 1, 1]) if is_70 else st.columns([0.5, 1, 2, 1, 1])
                
                selected = cols[0].checkbox(" ", key=f"chk_{emis}", label_visibility="collapsed")
                cols[1].write(f"`{roll}`")
                cols[2].write(row['student_name'])
                
                entry = {"exam_id": sel_exam, "emis_no": emis}
                
                if is_70:
                    t = cols[3].text_input("T", key=f"t_{emis}", label_visibility="collapsed")
                    p = cols[4].text_input("P", key=f"p_{emis}", label_visibility="collapsed")
                    i = cols[5].text_input("I", key=f"i_{emis}", label_visibility="collapsed")
                    if selected:
                        entry.update({f"{col_prefix}_T": t, f"{col_prefix}_P": p, f"{col_prefix}_I": i})
                        save_list.append(entry)
                else:
                    e = cols[3].text_input("E", key=f"e_{emis}", label_visibility="collapsed")
                    i = cols[4].text_input("I", key=f"i_{emis}", label_visibility="collapsed")
                    if selected:
                        entry.update({f"{col_prefix}_T": e, f"{col_prefix}_I": i})
                        save_list.append(entry)

            if st.form_submit_button("🚀 மதிப்பெண்களைச் சேமி", use_container_width=True):
                if save_list:
                    with st.spinner("சேமிக்கப்படுகிறது..."):
                        requests.post(BASE_URL, json={"data": save_list})
                        st.success("வெற்றிகரமாக அப்டேட் செய்யப்பட்டது!")
                        st.rerun()
                else:
                    st.warning("மாணவர்களைத் தேர்வு செய்யவும்.")
else:
    st.info("மாணவர்கள் பட்டியல் காலியாக உள்ளது.")
