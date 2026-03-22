import streamlit as st
import pandas as pd
import random
from datetime import datetime

# 1. பக்க அமைப்பு
st.set_page_config(page_title="GHSS Devanankurichi Exam Portal", layout="wide")

# --- CSS: மேம்படுத்தப்பட்ட வடிவமைப்பு ---
st.markdown("""
    <style>
    .block-container { padding-top: 1rem; }
    
    /* பள்ளி விவரங்கள் - இன்னும் பெரியதாக */
    .school-header {
        background-color: #e3f2fd;
        padding: 20px;
        border-radius: 12px;
        border-bottom: 5px solid #1E88E5;
        margin-bottom: 25px;
        text-align: center;
    }
    .school-name { color: #0D47A1; font-size: 2.5rem; font-weight: bold; margin: 0; padding-bottom: 5px; }
    .exam-detail { font-size: 1.3rem; color: #333; font-weight: bold; }

    /* வினா பலக வண்ணப் புள்ளிகள் */
    .nav-container { display: flex; flex-direction: column; align-items: center; margin-bottom: 5px; }
    .status-dot { width: 14px; height: 14px; border-radius: 50%; margin-bottom: 2px; border: 1px solid #bbb; }
    .dot-grey { background-color: #eee; }
    .dot-blue { background-color: #2196F3; } 
    .dot-green { background-color: #28a745; } 
    .dot-orange { background-color: #FF9800; }

    /* பெரிய பொத்தான்கள் (அடுத்து, முந்தைய) */
    div.stButton > button:not([key*="nav_btn_"]) {
        border-radius: 8px !important;
        padding: 12px 40px !important; /* நீளம் மற்றும் அகலம் அதிகரிப்பு */
        font-size: 1.1rem !important;
        font-weight: bold !important;
        width: 100% !important;
        height: 55px !important;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }

    /* வினா பலக பொத்தான்கள் */
    div[data-testid="stColumn"] button[key*="nav_btn_"] {
        width: 50px !important;
        height: 40px !important;
        font-size: 1rem !important;
    }

    .certificate-border { border: 15px double #1E88E5; padding: 40px; text-align: center; background: #fff; margin: 20px auto; max-width: 800px; }
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

# செஷன் ஸ்டேட்
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
        section_size = 25

        if st.session_state.shuffled_indices is None:
            indices = list(range(total_qs))
            random.shuffle(indices)
            st.session_state.shuffled_indices = indices

        # --- 1. லாகின் ---
        if st.session_state.page == 'login':
            st.markdown("<h1 style='text-align:center; color:#1E88E5;'>அரசு மேல்நிலைப்பள்ளி தேவனாங்குறிச்சி</h1>", unsafe_allow_html=True)
            st.divider()
            col1, col2, col3 = st.columns([1,2,1])
            with col2:
                name = st.text_input("மாணவர் பெயர்:", key="main_login")
                if st.button("தேர்வைத் தொடங்கு ➡️", type="primary"):
                    if name:
                        st.session_state.user_name = name
                        st.session_state.page = 'quiz'
                        st.rerun()

        # --- 2. வினாடி வினா ---
        elif st.session_state.page == 'quiz':
            q_ptr = st.session_state.current_q_idx
            idx = st.session_state.shuffled_indices[q_ptr]
            row = df.iloc[idx]
            st.session_state.visited.add(idx)
            
            # பெரிய பள்ளி விவரங்கள்
            st.markdown(f"""
            <div class="school-header">
                <p class="school-name">அரசு மேல்நிலைப்பள்ளி தேவனாங்குறிச்சி</p>
                <p class="exam-detail">பாடம்: {row.get('Subject Code', 'கணினி அறிவியல்')} | அலகு: {row.get('Lesson Code', 'L-1')}</p>
                <div style="margin-top:10px; font-size:1.2rem; color:#0D47A1;">வினா {q_ptr + 1} / {total_qs}</div>
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
                
                ans = st.radio("சரியான விடையைத் தேர்ந்தெடுக்கவும்:", st.session_state[f"opts_{idx}"], key=f"r_{idx}", 
                               index=st.session_state[f"opts_{idx}"].index(st.session_state.user_answers[idx]) if idx in st.session_state.user_answers else None)
                if ans: st.session_state.user_answers[idx] = ans

                st.checkbox("🤔 இந்த வினாவில் சந்தேகம் உள்ளது (Mark for Review)", value=(idx in st.session_state.marked), key=f"m_{idx}", on_change=lambda: st.session_state.marked.add(idx) if st.session_state[f"m_{idx}"] else st.session_state.marked.discard(idx))

                st.divider()
                n1, n2, n3 = st.columns([1, 1, 1])
                with n1:
                    if q_ptr > 0 and st.button("⬅️ முந்தைய", use_container_width=True):
                        st.session_state.current_q_idx -= 1; st.rerun()
                with n2:
                    if q_ptr < total_qs - 1 and st.button("அடுத்தது ➡️", use_container_width=True):
                        st.session_state.current_q_idx += 1; st.rerun()
                with n3:
                    if (q_ptr + 1) % section_size == 0 or (q_ptr + 1) == total_qs:
                        if st.button("மதிப்பீடு செய் 🚩", type="primary", use_container_width=True):
                            st.session_state.page = 'choice'; st.rerun()

            with col_nav:
                st.markdown("<h5 style='text-align:center;'>🔢 வினா பலகம்</h5>", unsafe_allow_html=True)
                grid = st.columns(5)
                start_s = (q_ptr // section_size) * section_size
                end_s = min(start_s + section_size, total_qs)
                
                for i in range(start_s, end_s):
                    ix = st.session_state.shuffled_indices[i]
                    with grid[(i - start_s) % 5]:
                        dot = "dot-grey"
                        if ix in st.session_state.marked: dot = "dot-orange"
                        elif ix in st.session_state.user_answers: dot = "dot-green"
                        elif ix in st.session_state.visited: dot = "dot-blue"
                        
                        st.markdown(f'<div class="nav-container"><div class="status-dot {dot}"></div></div>', unsafe_allow_html=True)
                        if st.button(f"{i+1}", key=f"nav_btn_{i}", type="primary" if i==q_ptr else "secondary"):
                            st.session_state.current_q_idx = i; st.rerun()
                st.markdown("<div style='font-size:0.8rem; margin-top:10px; text-align:center;'>🟢 விடை | 🔵 பார்த்தது | 🟠 சந்தேகம் | ⚪ ஆரம்பம்</div>", unsafe_allow_html=True)

        # --- 3. மதிப்பீடு / தேர்வு ---
        elif st.session_state.page == 'choice':
            st.markdown("<div style='text-align:center; padding:50px;'>", unsafe_allow_html=True)
            st.header("🎯 பகுதி நிறைவுற்றது")
            st.write("இந்த வினாக்களை மதிப்பீடு செய்யலாமா? அல்லது அடுத்த பகுதிக்குத் தொடரலாமா?")
            if st.button("மதிப்பீடு செய் (Result) ✅", type="primary"): 
                st.session_state.page = 'evaluate'; st.rerun()
            if (st.session_state.current_q_idx + 1) < total_qs:
                if st.button("அடுத்த பகுதிக்குச் செல் ➡️"):
                    st.session_state.current_q_idx += 1; st.session_state.page = 'quiz'; st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

        elif st.session_state.page == 'evaluate':
            score = 0
            limit = st.session_state.current_q_idx + 1
            for i in range(limit):
                idx = st.session_state.shuffled_indices[i]
                if str(st.session_state.user_answers.get(idx)) == str(df.iloc[idx]['Answer']): score += 1
            
            if limit >= total_qs:
                st.balloons()
                now = datetime.now().strftime("%d-%m-%Y %I:%M %p")
                percent = (score/total_qs)*100
                fdb = "மிகவும் நன்று 🌟" if percent>=90 else ("நன்று 👍" if percent>=70 else ("திருப்தி 🙂" if percent>=50 else "மீண்டும் முயற்சி செய்க 📚"))
                st.markdown(f"""
                <div class="certificate-border">
                    <div style="color:#1E88E5; font-size:2.2rem; font-weight:bold;">அரசு மேல்நிலைப்பள்ளி - தேவனாங்குறிச்சி</div>
                    <div style="font-size:1.1rem; color:#555;">நாமக்கல் மாவட்டம்</div><hr>
                    <div style="font-size:1.3rem; line-height:1.8;">
                        <b>{st.session_state.user_name}</b> அவர்கள் இப்பள்ளியின் <b>கணினி அறிவியல் பாடத்தில் <br> 
                        ஒருமதிப்பெண் தேர்வு எழுதி</b> <b>{now}</b> அன்று <br>
                        <div style="font-size:3rem; font-weight:bold; color:#d32f2f;">{score} / {total_qs}</div>
                        மதிப்பெண்கள் பெற்றுள்ளார். <br><br><b>{fdb}</b>
                    </div>
                    <div style="font-style:italic; font-size:1rem; color:#666; margin-top:30px; border-top:1px solid #ddd; padding-top:10px;">
                        "வெள்ளத் தனைய மலர்நீட்டம் மாந்தர்தம்<br>உள்ளத் தனையது உயர்வு"
                    </div>
                </div>
                """, unsafe_allow_html=True)
                if st.button("🔄 மீண்டும் தேர்வு எழுத"): st.session_state.clear(); st.rerun()
            else:
                st.subheader(f"இந்த வரையிலான மதிப்பெண்: {score} / {limit}")
                if st.button("அடுத்த பகுதிக்குத் தொடரவும் ➡️", type="primary"):
                    st.session_state.current_q_idx += 1; st.session_state.page = 'quiz'; st.rerun()

except Exception as e: st.error(f"பிழை: {e}")
