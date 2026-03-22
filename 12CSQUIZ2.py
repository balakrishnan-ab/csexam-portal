import streamlit as st
import pandas as pd
import random
from datetime import datetime

# 1. பக்க அமைப்பு
st.set_page_config(page_title="Exam Portal - GHSS Devanankurichi", layout="wide")

# --- CSS: பெரிய பொத்தான்கள் மற்றும் தலைப்பு ---
st.markdown("""
    <style>
    .block-container { padding-top: 2rem !important; }
    
    /* பள்ளித் தலைப்பு */
    .main-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        background-color: #f0f7ff;
        padding: 25px;
        border-radius: 15px;
        border: 2px solid #1E88E5;
        margin-bottom: 25px;
    }
    .school-name { color: #0D47A1; font-size: 3rem !important; font-weight: bold; margin: 0; }
    .exam-detail { font-size: 1.4rem; color: #333; font-weight: bold; }
    .q-counter-box {
        background-color: white;
        border: 3px solid #000;
        padding: 15px 25px;
        border-radius: 10px;
        font-size: 1.8rem;
        font-weight: bold;
        text-align: center;
    }

    /* அனைத்து முக்கிய பொத்தான்களையும் நீளமாக்க (Full Width) */
    div.stButton > button {
        width: 100% !important;
        height: 60px !important; /* உயரம் அதிகரிப்பு */
        font-size: 1.2rem !important;
        font-weight: bold !important;
        border-radius: 10px !important;
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    }

    /* வினா பலக வட்ட பொத்தான்கள் மட்டும் (சிறியதாக இருக்க) */
    div[data-testid="stColumn"] button[key*="nav_btn_"] {
        border-radius: 50% !important;
        width: 50px !important;
        height: 50px !important;
        font-size: 1rem !important;
        margin: 5px auto !important;
    }

    .nav-wrapper { display: flex; flex-direction: column; align-items: center; }
    .status-indicator { width: 12px; height: 12px; border-radius: 50%; margin-bottom: 4px; border: 1px solid #ccc; }
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

        # --- லாகின் பக்கம் ---
        if st.session_state.page == 'login':
            st.markdown("<h1 style='text-align:center;'>அரசு மேல்நிலைப்பள்ளி தேவனாங்குறிச்சி</h1>", unsafe_allow_html=True)
            col1, col2, col3 = st.columns([1,2,1])
            with col2:
                name = st.text_input("மாணவர் பெயர்:", key="login_v16")
                # இந்த பொத்தான் இப்போது நீளமாக இருக்கும்
                if st.button("தேர்வைத் தொடங்கு ➡️", type="primary"):
                    if name: st.session_state.user_name = name; st.session_state.page = 'quiz'; st.rerun()

        # --- வினாடி வினா பக்கம் ---
        elif st.session_state.page == 'quiz':
            q_ptr = st.session_state.current_q_idx
            idx = st.session_state.shuffled_indices[q_ptr]
            row = df.iloc[idx]
            st.session_state.visited.add(idx)
            
            st.markdown(f"""
            <div class="main-header">
                <div class="school-info">
                    <p class="school-name">அரசு மேல்நிலைப்பள்ளி - தேவனாங்குறிச்சி</p>
                    <p class="exam-detail">அலகுத் தேர்வு - 2026</p>
                </div>
                <div class="q-counter-box">வினா {q_ptr + 1} / {total_qs}</div>
            </div>
            """, unsafe_allow_html=True)

            col_main, col_nav = st.columns([7, 3])
            
            with col_main:
                st.caption(f"மாணவர்: {st.session_state.user_name} | பாடம்: {row.get('Subject Code', 'CS')}")
                st.write(f"### {row['Question Text']}")
                
                opts = [str(row['Ans-1']), str(row['Ans-2']), str(row['Ans-3']), str(row['Ans-4'])]
                if f"opts_{idx}" not in st.session_state:
                    random.shuffle(opts)
                    st.session_state[f"opts_{idx}"] = opts
                
                ans = st.radio("சரியான விடை:", st.session_state[f"opts_{idx}"], key=f"r_{idx}", 
                               index=st.session_state[f"opts_{idx}"].index(st.session_state.user_answers[idx]) if idx in st.session_state.user_answers else None)
                if ans: st.session_state.user_answers[idx] = ans

                st.checkbox("🤔 சந்தேகம் (Mark for Review)", value=(idx in st.session_state.marked), key=f"m_{idx}", on_change=lambda: st.session_state.marked.add(idx) if st.session_state[f"m_{idx}"] else st.session_state.marked.discard(idx))

                st.divider()
                # பொத்தான்கள் இப்போது மிக நீளமாக இருக்கும்
                n1, n2, n3 = st.columns([1, 1, 1])
                with n1:
                    if q_ptr > 0 and st.button("⬅️ முந்தைய"): st.session_state.current_q_idx -= 1; st.rerun()
                with n2:
                    if q_ptr < total_qs - 1 and st.button("அடுத்தது ➡️"): st.session_state.current_q_idx += 1; st.rerun()
                with n3:
                    if (q_ptr + 1) % 25 == 0 or (q_ptr + 1) == total_qs:
                        if st.button("மதிப்பீடு செய் 🚩", type="primary"): st.session_state.page = 'choice'; st.rerun()

            with col_nav:
                st.markdown("<h5 style='text-align:center;'>🔢 வினா பலகம்</h5>", unsafe_allow_html=True)
                grid = st.columns(5)
                start_s = (q_ptr // 25) * 25
                end_s = min(start_s + 25, total_qs)
                for i in range(start_s, end_s):
                    ix = st.session_state.shuffled_indices[i]
                    with grid[(i - start_s) % 5]:
                        dot = "#eee"
                        if ix in st.session_state.marked: dot = "#FF9800"
                        elif ix in st.session_state.user_answers: dot = "#28a745"
                        elif ix in st.session_state.visited: dot = "#2196F3"
                        st.markdown(f'<div class="nav-wrapper"><div class="status-indicator" style="background-color:{dot};"></div></div>', unsafe_allow_html=True)
                        if st.button(f"{i+1}", key=f"nav_btn_{i}", type="primary" if i==q_ptr else "secondary"):
                            st.session_state.current_q_idx = i; st.rerun()

        # --- மதிப்பீடு / சான்றிதழ் (வழக்கம் போல) ---
        elif st.session_state.page == 'choice' or st.session_state.page == 'evaluate':
             # (மதிப்பீடு மற்றும் சான்றிதழ் கோடிங் இங்கே வரும் - முந்தைய பதிப்பில் இருந்தது போல)
             if st.session_state.page == 'choice':
                st.markdown("<div style='text-align:center; padding:30px;'><h2>🎯 பகுதி நிறைவுற்றது</h2>", unsafe_allow_html=True)
                if st.button("மதிப்பீடு செய் ✅", type="primary"): st.session_state.page = 'evaluate'; st.rerun()
                if (st.session_state.current_q_idx + 1) < total_qs:
                    if st.button("அடுத்த பகுதிக்குச் செல் ➡️"): st.session_state.current_q_idx += 1; st.session_state.page = 'quiz'; st.rerun()
             elif st.session_state.page == 'evaluate':
                 st.write("மதிப்பீடு விவரங்கள் தயாராகின்றன...")
                 st.session_state.page = 'evaluate_final' # மதிப்பீட்டுப் பக்கத்திற்கு மாற்றுதல்
                 st.rerun()

except Exception as e: st.error(f"பிழை: {e}")
