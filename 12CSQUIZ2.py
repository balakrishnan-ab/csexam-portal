import streamlit as st
import pandas as pd
import random
from datetime import datetime

# 1. பக்க அமைப்பு (Page Layout)
st.set_page_config(page_title="தேர்வு மையம் - GHSS Devanankurichi", layout="wide")

# --- CSS: வண்ணக் குறியீடுகள் மற்றும் வடிவமைப்பு ---
st.markdown("""
    <style>
    .block-container { padding-top: 1.5rem; }
    .header-row { display: flex; justify-content: space-between; align-items: flex-start; width: 100%; margin-bottom: 10px; }
    .school-name { color: #1E88E5; font-size: clamp(1.2rem, 3vw, 2.2rem); font-weight: bold; margin: 0; line-height: 1.2; }
    .exam-info { font-size: 1rem; color: #555; margin: 0; font-weight: bold; }
    
    /* வினா பலக பொத்தான்கள் (வட்ட வடிவம்) */
    div[data-testid="stColumn"] button[key*="nav_btn_"] {
        border-radius: 50% !important;
        width: 45px !important;
        height: 45px !important;
        font-weight: bold !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        padding: 0 !important;
    }

    /* சாதாரண பொத்தான்கள் (செவ்வக வடிவம்) */
    div.stButton > button:not([key*="nav_btn_"]) {
        border-radius: 5px !important;
        padding: 8px 20px !important;
    }
    
    .certificate-border { 
        border: 15px double #1E88E5; 
        padding: 40px; 
        text-align: center; 
        background: #fdfdfd; 
        margin: 20px auto; 
        max-width: 800px; 
    }
    .score-display { font-size: 2.5rem; font-weight: bold; color: #d32f2f; margin: 15px 0; }
    .kural { font-style: italic; font-size: 0.9rem; color: #666; margin-top: 30px; border-top: 1px solid #ddd; padding-top: 10px; }
    </style>
    """, unsafe_allow_html=True)

@st.cache_data(ttl=60)
def get_data(url):
    try:
        data = pd.read_csv(url)
        data.columns = data.columns.str.strip()
        return data.dropna(subset=['Question Text'])
    except:
        return pd.DataFrame()

# உங்கள் கூகிள் ஷீட் CSV லிங்க்
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSQwApSEm-2EfhP7PVMuZVBUcrD0XGr3tMXMTpX2j-9m5gB3xPgECBEsXjqTtBmW7lnFcrIVuOycN7V/pub?output=csv"

