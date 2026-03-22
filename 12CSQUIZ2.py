import streamlit as st
import pandas as pd
import random
from datetime import datetime

# 1. பக்க அமைப்பு
st.set_page_config(page_title="தேர்வு மையம்", layout="wide")

# --- CSS: சான்றிதழ் வடிவமைப்பு ---
st.markdown("""
    <style>
    .block-container { padding-top: 1.5rem; }
    .certificate-border {
        border: 15px double #1E88E5;
        padding: 40px;
        text-align: center;
        background-color: #fdfdfd;
        color: #333;
        font-family: 'Arial', sans-serif;
        margin: 20px auto;
        max-width: 800px;
    }
    .cert-title { color: #1E88E5; font-size: 2.2rem; font-weight: bold; margin-bottom: 5px; }
    .cert-sub { font-size: 1.2rem; margin-bottom: 20px; color: #555; }
    .cert-body { font-size: 1.3rem; line-height: 1.8; margin-bottom: 25px; }
    .score-display { font-size: 2.5rem; font-weight: bold; color: #d32f2f; margin: 10px 0; }
    .kural { font-style: italic; font-size: 0.9rem; color: #666; margin-top: 30px; border-top: 1px solid #ddd; padding-top: 10px; }
    
    /* வினா பலக வண்ணங்கள் */
    [data-testid="stHorizontalBlock"] button[key*="nav_btn_"] {
        border-radius: 50% !important;
        width: 45px !important; height: 45px !important;
        display: flex !important; align-items: center !important; justify-content: center !important;
        font-weight: bold !important; padding: 0 !important; margin: 5px auto !important;
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
if 'visited_questions' not in st.session_state: st.session_state.visited_questions = set()
if 'marked_review' not in st.session_state: st.session_state.marked_review = set()
if 'shuffled_indices' not in st.session_state: st.session_state.shuffled_indices = None
if 'current_q_idx' not in st.session_state: st.session_state.current_q_idx = 0

try:
    df = get_data(SHEET_URL)
    if not df.empty:
        total_qs = len(df)
        section_limit = 25

        if st.session_state.shuffled_indices is None:
            indices = list(range(total_qs))
            random.shuffle(indices)
            st.session_state.shuffled_indices = indices

        # --- 1. லாகின் ---
        if st.session_state.page == 'login':
            st.markdown("<h1 style='text-align:center;'>அரசு மேல்நிலைப்பள்ளி தேவனாங்குறிச்சி</h1>", unsafe_allow_html=True)
            col1, col2, col3 = st.columns([1,2,1])
            with col2:
                name = st.text_input("மாணவர் பெயர்:", key="name_in")
                if st.button("தேர்வைத் தொடங்கு ➡️", type="primary", key="start_btn"):
                    if name:
                        st.session_state.user_name = name
                        st.session_state.page = 'quiz'
                        st.rerun()

        # --- 2. வினாடி வினா பக்கம் ---
        elif st.session_state.page == 'quiz':
            q_ptr = st.session_state.current_q_idx
            actual_idx = st.session_state.shuffled_indices[q_ptr]
            row = df.iloc[actual_idx]
            st.session_state.visited_questions.add(actual_idx)
            
            col_main, col_nav = st.columns([7, 3])
            with col_main:
                st.markdown(f"### {row['Question Text']}")
                opts = [str(row['Ans-1']), str(row['Ans-2']), str(row['Ans-3']), str(row['Ans-4'])]
                if f"opts_{actual_idx}" not in st.session_state:
                    random.shuffle(opts)
                    st.session_state[f"opts_{actual_idx}"] = opts
                
                ans = st.radio("விடைகள்:", st.session_state[f"opts_{actual_idx}"], key=f"r_{actual_idx}", 
                               index=st.session_state[f"opts_{actual_idx}"].index(st.session_state.user_answers[actual_idx]) if actual_idx in st.session_state.user_answers else None)
                if ans: st.session_state.user_answers[actual_idx] = ans

                is_marked = st.checkbox("🤔 சந்தேகம் (Mark for Review)", value=(actual_idx in st.session_state.marked_review), key=f"check_{actual_idx}")
                if is_marked: st.session_state.marked_review.add(actual_idx)
                else: st.session_state.marked_review.discard(actual_idx)

                st.divider()
                n1, n2, n3 = st.columns([1, 1, 1])
                with n1:
                    if q_ptr > 0 and st.button("⬅️ முந்தைய", key="p_btn"):
                        st.session_state.current_q_idx -= 1; st.rerun()
                with n2:
                    if q_ptr < total_qs - 1 and st.button("அடுத்தது ➡️", key="n_btn"):
                        st.session_state.current_q_idx += 1; st.rerun()
                with n3:
                    if (q_ptr + 1) % section_limit == 0 or (q_ptr + 1) == total_qs:
                        if st.button("மதிப்பீடு செய் 🚩", type="primary", key="e_btn"):
                            st.session_state.page = 'choice'; st.rerun()

            with col_nav:
                st.markdown("<h5 style='text-align:center;'>🔢 வினா பலகம்</h5>", unsafe_allow_html=True)
                grid = st.columns(5)
                start_sec = (q_ptr // section_limit) * section_limit
                end_sec = min(start_sec + section_limit, total_qs)
                for i in range(start_sec, end_sec):
                    idx = st.session_state.shuffled_indices[i]
                    with grid[(i - start_sec) % 5]:
                        if idx in st.session_state.marked_review: bg, txt, brd = "#FF9800", "white", "#EF6C00"
                        elif idx in st.session_state.user_answers: bg, txt, brd = "#28a745", "white", "#1e7e34"
                        elif idx in st.session_state.visited_questions: bg, txt, brd = "#2196F3", "white", "#1976D2"
                        else: bg, txt, brd = "#f0f2f6", "black", "#ccc"
                        
                        st.markdown(f"<style>button[key='nav_btn_{i}'] {{ background-color: {bg} !important; color: {txt} !important; border: {'3px solid black' if i==q_ptr else '2px solid '+brd} !important; }}</style>", unsafe_allow_html=True)
                        if st.button(f"{i+1}", key=f"nav_btn_{i}"):
                            st.session_state.current_q_idx = i; st.rerun()

        # --- 3. மதிப்பீடு & சான்றிதழ் ---
        elif st.session_state.page == 'choice':
            if st.button("மதிப்பீடு செய் ✅", type="primary"): st.session_state.page = 'evaluate'; st.rerun()
            if (st.session_state.current_q_idx + 1) < total_qs:
                if st.button("அடுத்த பகுதிக்குச் செல் ➡️"):
                    st.session_state.current_q_idx += 1; st.session_state.page = 'quiz'; st.rerun()

        elif st.session_state.page == 'evaluate':
            score = 0
            limit = st.session_state.current_q_idx + 1
            for i in range(limit):
                idx = st.session_state.shuffled_indices[i]
                if str(st.session_state.user_answers.get(idx)) == str(df.iloc[idx]['Answer']): score += 1
            
            if limit >= total_qs:
                # சான்றிதழ் விவரங்கள்
                st.balloons()
                now = datetime.now().strftime("%d-%m-%Y %I:%M %p")
                percent = (score / total_qs) * 100
                if percent >= 90: feedback = "வாழ்த்துக்கள்! மிகவும் நன்று 🌟"
                elif percent >= 70: feedback = "வாழ்த்துக்கள்! நன்று 👍"
                elif percent >= 50: feedback = "வாழ்த்துக்கள்! திருப்தி 🙂"
                else: feedback = "மீண்டும் முயற்சி செய்க 📚"

                st.markdown(f"""
                <div class="certificate-border">
                    <div class="cert-title">அரசு மேல்நிலைப்பள்ளி - தேவனாங்குறிச்சி</div>
                    <div class="cert-sub">நாமக்கல் மாவட்டம்</div>
                    <hr>
                    <div class="cert-body">
                        <b>{st.session_state.user_name}</b> அவர்கள் இப்பள்ளியின் கணினி அறிவியல் <br>
                        ஒருமதிப்பெண் தேர்வுத் தளத்தில் <b>{now}</b> அன்று தேர்வு எழுதி <br>
                        <div class="score-display">{score} / {total_qs}</div>
                        மதிப்பெண்கள் பெற்றுள்ளார். <br><br>
                        <b>{feedback}</b>
                    </div>
                    <div class="kural">
                        "வெள்ளத் தனைய மலர்நீட்டம் மாந்தர்தம்<br>உள்ளத் தனையது உயர்வு"
                    </div>
                </div>
                """, unsafe_allow_html=True)
                if st.button("🔄 மீண்டும் தேர்வு எழுத"): st.session_state.clear(); st.rerun()
            elif st.button("அடுத்த பகுதிக்குத் தொடரவும் ➡️"):
                st.session_state.current_q_idx += 1; st.session_state.page = 'quiz'; st.rerun()

except Exception as e: st.error(f"பிழை: {e}")
