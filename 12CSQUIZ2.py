import streamlit as st
import pandas as pd
import random
from datetime import datetime

# 1. பக்க அமைப்பு
st.set_page_config(page_title="12 கணினி அறிவியல் தேர்வு ", layout="wide")

# --- CSS ஸ்டைல் ---
st.markdown("""
    <style>
    .certificate-box {
        border: 10px double #1E88E5;
        padding: 50px;
        text-align: center;
        background-color: white;
        color: #333;
        margin-top: 20px;
    }
    .header-row { display: flex; justify-content: space-between; align-items: center; }
    .school-name { color: #1E88E5; font-size: 2rem; font-weight: bold; }
    .result-card { padding: 10px; border-radius: 5px; margin-bottom: 5px; border-left: 5px solid; }
    .correct { background-color: #d4edda; border-left-color: #28a745; }
    .wrong { background-color: #f8d7da; border-left-color: #dc3545; }
    </style>
    """, unsafe_allow_html=True)

@st.cache_data(ttl=60)
def get_data(url):
    data = pd.read_csv(url)
    data.columns = data.columns.str.strip()
    return data

SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSQwApSEm-2EfhP7PVMuZVBUcrD0XGr3tMXMTpX2j-9m5gB3xPgECBEsXjqTtBmW7lnFcrIVuOycN7V/pub?output=csv" 

# செஷன் ஸ்டேட்
if 'page' not in st.session_state: st.session_state.page = 'login'
if 'user_answers' not in st.session_state: st.session_state.user_answers = {}
if 'shuffled_indices' not in st.session_state: st.session_state.shuffled_indices = None
if 'current_q_idx' not in st.session_state: st.session_state.current_q_idx = 0