# செஷன் ஸ்டேட் (Session State) மேலாண்மை
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
        section_limit = 25

        if st.session_state.shuffled_indices is None:
            indices = list(range(total_qs))
            random.shuffle(indices)
            st.session_state.shuffled_indices = indices

        # --- 1. லாகின் பக்கம் (Login Page) ---
        if st.session_state.page == 'login':
            st.markdown("<h1 style='text-align:center;'>அரசு மேல்நிலைப்பள்ளி தேவனாங்குறிச்சி</h1>", unsafe_allow_html=True)
            st.divider()
            col1, col2, col3 = st.columns([1,2,1])
            with col2:
                name = st.text_input("மாணவர் பெயர்:", key="name_input_field")
                if st.button("தேர்வைத் தொடங்கு ➡️", type="primary", use_container_width=True):
                    if name:
                        st.session_state.user_name = name
                        st.session_state.page = 'quiz'
                        st.rerun()
                    else: st.error("தயவுசெய்து உங்கள் பெயரை உள்ளிடவும்!")

        # --- 2. வினாடி வினா பக்கம் (Quiz Page) ---
        elif st.session_state.page == 'quiz':
            q_ptr = st.session_state.current_q_idx
            idx = st.session_state.shuffled_indices[q_ptr]
            row = df.iloc[idx]
            
            # வினாவைப் பார்த்ததாகப் பதிவு (நீல நிறத்திற்காக)
            st.session_state.visited.add(idx)
            
            col_main, col_nav = st.columns([7, 3])
            
            with col_main:
                # பள்ளி மற்றும் வினா விவரங்கள் (தலைப்பு)
                st.markdown(f"""
                <div class="header-row">
                    <div>
                        <p class="school-name">அரசு மேல்நிலைப்பள்ளி தேவனாங்குறிச்சி</p>
                        <p class="exam-info">பாடம்: {row.get('Subject Code', 'கணினி அறிவியல்')} | அலகு: {row.get('Lesson Code', '-')}</p>
                    </div>
                    <div style="background:#f0f2f6; padding:10px; border-radius:8px; border:1px solid #1E88E5; text-align:center;">
                        <b>வினா {q_ptr + 1} / {total_qs}</b>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                st.caption(f"மாணவர்: {st.session_state.user_name}")
                st.divider()
                
                # வினா மற்றும் விடைகள்
                st.write(f"### {row['Question Text']}")
                
                opts = [str(row['Ans-1']), str(row['Ans-2']), str(row['Ans-3']), str(row['Ans-4'])]
                if f"opts_{idx}" not in st.session_state:
                    random.shuffle(opts)
                    st.session_state[f"opts_{idx}"] = opts
                
                ans = st.radio("சரியான விடையைத் தேர்ந்தெடுக்கவும்:", st.session_state[f"opts_{idx}"], key=f"r_{idx}", 
                               index=st.session_state[f"opts_{idx}"].index(st.session_state.user_answers[idx]) if idx in st.session_state.user_answers else None)
                
                if ans: st.session_state.user_answers[idx] = ans

                # சந்தேகம் (Mark for Review)
                is_m = st.checkbox("🤔 இந்த வினாவில் சந்தேகம் உள்ளது (Mark for Review)", value=(idx in st.session_state.marked), key=f"check_{idx}")
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
                    if (q_ptr + 1) % section_limit == 0 or (q_ptr + 1) == total_qs:
                        if st.button("மதிப்பீடு செய் 🚩", type="primary", use_container_width=True):
                            st.session_state.page = 'choice'; st.rerun()

            with col_nav:
                st.markdown("<h5 style='text-align:center;'>🔢 வினா பலகம்</h5>", unsafe_allow_html=True)
                grid = st.columns(5)
                start_s = (q_ptr // section_limit) * section_limit
                end_s = min(start_s + section_limit, total_qs)
                
                for i in range(start_s, end_s):
                    ix = st.session_state.shuffled_indices[i]
                    with grid[(i - start_s) % 5]:
                        # வண்ணத் தர்க்கம்
                        if ix in st.session_state.marked: bg, txt, brd = "#FF9800", "white", "#EF6C00" # ஆரஞ்சு
                        elif ix in st.session_state.user_answers: bg, txt, brd = "#28a745", "white", "#1e7e34" # பச்சை
                        elif ix in st.session_state.visited: bg, txt, brd = "#2196F3", "white", "#1976D2" # நீலம்
                        else: bg, txt, brd = "#f0f2f6", "black", "#ccc" # சாம்பல்
                        
                        # தற்போதைய வினா பார்டர்
                        curr_brd = "4px solid black" if i == q_ptr else f"2px solid {brd}"

                        st.markdown(f"""
                            <style>
                            button[key='nav_btn_{i}'] {{
                                background-color: {bg} !important;
                                color: {txt} !important;
                                border: {curr_brd} !important;
                            }}
                            </style>
                        """, unsafe_allow_html=True)
                        if st.button(f"{i+1}", key=f"nav_btn_{i}"):
                            st.session_state.current_q_idx = i; st.rerun()
                
                st.markdown("<div style='font-size:0.8rem; margin-top:10px;'>🟢 விடை அளித்தது | 🔵 பார்த்தது | 🟠 சந்தேகம் | ⚪ பார்க்காதது</div>", unsafe_allow_html=True)

        # --- 3. மற்ற பக்கங்கள் (மதிப்பீடு/சான்றிதழ்) ---
        elif st.session_state.page == 'choice':
            st.subheader("📍 இந்தப் பகுதி நிறைவுற்றது")
            if st.button("மதிப்பீடு செய் ✅", type="primary", use_container_width=True): st.session_state.page = 'evaluate'; st.rerun()
            if (st.session_state.current_q_idx + 1) < total_qs:
                if st.button("அடுத்த பகுதிக்குச் செல் ➡️", use_container_width=True):
                    st.session_state.current_q_idx += 1; st.session_state.page = 'quiz'; st.rerun()

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
                fdb = "வாழ்த்துக்கள்! மிகவும் நன்று 🌟" if percent>=90 else ("வாழ்த்துக்கள்! நன்று 👍" if percent>=70 else ("வாழ்த்துக்கள்! திருப்தி 🙂" if percent>=50 else "மீண்டும் முயற்சி செய்க 📚"))
                
                st.markdown(f"""
                <div class="certificate-border">
                    <div class="cert-title">அரசு மேல்நிலைப்பள்ளி - தேவனாங்குறிச்சி</div>
                    <div class="cert-sub">நாமக்கல் மாவட்டம்</div><hr>
                    <div class="cert-body">
                        <b>{st.session_state.user_name}</b> அவர்கள் இப்பள்ளியின் <b>கணினி அறிவியல் பாடத்தில் <br> 
                        ஒருமதிப்பெண் தேர்வு எழுதி</b> <b>{now}</b> அன்று <br>
                        <div class="score-display">{score} / {total_qs}</div>
                        மதிப்பெண்கள் பெற்றுள்ளார். <br><br><b>{fdb}</b>
                    </div>
                    <div class="kural">
                        "வெள்ளத் தனைய மலர்நீட்டம் மாந்தர்தம்<br>உள்ளத் தனையது உயர்வு"
                    </div>
                </div>
                """, unsafe_allow_html=True)
                if st.button("🔄 மீண்டும் தேர்வு எழுத"): st.session_state.clear(); st.rerun()
            elif st.button("அடுத்த பகுதிக்குத் தொடரவும் ➡️", type="primary"):
                st.session_state.current_q_idx += 1; st.session_state.page = 'quiz'; st.rerun()

except Exception as e:
    st.error(f"ஒரு எதிர்பாராத பிழை ஏற்பட்டது: {e}")
