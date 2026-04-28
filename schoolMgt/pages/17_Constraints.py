import streamlit as st
from supabase import create_client

# Supabase இணைப்பு
supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

st.set_page_config(page_title="நிபந்தனை மேலாண்மை", layout="centered")
st.title("⚙️ நிபந்தனை மேலாண்மை")
st.markdown("---")

# தரவை ஏற்றி காட்டவும்
rules_data = supabase.table("timetable_rules").select("*").execute().data
rules_dict = {r['rule_name']: r['rule_value'] for r in rules_data}

with st.form("rules_form"):
    st.subheader("🗓️ கால அட்டவணை அமைப்பு")
    col1, col2 = st.columns(2)
    with col1:
        periods_day = st.number_input("ஒரு நாளைக்கு பாடவேளைகள்:", 1, 10, int(rules_dict.get("periods_day", 8)))
    with col2:
        working_days = st.number_input("வாரத்தின் வேலை நாட்கள்:", 5, 7, int(rules_dict.get("working_days", 6)))
    
    st.markdown("---")
    st.subheader("👨‍🏫 ஆசிரியர் & வகுப்பு விதிகள்")
    max_consecutive = st.number_input("அதிகபட்ச தொடர் பாடவேளைகள்:", 1, 4, int(rules_dict.get("max_consecutive", 3)))
    
    col3, col4 = st.columns(2)
    with col3:
        min_class_per_day = st.checkbox("குறைந்தபட்சம் ஒரு நாளைக்கு ஒரு வகுப்பு ஒரு பாடம்", value=rules_dict.get("min_class_per_day") == "True")
    with col4:
        ct_first = st.checkbox("வகுப்பாசிரியர் முதல் பாடவேளை", value=rules_dict.get("ct_first") == "True")

    st.markdown("---")
    st.subheader("📊 பாடத் திட்டமிடல்")
    priority_subjects = st.multiselect("முன்னுரிமை பாடங்கள்:", ["Tamil", "English", "Maths", "Science", "Social"], default=rules_dict.get("priority_subjects", []))
    
    if st.form_submit_button("✅ அனைத்து விதிகளையும் சேமிக்கவும்"):
        rules = [
            {"rule_name": "periods_day", "rule_value": str(periods_day)},
            {"rule_name": "working_days", "rule_value": str(working_days)},
            {"rule_name": "max_consecutive", "rule_value": str(max_consecutive)},
            {"rule_name": "min_class_per_day", "rule_value": str(min_class_per_day)},
            {"rule_name": "ct_first", "rule_value": str(ct_first)},
            {"rule_name": "priority_subjects", "rule_value": ",".join(priority_subjects)}
        ]
        supabase.table("timetable_rules").upsert(rules).execute()
        st.success("நிபந்தனைகள் பாதுகாப்பாகச் சேமிக்கப்பட்டன!")
