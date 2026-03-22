import streamlit as st
import pandas as pd
import random
from datetime import datetime

# 1. பக்க அமைப்பு
st.set_page_config(page_title="Exam Portal - GHSS Devanankurichi", layout="wide")

# --- CSS: உயர்தர வடிவமைப்பு ---
st.markdown("""
    <style>
    .block-container { padding-top: 2rem !important; }
    .school-header { text-align: center; background-color: #f0f7ff; padding: 25px; border-radius: 15px; border: 2px solid #1E88E5; margin-bottom: 20px; }
    .school-name { color: #0D47A1; font-size: 3rem !important; font-weight: bold; margin: 0; }
    .q-counter-box { display: inline-block; background-color: #1E88E5; color: white; padding: 5px 15px; border-radius: 8px; font-size: 1.2rem; margin-left: 20px; vertical-align: middle; }
    div.stButton > button { width: 100% !important; height: 50px !important; font-weight: bold !important; font-size: 1.1rem !important; border-radius: 10px !important; }
    .result-card { padding: 15px; border-radius: 10px; margin-bottom: 10px; border-left: 10px solid; background-color: #f9f9f9; }
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

# செஷன் ஸ்டேட் மேலாண்மை
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
            st.markdown("<h1 style='text-align:center; color:#1E88E5;'>அரசு மேல்நிலைப்பள்ளி தேவனாங்குறிச்சி</h1>", unsafe_allow_html=True)
            col1, col2, col3 = st.columns([1,2,1])
            with col2:
                name = st.text_input("மாணவர் பெயர்:", key="main_name")
                if st.button("தேர்வைத் தொடங்கு ➡️", type="primary"):
                    if name: st.session_state.user_name = name; st.session_state.page = 'quiz'; st.rerun()

        # --- வினாடி வினா பக்கம் ---
        elif st.session_state.page == 'quiz':
            q_ptr = st.session_state.current_q_idx
            idx = st.session_state.shuffled_indices[q_ptr]
            row = df.iloc[idx]
            st.session_state.visited.add(idx)
            
            st.markdown(f"""
            <div class="school-header">
                <span class="school-name">அரசு மேல்நிலைப்பள்ளி தேவனாங்குறிச்சி</span>
                <span class="q-counter-box">வினா {q_ptr + 1} / {total_qs}</span>
                <p style="margin-top:10px; font-weight:bold;">பாடம்: {row.get('Subject Code', 'கணினி அறிவியல்')} | அலகு: {row.get('Lesson Code', 'L-1')}</p>
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
                        st.markdown(f'<div style="text-align:center;"><div style="width:12px; height:12px; border-radius:50%; background-color:{dot}; margin:auto;"></div></div>', unsafe_allow_html=True)
                        if st.button(f"{i+1}", key=f"nav_btn_{i}", type="primary" if i==q_ptr else "secondary"):
                            st.session_state.current_q_idx = i; st.rerun()

        # --- இடைநிலைப் பக்கம் (Choice) ---
        elif st.session_state.page == 'choice':
            st.markdown("<div style='text-align:center; padding:50px;'><h2>🎯 பகுதி நிறைவுற்றது</h2>", unsafe_allow_html=True)
            if st.button("மதிப்பீடு செய் (Result) ✅", type="primary"): 
                st.session_state.page = 'evaluate_view'; st.rerun()
            if (st.session_state.current_q_idx + 1) < total_qs:
                if st.button("அடுத்த பகுதிக்குச் செல் ➡️"):
                    st.session_state.current_q_idx += 1; st.session_state.page = 'quiz'; st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

        # --- மதிப்பீடு பக்கம் (Evaluation View) ---
        elif st.session_state.page == 'evaluate_view':
            st.header(f"📊 தேர்வு மதிப்பீடு: {st.session_state.user_name}")
            score = 0
            limit = st.session_state.current_q_idx + 1
            for i in range(limit):
                idx = st.session_state.shuffled_indices[i]
                u_ans = st.session_state.user_answers.get(idx, "பதிலளிக்கவில்லை")
                correct = str(df.iloc[idx]['Answer'])
                is_ok = (str(u_ans) == correct)
                if is_ok: score += 1
                
                clr = "#28a745" if is_ok else "#dc3545"
                st.markdown(f"""
                <div class="result-card" style="border-left-color:{clr};">
                    <b>வினா {i+1}:</b> {df.iloc[idx]['Question Text']}<br>
                    உங்கள் விடை: {u_ans} | சரியான விடை: <b>{correct}</b>
                </div>
                """, unsafe_allow_html=True)

            st.divider()
            st.subheader(f"தற்போதைய மதிப்பெண்: {score} / {limit}")
            if limit >= total_qs:
                if st.button("சான்றிதழ் பெற 📜", type="primary"): st.session_state.page = 'certificate'; st.rerun()
            else:
                if st.button("அடுத்த பகுதிக்குத் தொடரவும் ➡️", type="primary"):
                    st.session_state.current_q_idx += 1; st.session_state.page = 'quiz'; st.rerun()

        # --- சான்றிதழ் பக்கம் ---
        elif st.session_state.page == 'certificate':
            score = 0
            for idx in st.session_state.user_answers:
                if str(st.session_state.user_answers[idx]) == str(df.iloc[idx]['Answer']): score += 1
            
            st.balloons()
            now = datetime.now().strftime("%d-%m-%Y %I:%M %p")
            st.markdown(f"""
            <div style="border:15px double #1E88E5; padding:40px; text-align:center; background:white;">
                <h1 style="color:#1E88E5;">அரசு மேல்நிலைப்பள்ளி - தேவனாங்குறிச்சி</h1>
                <p>நாமக்கல் மாவட்டம்</p><hr>
                <p style="font-size:1.4rem;">மாணவர் <b>{st.session_state.user_name}</b> அவர்கள் இப்பள்ளியின் <b>கணினி அறிவியல் பாடத்தில்</b></p>
                <p style="font-size:1.4rem;">ஒருமதிப்பெண் தேர்வு எழுதி <b>{now}</b> அன்று</p>
                <h1 style="color:#d32f2f; font-size:4rem;">{score} / {total_qs}</h1>
                <p style="font-size:1.2rem;">மதிப்பெண்கள் பெற்றுள்ளார்.</p>
                <p><i>"வெள்ளத் தனைய மலர்நீட்டம் மாந்தர்தம் உள்ளத் தனையது உயர்வு"</i></p>
            </div>
            """, unsafe_allow_html=True)
            if st.button("🔄 மீண்டும் தேர்வு எழுத"): st.session_state.clear(); st.rerun()

except Exception as e: st.error(f"பிழை: {e}")
