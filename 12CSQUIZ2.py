import streamlit as st
import pandas as pd

# 1. பக்க அமைப்பு
st.set_page_config(page_title="12 கணிணி அறிவியல் ", layout="wide")

# --- CSS ஸ்டைல் ---
st.markdown("""
    <style>
    .block-container { padding-top: 1.5rem; }
    .header-row { display: flex; justify-content: space-between; align-items: center; width: 100%; margin-bottom: 10px; }
    .school-name { color: #1E88E5; font-size: clamp(1.2rem, 3vw, 2.2rem); font-weight: bold; margin: 0; }
    .stButton>button { padding: 2px 5px; font-size: 12px; }
    .result-card { padding: 15px; border-radius: 8px; margin-bottom: 10px; border-left: 5px solid; }
    .correct-card { background-color: #d4edda; border-left-color: #28a745; }
    .wrong-card { background-color: #f8d7da; border-left-color: #dc3545; }
    .login-box { background: #f9f9f9; padding: 30px; border-radius: 15px; border: 1px solid #ddd; }
    </style>
    """, unsafe_allow_html=True)

@st.cache_data(ttl=60)
def get_quiz_data(url):
    data = pd.read_csv(url)
    data.columns = data.columns.str.strip()
    return data

# 2. கூகிள் ஷீட் CSV லிங்க்
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSQwApSEm-2EfhP7PVMuZVBUcrD0XGr3tMXMTpX2j-9m5gB3xPgECBEsXjqTtBmW7lnFcrIVuOycN7V/pub?output=csv" 

# செஷன் ஸ்டேட் மேலாண்மை
if 'page' not in st.session_state: st.session_state.page = 'login'
if 'current_q' not in st.session_state: st.session_state.current_q = 0
if 'user_answers' not in st.session_state: st.session_state.user_answers = {}

