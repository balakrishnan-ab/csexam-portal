import streamlit as st
import pandas as pd

# 1. பக்க அமைப்பு
st.set_page_config(page_title="கல்வி வினாடி வினா மையம்", layout="wide")

# --- CSS ஸ்டைல் ---
st.markdown("""
    <style>
    .main .block-container { padding-top: 2rem; }
    .header-row { display: flex; justify-content: space-between; align-items: flex-start; width: 100%; margin-bottom: 10px; }
    .school-name { color: #1E88E5; font-size: clamp(1.5rem, 3.5vw, 2.5rem); font-weight: bold; margin: 0; }
    .question-box { background-color: #f0f2f6; padding: 12px; border-radius: 8px; border: 2px solid #1E88E5; text-align: center; font-size: 1.2rem; font-weight: bold; min-width: 150px; }
    .result-card { padding: 15px; border-radius: 10px; margin-bottom: 10px; border-left: 5px solid; }
    .correct-card { background-color: #d4edda; border-left-color: #28a745; }
    .wrong-card { background-color: #f8d7da; border-left-color: #dc3545; }
    hr { margin: 10px 0; }
    </style>
    """, unsafe_allow_html=True)

@st.cache_data(ttl=60)
def get_quiz_data(url):
    data = pd.read_csv(url)
    data.columns = data.columns.str.strip()
    return data

# 2. உங்கள் கூகிள் ஷீட் CSV லிங்க்
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSQwApSEm-2EfhP7PVMuZVBUcrD0XGr3tMXMTpX2j-9m5gB3xPgECBEsXjqTtBmW7lnFcrIVuOycN7V/pub?output=csv" 

if 'current_q' not in st.session_state: st.session_state.current_q = 0
if 'user_answers' not in st.session_state: st.session_state.user_answers = {}
if 'submitted' not in st.session_state: st.session_state.submitted = False

try:
    df = get_quiz_data(SHEET_URL)
    total_qs = len(df)
    
    user_name = st.sidebar.text_input("மாணவர் பெயர்:", value="", key="name_input")

    if not st.session_state.submitted:
        col1, col2 = st.columns([7, 3])
        with col1:
            q_idx = st.session_state.current_q
            row = df.iloc[q_idx]
            st.markdown(f'<div class="header-row"><div class="school-info"><p class="school-name">அரசு மேல்நிலைப்பள்ளி தேவனாங்குறிச்சி</p><p>அலகுத் தேர்வு - 2026</p></div><div class="question-box">வினா {q_idx + 1} / {total_qs}</div></div>', unsafe_allow_html=True)
            st.markdown("<hr>", unsafe_allow_html=True)
            st.write(f"### {row['Question Text']}")
            options = [str(row['Ans-1']), str(row['Ans-2']), str(row['Ans-3']), str(row['Ans-4'])]
            prev_ans = st.session_state.user_answers.get(q_idx, None)
            selected = st.radio("சரியான விடையைத் தேர்ந்தெடுக்கவும்:", options, index=options.index(prev_ans) if prev_ans in options else None, key=f"q_{q_idx}")
            if selected: st.session_state.user_answers[q_idx] = selected
            
            st.divider()
            b_col1, b_col2, b_col3 = st.columns([2, 2, 3])
            with b_col1:
                if q_idx > 0 and st.button("⬅️ முந்தைய"): 
                    st.session_state.current_q -= 1
                    st.rerun()
            with b_col2:
                if q_idx < total_qs - 1 and st.button("அடுத்தது ➡️"): 
                    st.session_state.current_q += 1
                    st.rerun()
            with b_col3:
                if q_idx == total_qs - 1 and st.button("✅ தேர்வைச் சமர்ப்பி", type="primary"):
                    if not user_name: st.sidebar.error("பெயரை உள்ளிடவும்!")
                    else: 
                        st.session_state.submitted = True
                        st.rerun()

        with col2:
            st.markdown("### 🔢 வினா பலகம்")
            grid_cols = st.columns(4)
            for i in range(total_qs):
                with grid_cols[i % 4]:
                    label = f"{i+1} ✅" if i in st.session_state.user_answers else f"{i+1}"
                    if st.button(label, key=f"nav_{i}", use_container_width=True, type="primary" if i == st.session_state.current_q else "secondary"):
                        st.session_state.current_q = i
                        st.rerun()

    else:
        # --- மேம்படுத்தப்பட்ட தேர்வு முடிவுகள் பகுதி ---
        score = 0
        st.header(f"📊 தேர்வு முடிவுகள்: {user_name}")
        st.divider()
        
        for i, row in df.iterrows():
            u_ans = st.session_state.user_answers.get(i, "பதிலளிக்கவில்லை")
            correct = str(row['Answer'])
            is_correct = (u_ans == correct)
            if is_correct: score += 1
            
            # வினா வாரியாக முடிவுகளைக் காட்டுதல்
            card_style = "correct-card" if is_correct else "wrong-card"
            icon = "✅ சரி" if is_correct else "❌ தவறு"
            
            st.markdown(f"""
                <div class="result-card {card_style}">
                    <p style="font-weight: bold; margin-bottom: 5px;">வினா {i+1}: {icon}</p>
                    <p style="margin-bottom: 5px;"><strong>கேள்வி:</strong> {row['Question Text']}</p>
                    <p style="margin-bottom: 2px;">உங்கள் விடை: <span style="color: {'green' if is_correct else 'red'}">{u_ans}</span></p>
                    {'' if is_correct else f'<p style="margin-bottom: 2px; font-weight: bold; color: green;">சரியான விடை: {correct}</p>'}
                </div>
            """, unsafe_allow_html=True)

        st.divider()
        st.balloons()
        st.metric("மொத்த மதிப்பெண்", f"{score} / {total_qs}")
        if st.button("🔄 மீண்டும் தேர்வு எழுது"):
            st.session_state.submitted = False
            st.session_state.user_answers = {}
            st.session_state.current_q = 0
            st.rerun()

except Exception as e:
    st.error(f"பிழை: {e}")
