import streamlit as st
import pandas as pd
import random
from datetime import datetime

# 1. பக்க அமைப்பு
st.set_page_config(page_title="Exam Portal - GHSS Devanankurichi", layout="wide")

# --- CSS: மொபைல் மற்றும் கணினி இரண்டிற்கும் ஏற்ற வடிவமைப்பு ---
st.markdown("""
    <style>
    /* மொபைலில் மேல்பகுதி மறையாமல் இருக்க */
    .block-container { padding-top: 1rem !important; padding-bottom: 1rem !important; }
    
    /* பள்ளித் தலைப்பு - Responsive Text */
    .school-header {
        text-align: center;
        background-color: #f0f7ff;
        padding: 15px;
        border-radius: 12px;
        border: 2px solid #1E88E5;
        margin-bottom: 15px;
    }
    .school-name { color: #0D47A1; font-size: clamp(1.5rem, 5vw, 3rem); font-weight: bold; margin: 0; }
    
    /* வினா எண் பெட்டி */
    .q-counter-box {
        display: inline-block;
        background-color: #1E88E5;
        color: white;
        padding: 5px 12px;
        border-radius: 8px;
        font-size: 1rem;
        margin-top: 10px;
    }

    /* வினா பலக பொத்தான்கள் - மொபைலில் வரிசையாக இருக்க */
    [data-testid="stHorizontalBlock"] .stColumn {
        width: 18% !important; /* 5 பொத்தான்கள் ஒரு வரிசையில் வர */
        flex: 0 0 18% !important;
        min-width: 18% !important;
    }
    
    div[data-testid="stColumn"] button {
        width: 100% !important;
        height: 45px !important;
        padding: 0 !important;
        font-size: 0.9rem !important;
    }

    /* முக்கிய பொத்தான்கள் (அடுத்து, முந்தைய) */
    div.stButton > button:not([key*="nav_btn_"]) {
        width: 100% !important;
        height: 50px !important;
        font-weight: bold !important;
        border-radius: 10px !important;
    }
    
    /* மதிப்பீடு அட்டைகள் */
    .result-card { padding: 12px; border-radius: 10px; margin-bottom: 8px; border-left: 8px solid; background-color: #f9f9f9; font-size: 0.9rem; }
    </style>
    """, unsafe_allow_html=True)

@st.cache_data(ttl=60)
def get_data(url):
    try:
        data = pd.read_csv(url)
        data.columns = data.columns.str.strip()
        return data.dropna(subset=['Question Text'])
    except: return pd.DataFrame()

SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSQwApSEm-2EfhP7PVMuZVBUcrD0XGr3tMXMTpX2j-9m5gB3xPgECBEsXjqTtBmW7lnFcrIVuOycN7V/pub?output=csv"

if 'page' not in st.session_state: st.session_state.page = 'login'
if 'user_answers' not in st.session_state: st.session_state.user_answers = {}
if 'visited' not in st.session_state: st.session_state.visited = set()
if 'marked' not in st.session_state: st.session_state.marked = set()
if 'shuffled_indices' not in st.session_state: st.session_state.shuffled_indices = None
if 'current_q_idx' not in st.session_state: st.session_state.current_q_idx = 0