try:
    df = get_quiz_data(SHEET_URL)
    total_qs = len(df)
    section_size = 25 

    # --- 1. பெயர் பதிவு பக்கம் ---
    if st.session_state.page == 'login':
        st.markdown("<h1 style='text-align: center; color: #1E88E5;'>அரசு மேல்நிலைப்பள்ளி தேவனாங்குறிச்சி</h1>", unsafe_allow_html=True)
        st.divider()
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.markdown('<div class="login-box">', unsafe_allow_html=True)
            st.subheader("📝 மாணவர் நுழைவு")
            name = st.text_input("உங்கள் பெயர்:", placeholder="பெயரைத் தட்டச்சு செய்யவும்")
            std = st.selectbox("வகுப்பு:", ["10-ஆம் வகுப்பு", "11-ஆம் வகுப்பு", "12-ஆம் வகுப்பு"])
            if st.button("தேர்வைத் தொடங்கு ➡️", use_container_width=True, type="primary"):
                if name:
                    st.session_state.user_name = name
                    st.session_state.page = 'quiz'
                    st.rerun()
                else: st.error("பெயரை உள்ளிடவும்!")
            st.markdown('</div>', unsafe_allow_html=True)

    # --- 2. வினாடி வினா பக்கம் ---
    elif st.session_state.page == 'quiz':
        q_idx = st.session_state.current_q
        row = df.iloc[q_idx]
        
        col1, col2 = st.columns([7, 3])
        with col1:
            st.markdown(f'<div class="header-row"><p class="school-name">அரசு மேல்நிலைப்பள்ளி தேவனாங்குறிச்சி</p><div style="background:#f0f2f6; padding:8px; border-radius:5px; border:1px solid #1E88E5;">வினா {q_idx + 1} / {total_qs}</div></div>', unsafe_allow_html=True)
            st.caption(f"மாணவர்: {st.session_state.user_name}")
            st.divider()
            
            st.markdown("<p style='font-size:1.2rem; font-weight:bold; color:#555;'>சரியான விடையைத் தேர்ந்தெடுக்கவும்:</p>", unsafe_allow_html=True)
            st.write(f"### {row['Question Text']}")
            
            options = [str(row['Ans-1']), str(row['Ans-2']), str(row['Ans-3']), str(row['Ans-4'])]
            prev_ans = st.session_state.user_answers.get(q_idx, None)
            selected = st.radio("Options", options, index=options.index(prev_ans) if prev_ans in options else None, key=f"q_{q_idx}", label_visibility="collapsed")
            
            if selected: st.session_state.user_answers[q_idx] = selected
            
            st.divider()
            b1, b2 = st.columns([1, 1])
            with b1:
                if q_idx > 0 and st.button("⬅️ முந்தைய", use_container_width=True):
                    st.session_state.current_q -= 1
                    st.rerun()
            with b2:
                if (q_idx + 1) % section_size == 0 or q_idx == total_qs - 1:
                    btn_label = "பகுதியை மதிப்பீடு செய் 🚩" if q_idx < total_qs - 1 else "✅ தேர்வைச் சமர்ப்பி"
                    if st.button(btn_label, type="primary", use_container_width=True):
                        st.session_state.page = 'confirm_eval'
                        st.rerun()
                elif st.button("அடுத்தது ➡️", use_container_width=True):
                    st.session_state.current_q += 1
                    st.rerun()

        with col2:
            st.markdown("##### 🔢 வினா பலகம்")
            grid_cols = st.columns(5)
            start_q = (q_idx // section_size) * section_size
            end_q = min(start_q + section_size, total_qs)
            for i in range(start_q, end_q):
                with grid_cols[(i-start_q) % 5]:
                    label = f"{i+1}✅" if i in st.session_state.user_answers else f"{i+1}"
                    if st.button(label, key=f"n_{i}", use_container_width=True, type="primary" if i == q_idx else "secondary"):
                        st.session_state.current_q = i
                        st.rerun()

    # --- 3. உறுதிப்படுத்தும் பக்கம் ---
    elif st.session_state.page == 'confirm_eval':
        st.markdown("<h2 style='text-align:center;'>🎯 மதிப்பீடு உறுதி செய்தல்</h2>", unsafe_allow_html=True)
        st.write(f"வணக்கம் {st.session_state.user_name}, நீங்கள் இந்தப் பகுதியின் வினாக்களை நிறைவு செய்துள்ளீர்கள். இப்போது உங்கள் விடைகளை மதிப்பீடு செய்யலாமா?")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("சரி, மதிப்பீடு செய் ✅", use_container_width=True, type="primary"):
                st.session_state.page = 'section_result'
                st.rerun()
        with c2:
            if st.button("இல்லை, மீண்டும் சரிபார் ⬅️", use_container_width=True):
                st.session_state.page = 'quiz'
                st.rerun()

    # --- 4. மதிப்பீடு பக்கம் ---
    elif st.session_state.page == 'section_result':
        q_idx = st.session_state.current_q
        start_q = (q_idx // section_size) * section_size
        end_q = min(start_q + section_size, total_qs)
        
        st.header(f"📊 மதிப்பீடு (வினா {start_q+1} - {end_q})")
        score = 0
        for i in range(start_q, end_q):
            u_ans = st.session_state.user_answers.get(i, "பதிலளிக்கவில்லை")
            correct = str(df.iloc[i]['Answer'])
            is_correct = (u_ans == correct)
            if is_correct: score += 1
            style = "correct-card" if is_correct else "wrong-card"
            st.markdown(f'<div class="result-card {style}"><b>வினா {i+1}:</b> {df.iloc[i]["Question Text"]}<br>உங்கள் விடை: {u_ans} | சரியான விடை: <b>{correct}</b></div>', unsafe_allow_html=True)
        
        st.metric("மதிப்பெண்", f"{score} / {end_q - start_q}")
        if end_q < total_qs:
            if st.button("அடுத்த பகுதிக்குத் தொடரவும் ➡️", type="primary", use_container_width=True):
                st.session_state.current_q = end_q
                st.session_state.page = 'quiz'
                st.rerun()
        else:
            st.success("தேர்வு நிறைவுற்றது!")
            if st.button("🔄 மீண்டும் முதல் பகுதிக்கு"):
                st.session_state.clear()
                st.rerun()

except Exception as e:
    st.error(f"பிழை: {e}")
