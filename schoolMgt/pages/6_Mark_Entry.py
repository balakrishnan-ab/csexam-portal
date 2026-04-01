import streamlit as st
import streamlit.components.v1 as components
import requests
import pandas as pd

BASE_URL = "https://script.google.com/macros/s/AKfycbzgqCZ6f-kwO46eZPWb_Tr7gz-JdLQSSOL8kVLzRbhPIrinmdQrGiNjNHYIYANNPO8xYg/exec"

st.set_page_config(page_title="Mark Entry JS", layout="wide")

@st.cache_data(ttl=60)
def fetch_all_data():
    try:
        e = requests.get(f"{BASE_URL}?sheet=Exams", allow_redirects=True).json()
        c = requests.get(f"{BASE_URL}?sheet=Classes", allow_redirects=True).json()
        g = requests.get(f"{BASE_URL}?sheet=Groups", allow_redirects=True).json()
        s = requests.get(f"{BASE_URL}?sheet=Subjects", allow_redirects=True).json()
        st_list = requests.get(f"{BASE_URL}?sheet=Students", allow_redirects=True).json()
        return e, c, g, s, st_list
    except: return [], [], [], [], []

st.title("✍️ மதிப்பெண் உள்ளீடு (JS Fast Update)")

exams, classes, groups, subjects, students = fetch_all_data()
if not exams or not classes: st.stop()

# 1. தேர்வு மற்றும் வகுப்புத் தேர்வு
c1, c2 = st.columns(2)
sel_exam = c1.selectbox("தேர்வு", [e['exam_name'] for e in exams])
sel_class = c2.selectbox("வகுப்பு", [c['class_name'] for c in classes])

target_group = next((c['group_name'] for c in classes if c['class_name'] == sel_class), "")
group_info = next((g for g in groups if g['group_name'] == target_group), None)

if group_info:
    sub_list = [s.strip() for s in str(group_info['subjects']).split(',')]
    sel_sub = st.selectbox("பாடம்", sub_list)
    sub_idx = sub_list.index(sel_sub) + 1
    col_prefix = f"Sub{sub_idx}"
    sub_info = next((s for s in subjects if s['subject_name'] == sel_sub), {"eval_type": "90 + 10"})
    eval_type = sub_info['eval_type']
else: st.stop()

st.divider()

if students:
    df = pd.DataFrame(students)
    df_f = df[df['class_name'] == sel_class].sort_values(by=['Gender', 'student_name'], ascending=[True, True])
    
    if not df_f.empty:
        # ⚡ JavaScript-ஐ இயக்க ஒரு பட்டன்
        st.markdown("### ⚡ விரைவுச் செயல்பாடுகள்")
        c_js1, c_js2 = st.columns(2)
        
        # JavaScript Code: இது பிரவுசரில் உள்ள அனைத்து Input பெட்டிகளையும் தேடி மதிப்பெண் இடும்
        js_code = """
        <script>
        function fillMarks(type, value) {
            const inputs = parent.document.querySelectorAll('input[type="text"]');
            inputs.forEach(input => {
                // Aria-label அல்லது பெட்டியின் பெயரைக் கொண்டு அடையாளம் காணுதல்
                if (input.getAttribute('aria-label') === type || input.placeholder === type) {
                    input.value = value;
                    // Streamlit-க்கு தகவல் அனுப்ப ஒரு 'input' ஈவென்ட் தேவை
                    input.dispatchEvent(new Event('input', { bubbles: True }));
                }
            });
        }
        </script>
        """
        components.html(js_code, height=0)

        # பட்டன்கள்
        if c_js1.button("✅ அனைவருக்கும் 10 (Internal)"):
            st.toast("Internal மதிப்பெண்கள் நிரப்பப்படுகின்றன...")
            # இங்கு JS மூலம் மதிப்பெண் இடலாம் (குறிப்பு: Streamlit Form-க்குள் இது சவாலானது)
            
        # ---------------------------------------------------------
        # மீண்டும் அதே Form முறை, ஆனால் மேம்படுத்தப்பட்ட வேகத்துடன்
        # ---------------------------------------------------------
        with st.form("marks_form_js"):
            f1, f2 = st.columns(2)
            auto_i = f1.toggle("அனைவருக்கும் Internal (10)")
            auto_p = f2.toggle("அனைவருக்கும் Practical (20)") if "70" in eval_type else False

            save_data = []
            h = st.columns([0.5, 2, 1, 1, 1]) if "70" in eval_type else st.columns([0.5, 2, 1, 1])
            h[0].write("தேர்வு"); h[1].write("பெயர்")
            
            for _, row in df_f.iterrows():
                cols = st.columns([0.5, 2, 1, 1, 1]) if "70" in eval_type else st.columns([0.5, 2, 1, 1])
                is_sel = cols[0].checkbox(" ", value=auto_i or auto_p, key=f"s_{row['emis_no']}", label_visibility="collapsed")
                cols[1].write(f"**{row['student_name']}**")
                
                if "70" in eval_type:
                    t = cols[2].text_input("Theory", key=f"t_{row['emis_no']}", label_visibility="collapsed")
                    p = cols[3].text_input("Prac", value="20" if (auto_p) else "", key=f"p_{row['emis_no']}", label_visibility="collapsed")
                    i = cols[4].text_input("Int", value="10" if (auto_i) else "", key=f"i_{row['emis_no']}", label_visibility="collapsed")
                    if is_sel or t or p or i:
                        save_data.append({"action": "upsert", "exam_id": sel_exam, "emis_no": row['emis_no'], f"{col_prefix}_T": t, f"{col_prefix}_P": p, f"{col_prefix}_I": i})
                else:
                    e = cols[2].text_input("Exam", key=f"e_{row['emis_no']}", label_visibility="collapsed")
                    i = cols[3].text_input("Int", value="10" if (auto_i) else "", key=f"i_{row['emis_no']}", label_visibility="collapsed")
                    if is_sel or e or i:
                        save_data.append({"action": "upsert", "exam_id": sel_exam, "emis_no": row['emis_no'], f"{col_prefix}_T": e, f"{col_prefix}_I": i})

            if st.form_submit_button("🚀 சேமி", use_container_width=True):
                requests.post(f"{BASE_URL}?sheet=Marks", json={"data": save_data}, allow_redirects=True)
                st.success("வெற்றிகரமாகச் சேமிக்கப்பட்டது!")
                st.rerun()
