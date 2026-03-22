import streamlit as st
import pandas as pd

# 1. பக்க அமைப்பு
st.set_page_config(page_title="கணிணி வினாடி வினா ", layout="wide")

# --- தலைப்பு மற்றும் இடைவெளி சரிசெய்தல் CSS ---
st.markdown("""
    <style>
    /* பக்கத்தின் மொத்த இடைவெளியைச் சரிசெய்ய */
    .main .block-container {
        padding-top: 3rem; 
        padding-left: 2rem;
        padding-right: 2rem;
    }
    
    /* தலைப்பு வரிசை - சற்று கீழே இறக்கப்பட்டுள்ளது */
    .header-row {
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        width: 100%;
        margin-top: 10px;
        margin-bottom: 10px;
        padding: 10px;
        background-color: white;
        z-index: 100;
    }
    
    .school-info {
        flex: 3;
        text-align: left;
    }

    .school-name {
        color: #1E88E5;
        font-size: clamp(1.5rem, 3.5vw, 2.5rem);
        font-weight: bold;
        margin: 0;
        line-height: 1.2;
    }
    
    .exam-name {
        font-size: clamp(1rem, 1.5vw, 1.3rem);
        color: #555;
        margin: 5px 0 0 0;
    }

    /* வினா எண் கட்டம் - தெளிவான தோற்றம் */
    .question-box {
        flex: 1;
        max-width: 180px;
        background-color: #f0f2f6;
        padding: 12px;
        border-radius: 8px;
        border: 2px solid #1E88E5;
        text-align: center;
        font-size: 1.2rem;
        font-weight: bold;
        color: #333;
        margin-left: 20px;
    }

    hr { margin-top: 5px; margin-bottom: 15px; border: 0; border-top: 1px solid #ddd; }
    </style>
    """, unsafe_allow_html=True)

# --- Caching வசதி ---
@st.cache_data(ttl=300)
def get_quiz_data(url):
    data = pd.read_csv(url)
    data.columns = data.columns.str.strip()
    return data

# 2. உங்கள் கூகிள் ஷீட் CSV லிங்க்
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSQwApSEm-2EfhP7PVMuZVBUcrD0XGr3tMXMTpX2j-9m5gB3xPgECBEsXjqTtBmW7lnFcrIVuOycN7V/pub?output=csv"

if 'current_q' not in st.session_state:
    st.session_state.current_q = 0
if 'user_answers' not in st.session_state:
    st.session_state.user_answers = {}
if 'submitted' not in st.session_state:
    st.session_state.submitted = False

try:
    df = get_quiz_data(SHEET_URL)
    total_qs = len(df)

    # பக்கவாட்டுப் பட்டி
    st.sidebar.title("👤 மாணவர் விவரம்")
    user_name = st.sidebar.text_input("பெயரை உள்ளிடவும்:", placeholder="உங்கள் பெயர்")
    st.sidebar.divider()

    if not st.session_state.submitted:
        col1, col2 = st.columns([7, 3])

        with col1:
            q_idx = st.session_state.current_q
            row = df.iloc[q_idx]

            # --- தலைப்பு மற்றும் வினா எண் ஒரே வரிசையில் ---
            st.markdown(f"""
                <div class="header-row">
                    <div class="school-info">
                        <p class="school-name">அரசு மேல்நிலைப்பள்ளி தேவனாங்குறிச்சி</p>
                        <p class="exam-name">அலகுத் தேர்வு - 2026</p>
                    </div>
                    <div class="question-box">
                        வினா {q_idx + 1} / {total_qs}
                    </div>
                </div>
            """, unsafe_allow_html=True)
            
            st.markdown("<hr>", unsafe_allow_html=True)
            
            # வினா விவரங்கள்
            st.caption(f"பாடம்: {row['Subject Code']} | அலகு: {row['Lesson Code']}")
            st.markdown("### " + row['Question Text'])
            
            options = [str(row['Ans-1']), str(row['Ans-2']), str(row['Ans-3']), str(row['Ans-4'])]
            prev_ans = st.session_state.user_answers.get(q_idx, None)
            
            selected = st.radio("சரியான விடையைத் தேர்ந்தெடுக்கவும்:", options, 
                                index=options.index(prev_ans) if prev_ans in options else None,
                                key=f"q_radio_{q_idx}")

            if selected:
                st.session_state.user_answers[q_idx] = selected

            st.divider()
            
            # பொத்தான்கள்
            b_col1, b_col2, b_col3 = st.columns([2, 2, 3])
            with b_col1:
                if q_idx > 0 and st.button("⬅️ முந்தைய", use_container_width=True):
                    st.session_state.current_q -= 1
                    st.rerun()
            with b_col2:
                if q_idx < total_qs - 1 and st.button("அடுத்தது ➡️", use_container_width=True):
                    st.session_state.current_q += 1
                    st.rerun()
            with b_col3:
                if q_idx == total_qs - 1 and st.button("✅ தேர்வைச் சமர்ப்பி", use_container_width=True, type="primary"):
                    if not user_name: st.sidebar.error("பெயரை உள்ளிடவும்!")
                    else:
                        st.session_state.submitted = True
                        st.rerun()

        with col2:
            st.markdown("### 🔢 வினா பலகம்")
            grid_cols = st.columns(4) 
            for i in range(total_qs):
                with grid_cols[i % 4]:
                    btn_type = "primary" if i == st.session_state.current_q else "secondary"
                    label = f"{i+1} ✅" if i in st.session_state.user_answers else f"{i+1}"
                    if st.button(label, key=f"nav_{i}", use_container_width=True, type=btn_type):
                        st.session_state.current_q = i
                        st.rerun()

    else:
        # தேர்வு முடிவுகள்
        score = 0
        st.header(f"📊 தேர்வு முடிவுகள்: {user_name}")
        for i, row in df.iterrows():
            u_ans = st.session_state.user_answers.get(i, "பதிலளிக்கவில்லை")
            correct = str(row['Anser'])
            if u_ans == correct: score += 1
            with st.expander(f"வினா {i+1}: {'சரி ✅' if u_ans == correct else 'தவறு ❌'}"):
                st.write(f"**வினா:** {row['Question Text']}")
                st.write(f"**உங்கள் விடை:** {u_ans}")
                st.write(f"**சரியான விடை:** {correct}")
        
        st.metric("மொத்த மதிப்பெண்", f"{score} / {total_qs}")
        if st.button("🔄 மீண்டும் தேர்வு"):
            st.session_state.submitted = False
            st.session_state.user_answers = {}
            st.session_state.current_q = 0
            st.rerun()

except Exception as e:
    st.error(f"பிழை: {e}")