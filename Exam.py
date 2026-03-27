import streamlit as st
import pandas as pd
import random
import requests
from datetime import datetime

# 1. பக்க அமைப்பு
st.set_page_config(page_title="GHSS Devanankurichi - Exam Portal", layout="wide")

# --- CSS: கச்சிதமான வினா பலகம் மற்றும் வடிவமைப்பு ---
st.markdown("""
    <style>
    .school-header { text-align: center; background-color: #f0f7ff; padding: 20px; border-radius: 12px; border: 2px solid #1E88E5; margin-bottom: 20px; }
    .school-name { color: #0D47A1; font-size: 2.2rem !important; font-weight: bold; margin: 0; }
    .q-box { border: 1px solid #ddd; padding: 20px; border-radius: 10px; background: white; margin-bottom: 10px; }
    
    /* வினா பலக பொத்தான்கள் - நெருக்கமாக அடுக்க */
    div[data-testid="stColumn"] button {
        padding: 5px !important;
        height: 45px !important;
        width: 100% !important;
        min-width: 45px !important;
        font-size: 0.9rem !important;
        margin: 2px 0px !important;
    }
    
    /* பலக பெட்டி (Container) */
    .nav-container {
        background-color: #f9f9f9;
        padding: 10px;
        border-radius: 10px;
        border: 1px solid #eee;
    }

    .option-box { padding: 12px; border-radius: 8px; margin: 6px 0; border: 1px solid #ddd; }
    .opt-correct { background-color: #d4edda; border-left: 10px solid #28a745; font-weight: bold; }
    .opt-wrong { background-color: #f8d7da; border-left: 10px solid #dc3545; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- மதிப்பெண் சேமிக்கும் செயல்பாடு ---
def save_score(name, std, subject, score, total):
    API_URL = "https://sheetdb.io/api/v1/w7ktpqhwxaiy9" 
    data = {"Name": name, "Standard": std, "Datetime": datetime.now().strftime("%d-%m-%Y %H:%M"), "Subject": subject, "Score": score, "Total": total}
    try: requests.post(API_URL, json={"data": [data]})
    except: pass

@st.cache_data(ttl=60)
def get_data(url):
    try:
        data = pd.read_csv(url)
        data.columns = data.columns.str.strip()
        return data.dropna(subset=['Question Text'])
    except: return pd.DataFrame()

SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSQwApSEm-2EfhP7PVMuZVBUcrD0XGr3tMXMTpX2j-9m5gB3xPgECBEsXjqTtBmW7lnFcrIVuOycN7V/pub?output=csv"

# செஷன் ஸ்டேட்
if 'page' not in st.session_state: st.session_state.page = 'login'
if 'user_answers' not in st.session_state: st.session_state.user_answers = {}
if 'visited' not in st.session_state: st.session_state.visited = set()
if 'marked' not in st.session_state: st.session_state.marked = set()
if 'current_q_idx' not in st.session_state: st.session_state.current_q_idx = 0
if 'options_map' not in st.session_state: st.session_state.options_map = {}
if 'score_saved' not in st.session_state: st.session_state.score_saved = False

try:
    df_raw = get_data(SHEET_URL)

    if st.session_state.page == 'login':
        st.markdown('<div class="school-header"><p class="school-name">அரசு மேல்நிலைப்பள்ளி தேவனாங்குறிச்சி</p></div>', unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1,2,1])
        with col2:
            st.subheader("🎓 மாணவர் லாகின்")
            name = st.text_input("மாணவர் பெயர்:")
            if not df_raw.empty:
                std_list = sorted(df_raw['Standard'].unique().tolist()) if 'Standard' in df_raw.columns else ["10", "12"]
                sel_std = st.selectbox("வகுப்பு (Standard):", std_list)
                df_std = df_raw[df_raw['Standard'].astype(str) == str(sel_std)]
                med_list = sorted(df_std['Medium'].unique().tolist()) if 'Medium' in df_std.columns else ["தமிழ்"]
                sel_med = st.selectbox("பயிற்று மொழி:", med_list)
                df_med = df_std[df_std['Medium'] == sel_med]
                sub_list = sorted(df_med['Subject Code'].unique().tolist())
                sel_sub = st.selectbox("பாடம்:", sub_list)
                df_sub = df_med[df_med['Subject Code'] == sel_sub]
                num_q = st.number_input(f"வினாக்கள் எண்ணிக்கை:", 1, len(df_sub), min(25, len(df_sub)))
                
                if st.button("தேர்வைத் தொடங்கு ➡️", type="primary") and name:
                    st.session_state.user_name, st.session_state.selected_std, st.session_state.selected_subject = name, sel_std, sel_sub
                    st.session_state.filtered_df = df_sub.sample(n=num_q).reset_index(drop=True)
                    st.session_state.options_map = {i: random.sample([str(df_sub.iloc[i][f'Ans-{j}']) for j in range(1,5)], 4) for i in range(len(st.session_state.filtered_df))}
                    st.session_state.page = 'quiz'; st.rerun()

    elif st.session_state.page == 'quiz':
        df, q_idx = st.session_state.filtered_df, st.session_state.current_q_idx
        row = df.iloc[q_idx]
        st.session_state.visited.add(q_idx)
        st.markdown('<div class="school-header"><p class="school-name">அரசு மேல்நிலைப்பள்ளி தேவனாங்குறிச்சி</p></div>', unsafe_allow_html=True)
        
        m_
