import streamlit as st
import pandas as pd

st.title("⚙️ ஆட்டோ-ஜெனரேட் டைம்டேபிள் - எடிட்டர்")
# 'அனைவருக்கும் ஒதுக்கீடு' பட்டன்
if st.button("🤖 அனைவருக்கும் தானாக நிரப்பு (Auto-Assign All)"):
    # 1. ஒரு காலி DataFrame உருவாக்குதல்
    new_df = pd.DataFrame(index=["Mon", "Tue", "Wed", "Thu", "Fri", "Sat"], 
                          columns=[str(i) for i in range(1, 9)]).fillna("-")
    
    # 2. ஒதுக்கீட்டு தரவுகளைப் பெற்று பாடங்களை வரிசைப்படுத்துதல்
    # (இங்கே உங்கள் Supabase allot_data தரவுகளைப் பயன்படுத்தவும்)
    all_tasks = []
    for a in allot_data:
        # அந்த வகுப்புக்கு எத்தனை பாட வேளைகள் தேவையோ அத்தனை முறை சேர்ப்பது
        all_tasks.extend([a['class_name']] * a['periods_per_week'])
    
    # 3. சீரற்ற முறையில் பாடங்களை நிரப்புதல் (Simple Logic)
    # தேவைப்பட்டால் இங்கே Constraint Logic சேர்க்கலாம்
    idx = 0
    days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
    periods = [str(i) for i in range(1, 9)]
    
    for d in days:
        for p in periods:
            if idx < len(all_tasks):
                new_df.at[d, p] = all_tasks[idx]
                idx += 1
    
    # 4. session_state-ஐ புதுப்பித்தல்
    st.session_state.temp_tt = new_df
    st.rerun() # ரீ-ரன் செய்தால் எடிட்டரில் தரவு தானாகத் தெரியும்
# Tabs உருவாக்கம்
tab1, tab2 = st.tabs(["👨‍🏫 ஆசிரியர் வாரியாக", "🏫 வகுப்பு வாரியாக"])

# தற்காலிக தரவு (Example Data)
if 'temp_tt' not in st.session_state:
    st.session_state.temp_tt = pd.DataFrame(index=["Mon", "Tue", "Wed", "Thu", "Fri"], columns=[str(i) for i in range(1, 9)]).fillna("-")

with tab1:
    st.subheader("ஆசிரியர் வாரியான தற்காலிக அட்டவணை")
    # key="teacher_editor" என்று கொடுக்கவும்
    edited_teacher_tt = st.data_editor(
        st.session_state.temp_tt, 
        use_container_width=True, 
        key="teacher_editor"
    )

with tab2:
    st.subheader("வகுப்பு வாரியான தற்காலிக அட்டவணை")
    # key="class_editor" என்று கொடுக்கவும்
    edited_class_tt = st.data_editor(
        st.session_state.temp_tt, 
        use_container_width=True, 
        key="class_editor"
    )
# சேமிப்பு மற்றும் கைவிடும் பட்டன்கள்
col1, col2 = st.columns([1, 1])
with col1:
    if st.button("💾 சரி (Save)"):
        # இங்கே தரவுத்தளத்தில் (Supabase) சேமிக்கும் தர்க்கத்தை எழுதவும்
        st.session_state.temp_tt = edited_teacher_tt # தற்காலிக தரவை அப்டேட் செய்யவும்
        st.success("அட்டவணை வெற்றிகரமாகச் சேமிக்கப்பட்டது!")
with col2:
    if st.button("❌ கைவிடு (Discard)"):
        # தற்காலிக தரவை நீக்கிவிடலாம்
        st.warning("மாற்றங்கள் கைவிடப்பட்டன!")
        st.rerun()

st.info("குறிப்பு: 'சரி' கொடுத்தால் மட்டுமே மாற்றங்கள் தரவுத்தளத்தில் பதிவாகும்.")
