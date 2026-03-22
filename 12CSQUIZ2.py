import streamlit as st
import pandas as pd
import random
from datetime import datetime

# 1. பக்க அமைப்பு
st.set_page_config(page_title="தேர்வு மையம் - GHSS Devanankurichi", layout="wide")

# --- CSS: பள்ளி பெயர் மற்றும் வண்ணக் கட்டங்கள் ---
st.markdown("""
    <style>
    .block-container { padding-top: 1.5rem; }
    
    /* பள்ளி விவரங்கள் */
    .school-header {
        background-color: #f0f8ff;
        padding: 15px;
        border-radius: 10px;
        border-left: 8px solid #1E88E5;
        margin-bottom: 20px;
    }
    .school-name { color: #1E88E5; font-size: 2rem; font-weight: bold; margin: 0; }
    .exam-detail { font-size: 1.1rem; color: #444; font-weight: bold; }

    /* வினா பலக பொத்தான்கள் மற்றும் வண்ணப் புள்ளிகள் */
    .nav-container {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        margin-bottom: 10px;
    }
    .status-dot {
        width: 12px;
        height: 12px;
        border-radius: 50%;
        margin-bottom: 4px;
        border: 1px solid #ddd;
    }
    
    /* வண்ணங்கள் */
    .dot-grey { background-color: #eee; }
    .dot-blue { background-color: #2196F3; } /* பார்த்தது */
    .dot-green { background-color: #28a745; } /* விடை அளித்தது */
    .dot-orange { background-color: #FF9800; } /* சந்தேகம் */

    div[data-testid="stColumn"] button {
        width: 45px !important;
        height: 35px !important;
        padding: 0 !important;
        font-weight: bold !important;
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

        # --- லாகின் ---
        if st.session_state.page == 'login':
            st.markdown("<h1 style='text-align:center;'>அரசு மேல்நிலைப்பள்ளி தேவனாங்குறிச்சி</h1>", unsafe_allow_html=True)
            col1, col2, col3 = st.columns([1,2,1])
            with col2:
                name = st.text_input("மாணவர் பெயர்:", key="login_name")
                if st.button("தேர்வைத் தொடங்கு ➡️", type="primary"):
                    if name:
                        st.session_state.user_name = name
                        st.session_state.page = 'quiz'
                        st.rerun()

        # --- வினாடி வினா ---
        elif st.session_state.page == 'quiz':
            q_ptr = st.session_state.current_q_idx
            idx = st.session_state.shuffled_indices[q_ptr]
            row = df.iloc[idx]
            st.session_state.visited.add(idx)
            
            # பள்ளி பெயர் - எச்.டி.எம்.எல் (HTML) மூலம் நேரடியாக
            st.markdown(f"""
            <div class="school-header">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <p class="school-name">அரசு மேல்நிலைப்பள்ளி தேவனாங்குறிச்சி</p>
                        <p class="exam-detail">பாடம்: {row.get('Subject Code', 'CS')} | அலகு: {row.get('Lesson Code', 'L-1')}</p>
                    </div>
                    <div style="background:#fff; padding:10px; border:2px solid #1E88E5; border-radius:8px; font-weight:bold;">
                        வினா {q_ptr + 1} / {total_qs}
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            col_main, col_nav = st.columns([7, 3])
            
            with col_main:
                st.write(f"### {row['Question Text']}")
                opts = [str(row['Ans-1']), str(row['Ans-2']), str(row['Ans-3']), str(row['Ans-4'])]
                if f"opts_{idx}" not in st.session_state:
                    random.shuffle(opts)
                    st.session_state[f"opts_{idx}"] = opts
                
                ans = st.radio("சரியான விடையைத் தேர்ந்தெடுக்கவும்:", st.session_state[f"opts_{idx}"], key=f"r_{idx}", 
                               index=st.session_state[f"opts_{idx}"].index(st.session_state.user_answers[idx]) if idx in st.session_state.user_answers else None)
                if ans: st.session_state.user_answers[idx] = ans

                is_m = st.checkbox("🤔 இந்த வினாவில் சந்தேகம் உள்ளது (Mark for Review)", value=(idx in st.session_state.marked), key=f"m_{idx}")
                if is_m: st.session_state.marked.add(idx)
                else: st.session_state.marked.discard(idx)

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
                        # வண்ணத் தர்க்கம் (புள்ளி வடிவில்)
                        dot_class = "dot-grey"
                        if ix in st.session_state.marked: dot_class = "dot-orange"
                        elif ix in st.session_state.user_answers: dot_class = "dot-green"
                        elif ix in st.session_state.visited: dot_class = "dot-blue"
                        
                        st.markdown(f'<div class="nav-container"><div class="status-dot {dot_class}"></div></div>', unsafe_allow_html=True)
                        if st.button(f"{i+1}", key=f"nav_btn_{i}", type="primary" if i==q_ptr else "secondary"):
                            st.session_state.current_q_idx = i; st.rerun()
                
                st.markdown("<div style='font-size:0.8rem; margin-top:10px;'>🟢 விடை அளித்தது | 🔵 பார்த்தது | 🟠 சந்தேகம் | ⚪ பார்க்காதது</div>", unsafe_allow_html=True)

        # --- சான்றிதழ் (முந்தைய அதே நேர்த்தியான வடிவம்) ---
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
                    <div style="color:#1E88E5; font-size:2rem; font-weight:bold;">அரசு மேல்நிலைப்பள்ளி - தேவனாங்குறிச்சி</div>
                    <div style="font-size:1.1rem; color:#555;">நாமக்கல் மாவட்டம்</div><hr>
                    <div style="font-size:1.3rem; line-height:1.8;">
                        <b>{st.session_state.user_name}</b> அவர்கள் இப்பள்ளியின் <b>கணினி அறிவியல் பாடத்தில் <br> 
                        ஒருமதிப்பெண் தேர்வு எழுதி</b> <b>{now}</b> அன்று <br>
                        <div style="font-size:2.5rem; font-weight:bold; color:#d32f2f;">{score} / {total_qs}</div>
                        மதிப்பெண்கள் பெற்றுள்ளார். <br><br><b>{fdb}</b>
                    </div>
                    <div style="font-style:italic; font-size:0.9rem; color:#666; margin-top:30px; border-top:1px solid #ddd; padding-top:10px;">
                        "வெள்ளத் தனைய மலர்நீட்டம் மாந்தர்தம்<br>உள்ளத் தனையது உயர்வு"
                    </div>
                </div>
                """, unsafe_allow_html=True)
                if st.button("🔄 மீண்டும் தேர்வு எழுத"): st.session_state.clear(); st.rerun()
            elif st.button("அடுத்த பகுதிக்குத் தொடரவும் ➡️"):
                st.session_state.current_q_idx += 1; st.session_state.page = 'quiz'; st.rerun()

        elif st.session_state.page == 'choice':
            if st.button("மதிப்பீடு செய் ✅", type="primary", use_container_width=True): st.session_state.page = 'evaluate'; st.rerun()
            if (st.session_state.current_q_idx + 1) < total_qs:
                if st.button("அடுத்த பகுதிக்குச் செல் ➡️", use_container_width=True):
                    st.session_state.current_q_idx += 1; st.session_state.page = 'quiz'; st.rerun()

except Exception as e: st.error(f"பிழை: {e}")