try:
    df = get_data(SHEET_URL)
    if not df.empty:
        total_qs = len(df)
        if st.session_state.shuffled_indices is None:
            indices = list(range(total_qs))
            random.shuffle(indices)
            st.session_state.shuffled_indices = indices

        # --- லாகின் ---
        if st.session_state.page == 'login':
            st.markdown("<h2 style='text-align:center;'>அரசு மேல்நிலைப்பள்ளி தேவனாங்குறிச்சி</h2>", unsafe_allow_html=True)
            name = st.text_input("மாணவர் பெயர்:", key="m_login")
            if st.button("தேர்வைத் தொடங்கு ➡️", type="primary"):
                if name: st.session_state.user_name = name; st.session_state.page = 'quiz'; st.rerun()

        # --- வினாடி வினா ---
        elif st.session_state.page == 'quiz':
            q_ptr = st.session_state.current_q_idx
            idx = st.session_state.shuffled_indices[q_ptr]
            row = df.iloc[idx]
            st.session_state.visited.add(idx)
            
            st.markdown(f"""
            <div class="school-header">
                <p class="school-name">அரசு மேல்நிலைப்பள்ளி தேவனாங்குறிச்சி</p>
                <div class="q-counter-box">வினா {q_ptr + 1} / {total_qs}</div>
                <p style="margin-top:5px; font-size:0.9rem;">{row.get('Subject Code', 'CS')} | {row.get('Lesson Code', 'Unit-1')}</p>
            </div>
            """, unsafe_allow_html=True)

            # மொபைலில் வினா முதலில் வர வேண்டும், பலகம் கீழே வரலாம்
            st.write(f"### {row['Question Text']}")
            opts = [str(row['Ans-1']), str(row['Ans-2']), str(row['Ans-3']), str(row['Ans-4'])]
            if f"opts_{idx}" not in st.session_state:
                random.shuffle(opts)
                st.session_state[f"opts_{idx}"] = opts
            
            ans = st.radio("விடை:", st.session_state[f"opts_{idx}"], key=f"r_{idx}", 
                           index=st.session_state[f"opts_{idx}"].index(st.session_state.user_answers[idx]) if idx in st.session_state.user_answers else None)
            if ans: st.session_state.user_answers[idx] = ans

            st.checkbox("🤔 சந்தேகம் (Mark for Review)", value=(idx in st.session_state.marked), key=f"m_{idx}", on_change=lambda: st.session_state.marked.add(idx) if st.session_state[f"m_{idx}"] else st.session_state.marked.discard(idx))

            # கட்டுப்பாட்டு பொத்தான்கள்
            col_b1, col_b2 = st.columns(2)
            with col_b1:
                if q_ptr > 0 and st.button("⬅️ முந்தைய"): st.session_state.current_q_idx -= 1; st.rerun()
            with col_b2:
                if q_ptr < total_qs - 1 and st.button("அடுத்தது ➡️"): st.session_state.current_q_idx += 1; st.rerun()
            
            if (q_ptr + 1) % 25 == 0 or (q_ptr + 1) == total_qs:
                if st.button("மதிப்பீடு செய் 🚩", type="primary"): st.session_state.page = 'choice'; st.rerun()

            st.divider()
            # வினா பலகம் - கீழே மாற்றப்பட்டுள்ளது (மொபைல் வசதிக்காக)
            st.markdown("<p style='text-align:center; font-weight:bold;'>🔢 வினா பலகம்</p>", unsafe_allow_html=True)
            start_s = (q_ptr // 25) * 25
            end_s = min(start_s + 25, total_qs)
            
            grid = st.columns(5) # மொபைலிலும் 5 காலம்களாக இருக்கும்
            for i in range(start_s, end_s):
                ix = st.session_state.shuffled_indices[i]
                with grid[(i - start_s) % 5]:
                    dot = "⚪"
                    if ix in st.session_state.marked: dot = "🟠"
                    elif ix in st.session_state.user_answers: dot = "🟢"
                    elif ix in st.session_state.visited: dot = "🔵"
                    
                    if st.button(f"{dot}\n{i+1}", key=f"nav_btn_{i}", type="primary" if i==q_ptr else "secondary"):
                        st.session_state.current_q_idx = i; st.rerun()

        # --- மதிப்பீடு / சான்றிதழ் ---
        elif st.session_state.page == 'evaluate_view':
            st.header(f"📊 மதிப்பீடு: {st.session_state.user_name}")
            score = 0
            limit = st.session_state.current_q_idx + 1
            for i in range(limit):
                idx = st.session_state.shuffled_indices[i]
                u_ans = st.session_state.user_answers.get(idx, "பதிலளிக்கவில்லை")
                correct = str(df.iloc[idx]['Answer'])
                is_ok = (str(u_ans) == correct)
                if is_ok: score += 1
                
                clr = "#28a745" if is_ok else "#dc3545"
                st.markdown(f'<div class="result-card" style="border-left-color:{clr};"><b>வினா {i+1}:</b> {df.iloc[idx]["Question Text"]}<br>விடை: {u_ans} | சரியான விடை: <b>{correct}</b></div>', unsafe_allow_html=True)
            
            st.subheader(f"மதிப்பெண்: {score} / {limit}")
            if limit >= total_qs:
                if st.button("சான்றிதழ் 📜", type="primary"): st.session_state.page = 'certificate'; st.rerun()
            elif st.button("அடுத்த பகுதிக்கு ➡️"): st.session_state.current_q_idx += 1; st.session_state.page = 'quiz'; st.rerun()

        elif st.session_state.page == 'choice':
            st.markdown("<div style='text-align:center; padding:20px;'><h3>🎯 பகுதி நிறைவு</h3></div>", unsafe_allow_html=True)
            if st.button("மதிப்பீடு செய் ✅", type="primary"): st.session_state.page = 'evaluate_view'; st.rerun()
            if (st.session_state.current_q_idx + 1) < total_qs:
                if st.button("அடுத்த பகுதிக்கு ➡️"): st.session_state.current_q_idx += 1; st.session_state.page = 'quiz'; st.rerun()

except Exception as e: st.error(f"பிழை: {e}")
