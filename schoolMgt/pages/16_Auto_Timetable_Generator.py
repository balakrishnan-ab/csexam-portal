import streamlit as st
import pandas as pd

st.title("⚙️ ஆட்டோ-ஜெனரேட் டைம்டேபிள் - எடிட்டர்")

# Tabs உருவாக்கம்
tab1, tab2 = st.tabs(["👨‍🏫 ஆசிரியர் வாரியாக", "🏫 வகுப்பு வாரியாக"])

# தற்காலிக தரவு (Example Data)
if 'temp_tt' not in st.session_state:
    st.session_state.temp_tt = pd.DataFrame(index=["Mon", "Tue", "Wed", "Thu", "Fri"], columns=[str(i) for i in range(1, 9)]).fillna("-")

with tab1:
    st.subheader("ஆசிரியர் வாரியான தற்காலிக அட்டவணை")
    # எக்செல் போன்ற எடிட்டர்
    edited_teacher_tt = st.data_editor(st.session_state.temp_tt, use_container_width=True)

with tab2:
    st.subheader("வகுப்பு வாரியான தற்காலிக அட்டவணை")
    # எக்செல் போன்ற எடிட்டர்
    edited_class_tt = st.data_editor(st.session_state.temp_tt, use_container_width=True)

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
