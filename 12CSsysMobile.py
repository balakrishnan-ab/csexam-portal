import streamlit as st
import pandas as pd
import random
from datetime import datetime

# 1. பக்க அமைப்பு
st.set_page_config(page_title="Exam Portal - GHSS Devanankurichi", layout="wide")

# --- CSS: வலதுபுற வினா பலகம் மற்றும் பெரிய வட்டப் பொத்தான்கள் ---
st.markdown("""
    <style>
    .block-container { padding-top: 1.5rem !important; }
    
    /* பள்ளித் தலைப்பு */
    .school-header {
        text-align: center; background-color: #f0f7ff;
        padding: 20px; border-radius: 12px; border: 2px solid #1E88E5;
        margin-bottom: 20px;
    }
    .school-name { color: #0D47A1; font-size: clamp(1.5rem, 4vw, 2.5rem); font-weight: bold; margin: 0; }
    
    /* வினா எண் பெட்டி */
    .q-counter-box {
        display: inline-block; background-color: #1E88E5; color: white;
        padding: 5px 15px; border-radius: 8px; font-size: 1.1rem; margin-top: 5px;
    }

    /* வலதுபுற வினா பலகம் (Sidebar/Column) */
    .nav-column {
        background-color: #ffffff; padding: 15px;
        border: 1px solid #ddd; border-radius: 10px;
        box-shadow: 2px 2px 10px rgba(0,0,0,0.05);
    }

    /* வட்ட வடிவப் பொத்தான்கள் - பெரியதாக */
    div[data-testid="stColumn"] button[key*="nav_btn_"] {
        border-radius: 50% !important;
        width: 55px !important;
        height: 55px !important;
        font-weight: bold !important;
        font-size: 1.2rem !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        margin: 8px auto !important;
        border: 2px solid #ccc !important;
    }

    /* நிலை வண்ணப் புள்ளிகள் */
    .dot-box { display: flex; justify-content: center; margin-bottom: -15px; }
    .status-dot { width: 12px; height: 12px; border-radius: 50%; border: 1px solid #999; }

    /* கட்டுப்பாட்டு பொத்தான்கள் (அடுத்து, முந்தைய) */
    div.stButton > button:not([key*="nav_btn_"]) {
        width: 100% !important; height: 50px !important;
        font-weight: bold !important; border-radius: 8px !important;
    }
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

        if st.session_state.page == 'login':
            st.markdown("<h2 style='text-align:center;'>அரசு மேல்நிலைப்பள்ளி தேவனாங்குறிச்சி</h2>", unsafe_allow_html=True)
            name = st.text_input("மாணவர் பெயர்:", key="login_v19")
            if st.button("தேர்வைத் தொடங்கு ➡️", type="primary"):
                if name: st.session_state.user_name = name; st.session_state.page = 'quiz'; st.rerun()

        elif st.session_state.page == 'quiz':
            q_ptr = st.session_state.current_q_idx
            idx = st.session_state.shuffled_indices[q_ptr]
            row = df.iloc[idx]
            st.session_state.visited.add(idx)
            
            # தலைப்பு
            st.markdown(f"""
            <div class="school-header">
                <p class="school-name">அரசு மேல்நிலைப்பள்ளி தேவனாங்குறிச்சி</p>
                <div class="q-counter-box">வினா {q_ptr + 1} / {total_qs}</div>
                <p style="margin-top:5px; font-weight:bold;">{row.get('Subject Code', 'CS')} | {row.get('Lesson Code', 'L-1')}</p>
            </div>
            """, unsafe_allow_html=True)

            col_main, col_nav = st.columns([7, 3])
            
            with col_main:
                st.caption(f"மாணவர்: {st.session_state.user_name}")
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
                b_col1, b_col2 = st.columns(2)
                with b_col1:
                    if q_ptr > 0 and st.button("⬅️ முந்தைய"): st.session_state.current_q_idx -= 1; st.rerun()
                with b_col2:
                    if q_ptr < total_qs - 1 and st.button("அடுத்தது ➡️"): st.session_state.current_q_idx += 1; st.rerun()
                
                if (q_ptr + 1) % 25 == 0 or (q_ptr + 1) == total_qs:
                    if st.button("மதிப்பீடு செய் 🚩", type="primary"): st.session_state.page = 'choice'; st.rerun()

            with col_nav:
                st.markdown("<div class='nav-column'><h5 style='text-align:center;'>🔢 வினா பலகம்</h5>", unsafe_allow_html=True)
                grid = st.columns(4) # 4 காலம்களாக மாற்றப்பட்டுள்ளது (பெரிய பொத்தான்களுக்காக)
                start_s = (q_ptr // 25) * 25
                end_s = min(start_s + 25, total_qs)
                
                for i in range(start_s, end_s):
                    ix = st.session_state.shuffled_indices[i]
                    with grid[(i - start_s) % 4]:
                        dot_c = "#eee"
                        if ix in st.session_state.marked: dot_c = "#FF9800"
                        elif ix in st.session_state.user_answers: dot_c = "#28a745"
                        elif ix in st.session_state.visited: dot_c = "#2196F3"
                        
                        st.markdown(f'<div class="dot-box"><div class="status-dot" style="background-color:{dot_c};"></div></div>', unsafe_allow_html=True)
                        if st.button(f"{i+1}", key=f"nav_btn_{i}", type="primary" if i==q_ptr else "secondary"):
                            st.session_state.current_q_idx = i; st.rerun()
                st.markdown("</div>", unsafe_allow_html=True)
                st.markdown("<p style='font-size:0.8rem; margin-top:10px; text-align:center;'>🟢 விடை | 🔵 பார்த்தது | 🟠 சந்தேகம்</p>", unsafe_allow_html=True)

        # --- மதிப்பீடு / சான்றிதழ் (வழக்கம் போல) ---
        elif st.session_state.page == 'choice':
            if st.button("மதிப்பீடு செய் ✅", type="primary"): st.session_state.page = 'evaluate'; st.rerun()
            if (st.session_state.current_q_idx + 1) < total_qs:
                if st.button("அடுத்த பகுதிக்குச் செல் ➡️"):
                    st.session_state.current_q_idx += 1; st.session_state.page = 'quiz'; st.rerun()

except Exception as e: st.error(f"பிழை: {e}")
