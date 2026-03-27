import streamlit as st
import pandas as pd
import random
import requests
from datetime import datetime

# 1. பக்க அமைப்பு
st.set_page_config(page_title="GHSS Devanankurichi - Pro Exam Portal", layout="wide")

# --- CSS: கச்சிதமான வடிவமைப்பு ---
st.markdown("""
    <style>
    .school-header { text-align: center; background-color: #f0f7ff; padding: 20px; border-radius: 12px; border: 2px solid #1E88E5; margin-bottom: 20px; }
    .school-name { color: #0D47A1; font-size: 2.2rem !important; font-weight: bold; margin: 0; }
    .q-box { border: 1px solid #ddd; padding: 20px; border-radius: 10px; background: white; margin-bottom: 10px; }
    div[data-testid="stColumn"] button { padding: 5px !important; height: 45px !important; width: 100% !important; font-size: 0.9rem !important; }
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

# செஷன் ஸ்டேட் தொடக்கம்
if 'page' not in st.session_state: st.session_state.page = 'login'
if 'user_answers' not in st.session_state: st.session_state.user_answers = {}
if 'visited' not in st.session_state: st.session_state.visited = set()
if 'marked' not in st.session_state: st.session_state.marked = set()
if 'current_q_idx' not in st.session_state: st.session_state.current_q_idx = 0
if 'options_map' not in st.session_state: st.session_state.options_map = {}
if 'score_saved' not in st.session_state: st.session_state.score_saved = False

try:
    df_raw = get_data(SHEET_URL)

    # --- 1. லாகின் பக்கம் ---
    if st.session_state.page == 'login':
        st.markdown('<div class="school-header"><p class="school-name">அரசு மேல்நிலைப்பள்ளி தேவனாங்குறிச்சி</p></div>', unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1,2,1])
        with col2:
            st.subheader("🎓 மாணவர் லாகின்")
            name = st.text_input("மாணவர் பெயர்:", value=st.session_state.get('user_name', ''))
            
            if not df_raw.empty:
                # 1. வகுப்பு தேர்வு
                std_list = sorted(df_raw['Standard'].unique().tolist()) if 'Standard' in df_raw.columns else ["10", "12"]
                sel_std = st.selectbox("வகுப்பு:", std_list)
                df_std = df_raw[df_raw['Standard'].astype(str) == str(sel_std)]
                
                # 2. பாடம் தேர்வு
                sub_list = sorted(df_std['Subject Code'].unique().tolist())
                sel_sub = st.selectbox("பாடம்:", sub_list)
                df_sub = df_std[df_std['Subject Code'] == sel_sub]
                
                # 3. அலகு (Lesson) தேர்வு - புதிய வசதி
                lesson_col = 'Lesson Code' if 'Lesson Code' in df_sub.columns else ('Lesson' if 'Lesson' in df_sub.columns else None)
                final_df = df_sub.copy()
                
                if lesson_col:
                    lesson_list = sorted(df_sub[lesson_col].unique().tolist())
                    sel_lessons = st