try:
    df = get_data(SHEET_URL)
    total_questions = len(df)
    section_limit = 25

    if st.session_state.shuffled_indices is None:
        indices = list(range(total_questions))
        random.shuffle(indices)
        st.session_state.shuffled_indices = indices

    # --- 1. லாகின் பக்கம் ---
    if st.session_state.page == 'login':
        st.markdown("<h1 style='text-align:center;'>அரசு மேல்நிலைப்பள்ளி தேவனாங்குறிச்சி</h1>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1,2,1])
        with col2:
            name = st.text_input("மாணவர் பெயர்:")
            if st.button("தேர்வைத் தொடங்கு ➡️", type="primary", use_container_width=True):
                if name:
                    st.session_state.user_name = name
                    st.session_state.page = 'quiz'
                    st.rerun()
                else: st.error("பெயரை உள்ளிடவும்!")

    # --- 2. வினாடி வினா பக்கம் ---
    elif st.session_state.page == 'quiz':
        q_ptr = st.session_state.current_q_idx
        actual_idx = st.session_state.shuffled_indices[q_ptr]
        row = df.iloc[actual_idx]
        
        st.markdown(f'<div class="header-row"><p class="school-name">அரசு மேல்நிலைப்பள்ளி</p><h3>வினா {q_ptr + 1} / {total_questions}</h3></div>', unsafe_allow_html=True)
        st.divider()
        
        st.markdown("##### சரியான விடையைத் தேர்ந்தெடுக்கவும்:")
        st.write(f"### {row['Question Text']}")
        
        opts = [str(row['Ans-1']), str(row['Ans-2']), str(row['Ans-3']), str(row['Ans-4'])]
        if f"opts_{actual_idx}" not in st.session_state:
            random.shuffle(opts)
            st.session_state[f"opts_{actual_idx}"] = opts
        
        ans = st.radio("விடைகள்:", st.session_state[f"opts_{actual_idx}"], key=f"r_{actual_idx}", index=None)
        if ans: st.session_state.user_answers[actual_idx] = ans

        st.divider()
        # 25 வினாக்கள் முடிந்தவுடன் அல்லது கடைசி வினாவில்
        if (q_ptr + 1) % section_limit == 0 or (q_ptr + 1) == total_questions:
            if st.button("பகுதியை முடிக்க 🚩", type="primary", use_container_width=True):
                st.session_state.page = 'choice'
                st.rerun()
        else:
            if st.button("அடுத்த வினா ➡️", use_container_width=True):
                st.session_state.current_q_idx += 1
                st.rerun()

    # --- 3. விருப்பத் தேர்வு பக்கம் (Choice Page) ---
    elif st.session_state.page == 'choice':
        st.subheader("📍 இந்தப் பகுதி நிறைவுற்றது")
        st.write("நீங்கள் இந்தப் பகுதிக்கான விடைகளை இப்போது மதிப்பீடு செய்ய விரும்புகிறீர்களா? அல்லது நேரடியாக அடுத்த பகுதிக்குச் செல்ல விரும்புகிறீர்களா?")
        
        c1, c2 = st.columns(2)
        with c1:
            if st.button("மதிப்பீடு செய் (Result) 📊", use_container_width=True):
                st.session_state.page = 'evaluate'
                st.rerun()
        with c2:
            q_ptr = st.session_state.current_q_idx
            if (q_ptr + 1) < total_questions:
                if st.button("அடுத்த பகுதிக்குச் செல் ➡️", use_container_width=True, type="primary"):
                    st.session_state.current_q_idx += 1
                    st.session_state.page = 'quiz'
                    st.rerun()
            else:
                st.write("இதுவே கடைசிப் பகுதி. தயவுசெய்து 'மதிப்பீடு செய்' பொத்தானை அழுத்தவும்.")

    # --- 4. மதிப்பீடு மற்றும் சான்றிதழ் ---
    elif st.session_state.page == 'evaluate':
        q_ptr = st.session_state.current_q_idx
        # இது வரை எழுதிய அனைத்து வினாக்களையும் மதிப்பீடு செய்யும்
        # அல்லது அந்தப் பகுதியை மட்டும் காட்ட விரும்பினால் start_ptr பயன்படுத்தலாம்
        st.header(f"📊 தேர்வு மதிப்பீடு")
        
        overall_score = 0
        for i in range(q_ptr + 1):
            idx = st.session_state.shuffled_indices[i]
            u_ans = st.session_state.user_answers.get(idx, "பதிலளிக்கவில்லை")
            correct = str(df.iloc[idx]['Answer'])
            is_ok = (u_ans == correct)
            if is_ok: overall_score += 1
            
            # வினாக்களைக் காட்டுதல் (விரும்பினால் இதை மட்டும் எக்ஸ்பாண்டரில் வைக்கலாம்)
            with st.expander(f"வினா {i+1}: {'✅' if is_ok else '❌'}"):
                st.write(f"**கேள்வி:** {df.iloc[idx]['Question Text']}")
                st.write(f"உங்கள் விடை: {u_ans} | சரியான விடை: {correct}")

        st.divider()
        if (q_ptr + 1) < total_questions:
            st.metric("இது வரையிலான மதிப்பெண்", f"{overall_score} / {q_ptr + 1}")
            if st.button("அடுத்த பகுதிக்குத் தொடரவும் ➡️", type="primary"):
                st.session_state.current_q_idx += 1
                st.session_state.page = 'quiz'
                st.rerun()
        else:
            # சான்றிதழ்
            st.balloons()
            st.markdown(f"""
                <div class="certificate-box">
                    <h1 style="color:#1E88E5;">வெற்றிச் சான்றிதழ்</h1>
                    <p style="font-size:1.5rem;">மாணவர் <b>{st.session_state.user_name}</b></p>
                    <p>அரசு மேல்நிலைப்பள்ளி தேவனாங்குறிச்சி நடத்திய தேர்வில்</p>
                    <h2>{overall_score} / {total_questions}</h2>
                    <p>மதிப்பெண்கள் பெற்றுள்ளார்.</p>
                    <p>நாள்: {datetime.now().strftime('%d-%m-%Y')}</p>
                </div>
            """, unsafe_allow_html=True)
            if st.button("மீண்டும் தேர்வு எழுத 🔄"):
                st.session_state.clear()
                st.rerun()

except Exception as e:
    st.error(f"பிழை: {e}")
