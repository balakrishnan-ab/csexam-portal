import streamlit as st
import pandas as pd
import random
from datetime import datetime

# 1. பக்க அமைப்பு
st.set_page_config(page_title="தேர்வு மையம்", layout="wide")

# --- CSS: துல்லியமான பொத்தான் மற்றும் பலக வடிவமைப்பு ---
st.markdown("""
    <style>
    .block-container { padding-top: 1.5rem; }
    .header-row { display: flex; justify-content: space-between; align-items: center; width: 100%; margin-bottom: 10px; }
    .school-name { color: #1E88E5; font-size: clamp(1.2rem, 3vw, 2.2rem); font-weight: bold; margin: 0; }
    
    /* வினா பலக வட்டங்கள் மட்டும் */
    .nav-btn-style {
        border-radius: 50% !important;
        width: 45px !important;
        height: 45px !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        font-weight: bold !important;
        padding: 0 !important;
        margin: 5px auto !important;
    }

    /* சாதாரண பொத்தான்கள் (அடுத்து, முந்தைய, லாகின்) - செவ்வக வடிவம் */
    div.stButton > button:not([key*="nav_"]) {
        border-radius: 5px !important;
        padding: 10px 25px !important;
        width: 100% !important;
        height: auto !important;
    }
    
    .certificate-box { border: 10px double #1E88E5; padding: 40px; text-align: center; background: white; margin-top: 20px; }
    </style>
    """, unsafe_allow_html=True)

@st.cache_data(ttl=60)
def get_data(url):
    data = pd.read_csv(url)
    data.columns = data.columns.str.strip()
    return data

# உங்கள் கூகிள் ஷீட் CSV லிங்க்
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSQwApSEm-2EfhP7PVMuZVBUcrD0XGr3tMXMTpX2j-9m5gB3xPgECBEsXjqTtBmW7lnFcrIVuOycN7V/pub?output=csv" 

# செஷன் ஸ்டேட் மேலாண்மை
if 'page' not in st.session_state: st.session_state.page = 'login'
if 'user_answers' not in st.session_state: st.session_state.user_answers = {}
if 'shuffled_indices' not in st.session_state: st.session_state.shuffled_indices = None
if 'current_q_idx' not in st.session_state: st.session_state.current_q_idx = 0

try:
    df = get_data(SHEET_URL)
    total_qs = len(df)
    section_limit = 25

    if st.session_state.shuffled_indices is None:
        indices = list(range(total_qs))
        random.shuffle(indices)
        st.session_state.shuffled_indices = indices

    # --- 1. லாகின் பக்கம் ---
    if st.session_state.page == 'login':
        st.markdown("<h1 style='text-align:center;'>அரசு மேல்நிலைப்பள்ளி தேவனாங்குறிச்சி</h1>", unsafe_allow_html=True)
        st.divider()
        col1, col2, col3 = st.columns([1,2,1])
        with col2:
            name = st.text_input("மாணவர் பெயர்:", key="user_name_input")
            if st.button("தேர்வைத் தொடங்கு ➡️", type="primary"):
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
        
        col_main, col_nav = st.columns([7, 3])
        
        with col_main:
            st.markdown(f'<div class="header-row"><p class="school-name">அரசு மேல்நிலைப்பள்ளி</p><h3>வினா {q_ptr + 1} / {total_qs}</h3></div>', unsafe_allow_html=True)
            st.caption(f"மாணவர்: {st.session_state.user_name}")
            st.divider()
            
            st.markdown("##### சரியான விடையைத் தேர்ந்தெடுக்கவும்:")
            st.write(f"### {row['Question Text']}")
            
            # விடைகளைக் கலக்குதல்
            opts = [str(row['Ans-1']), str(row['Ans-2']), str(row['Ans-3']), str(row['Ans-4'])]
            if f"opts_{actual_idx}" not in st.session_state:
                random.shuffle(opts)
                st.session_state[f"opts_{actual_idx}"] = opts
            
            # விடைத் தேர்வு
            current_options = st.session_state[f"opts_{actual_idx}"]
            selected_ans = st.radio("விடைகள்:", current_options, key=f"r_{actual_idx}", 
                                   index=current_options.index(st.session_state.user_answers[actual_idx]) if actual_idx in st.session_state.user_answers else None)
            
            if selected_ans
