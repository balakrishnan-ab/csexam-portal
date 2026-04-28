import streamlit as st
from supabase import create_client

# Supabase இணைப்பு (Secrets-ஐப் பயன்படுத்தவும்)
supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

st.title("⚙️ நிபந்தனை மேலாண்மை (Constraints Manager)")

with st.form("rules_form"):
    work_days = st.radio("வேலை நாட்கள் (5 அல்லது 6):", [5, 6], index=1)
    max_consecutive = st.number_input("ஒரே வகுப்பு அதிகபட்ச தொடர் பாடவேளை:", 1, 4, 3)
    class_teacher_first = st.checkbox("வகுப்பாசிரியர் முதல் பாடத்தில் இருக்க வேண்டும்", value=True)
    
    if st.form_submit_button("விதிகளைச் சேமிக்கவும்"):
        rules = [
            {"rule_name": "work_days", "rule_value": str(work_days)},
            {"rule_name": "max_consecutive", "rule_value": str(max_consecutive)},
            {"rule_name": "ct_first", "rule_value": str(class_teacher_first)}
        ]
        supabase.table("timetable_rules").upsert(rules).execute()
        st.success("நிபந்தனைகள் Supabase-ல் சேமிக்கப்பட்டன!")
