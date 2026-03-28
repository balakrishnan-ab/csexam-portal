import streamlit as st
import pandas as pd
import random
import requests
from datetime import datetime

# 1. பக்க அமைப்பு
st.set_page_config(page_title="GHSS Devanankurichi - Exam Portal", layout="wide")

# --- CSS வடிவமைப்பு ---
st.markdown("""
    <style>
    .school-header { text-align: center; background-color: #f0f7ff; padding: 15px; border-radius: 12px; border: 2px solid #1E88E5; margin-bottom: 20px; }
    .school-name { color: #0D47A1; font-size: 2rem !important; font-weight: bold; margin: 0; }
    .q-box { border: 1px solid #ddd; padding: 20px; border-radius: 10px; background: white; margin-bottom: 10px; }
    .option-box { padding: 12px; border-radius: 8px; margin: 6px 0; border: 1px solid #ddd; }
    .opt-correct { background-color: #d4edda; border-left: 10px solid #28a745; font-weight: bold; }
    .opt-wrong { background-color: #f8d7da; border-left: 10px solid #dc3545; font-weight: bold; }
    div[data-testid="stColumn"] button { padding: 5px !important; height: 40px !important; width: 100% !important; }
    .lesson-tag { background-color: #E3F2FD; color: #1565C0; padding: 3px 10px; border-radius: 5px; font-size: 0.85rem; font-weight: bold; border: 1px solid #BBDEFB; }
    </style>
    """, unsafe_allow_html=True)

# --- மதிப்பெண் சேமிக்கும் செயல்பாடு (மேம்படுத்தப்பட்டது) ---
def save_score(name, std, subject, score, total):
    # உங்கள் SheetDB API URL
    API_URL = "https://sheetdb.io/api/v1/w7ktpqhwxaiy9" 
    
    # தரவு அனுப்புதல்
    data_to_send = {
        "name": str(name),
        "Standard": str(std),
        "Datetime": datetime.now().strftime("%d-%m-%Y %H:%M"),
        "Subject": str(subject),
        "Score": str(score),
        "Total": str(total)
    }
    
    try:
        # SheetDB-க்கு POST ரிக்வெஸ்ட்
        response = requests.post(API_URL, json=data_to_send, timeout=10)
        # SheetDB பொதுவாக 201 தரும், சில சமயம் 200 தரும்
        if response.status_code in [200, 201]:
            return True, "வெற்றி"
        else:
            return False, f"Status: {response.status_code}, Text: {response.text}"
    except Exception as e:
        return False, str(e)

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
if 'seen_ids' not in st.session_state: st.session_state.seen_ids = set()
if 'user_answers' not in st.session_state: st.session_state.user_answers = {}
if 'visited' not in st.session_state: st.session_state.visited = set()
if 'marked' not in st.session_state: st.session_state.marked = set()
if 'current_q_idx' not in st.session_state: st.session_state.current_q_idx = 0

try:
    df_raw = get_data(SHEET_URL)

    # --- 1. லாகின் பக்கம் ---
    if st.session_state.page == 'login':
        st.markdown('<div class="school-header"><p class="school-name">அரசு மேல்நிலைப்பள்ளி தேவனாங்குறிச்சி</p></div>', unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1,2,1])
        with col2:
            st.subheader("🎓 மாணவர் லாகின்")
            u_name = st.text_input("மாணவர் பெயர்:")
            
            if not df_raw.empty:
                std_list = sorted(df_raw['Standard'].unique().tolist())
                sel_std = st.selectbox("வகுப்பு:", std_list)
                df_std = df_raw[df_raw['Standard'].astype(str) == str(sel_std)]
                
                sub_list = sorted(df_std['Subject Code'].unique().tolist())
                sel_sub = st.selectbox("பாடம்:", sub_list)
                df_sub = df_std[df_std['Subject Code'] == sel_sub]
                
                # அலகு (Lesson) தேர்வு
                lesson_col = 'Lesson Code' if 'Lesson Code' in df_sub.columns else ('Lesson' if 'Lesson' in df_sub.columns else None)
                lesson_list = sorted(df_sub[lesson_col].unique().tolist()) if lesson_col else []
                sel_lessons = st.multiselect("அலகுகள் (Lessons):", lesson_list)
                
                pool = df_sub[df_sub[lesson_col].isin(sel_lessons)] if sel_lessons else df_sub
                
                remaining = [idx for idx in pool.index if idx not in st.session_state.seen_ids]
                if not remaining:
                    st.session_state.seen_ids = set()
                    remaining = list(pool.index)

                num_q = st.number_input(f"புதிய வினாக்கள் (மீதம்: {len(remaining)}):", 1, len(remaining), min(len(remaining), 10))
                
                if st.button("தேர்வைத் தொடங்கு ➡️", type="primary") and u_name:
                    st.session_state.user_name = u_name
                    st.session_state.selected_std, st.session_state.selected_subject = sel_std, sel_sub
                    current_selection = random.sample(remaining, num_q)
                    st.session_state.filtered_df = pool.loc[current_selection].reset_index(drop=True)
                    for idx in current_selection: st.session_state.seen_ids.add(idx)
                    st.session_state.options_map = {i: random.sample([str(st.session_state.filtered_df.iloc[i][f'Ans-{j}']) for j in range(1,5)], 4) for i in range(len(st.session_state.filtered_df))}
                    st.session_state.user_answers, st.session_state.visited, st.session_state.marked = {}, set(), set()
                    st.session_state.current_q_idx, st.session_state.score_saved = 0, False
                    st.session_state.page = 'quiz'; st.rerun()

    # --- 2. வினாடி வினா பக்கம் ---
    elif st.session_state.page == 'quiz':
        df, q_idx = st.session_state.filtered_df, st.session_state.current_q_idx
        row = df.iloc[q_idx]
        st.session_state.visited.add(q_idx)
        st.markdown('<div class="school-header"><p class="school-name">அரசு மேல்நிலைப்பள்ளி தேவனாங்குறிச்சி</p></div>', unsafe_allow_html=True)
        m_col, n_col = st.columns([7.5, 2.5])
        with m_col:
            st.markdown(f'<div class="q-box"><b>வினா {q_idx + 1} / {len(df)}</b><br><h3>{row["Question Text"]}</h3></div>', unsafe_allow_html=True)
            opts = st.session_state.options_map[q_idx]
            curr_ans = st.session_state.user_answers.get(q_idx)
            ans = st.radio("விடை:", opts, key=f"r_{q_idx}", index=opts.index(curr_ans) if curr_ans in opts else None)
            if ans: st.session_state.user_answers[q_idx] = ans
            st.checkbox("🚩 சந்தேகம்", value=(q_idx in st.session_state.marked), key=f"m_{q_idx}", on_change=lambda: st.session_state.marked.add(q_idx) if st.session_state[f"m_{q_idx}"] else st.session_state.marked.discard(q_idx))
            st.divider()
            b1, b2, b3 = st.columns(3)
            with b1: 
                if q_idx > 0 and st.button("⬅️ முந்தைய"): st.session_state.current_q_idx -= 1; st.rerun()
            with b2:
                if q_idx < len(df)-1 and st.button("அடுத்தது ➡️"): st.session_state.current_q_idx += 1; st.rerun()
            with b3:
                if st.button("🏁 முடி (Submit)", type="primary"): st.session_state.page = 'result'; st.rerun()
        with n_col:
            grid = st.columns(5)
            for i in range(len(df)):
                lbl = "✅" if i in st.session_state.user_answers else ("🚩" if i in st.session_state.marked else f"{i+1}")
                bg = "#28A745" if i in st.session_state
