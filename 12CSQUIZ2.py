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
    [data-testid="stHorizontalBlock"] button[key*="nav_btn_"] {
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
    div.stButton > button:not([key*="nav_btn_"]) {
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
    try:
        data = pd.read_csv(url)
        data.columns = data.columns.str.strip()
        # காலி வரிசைகளை நீக்க
        data = data.dropna(subset=['Question Text'])
        return data
    except Exception as e:
        st.error(f"CSV கோப்பைப் படிப்பதில் பிழை: {e}")
        return pd.DataFrame()

# உங்கள் புதிய கூகிள் ஷீட் CSV லிங்க் இங்கே இணைக்கப்பட்டுள்ளது
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSQwApSEm-2EfhP7PVMuZVBUcrD0XGr3tMXMTpX2j-9m5gB3xPgECBEsXjqTtBmW7lnFcrIVuOycN7V/pub?output=csv"

# செஷன் ஸ்டேட் மேலாண்மை
if 'page' not in st.session_state: st.session_state.page = 'login'
if 'user_answers' not in st.session_state: st.session_state.user_answers = {}
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

        # --- 1. லாகின் பக்கம் ---
        if st.session_state.page == 'login':
            st.markdown("<h1 style='text-align:center;'>அரசு மேல்நிலைப்பள்ளி தேவனாங்குறிச்சி</h1>", unsafe_allow_html=True)
            st.divider()
            col1, col2, col3 = st.columns([1,2,1])
            with col2:
                name = st.text_input("மாணவர் பெயர்:", key="user_name_input")
                if st.button("தேர்வைத் தொடங்கு ➡️", type="primary", key="start_exam_btn"):
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
                
                # விடைகளைச் சேகரித்து உரை வடிவில் (String) மாற்றுதல்
                opts = [str(row['Ans-1']), str(row['Ans-2']), str(row['Ans-3']), str(row['Ans-4'])]
                opts = [opt for opt in opts if opt != 'nan'] # காலி விடைகளை நீக்க
                
                if f"opts_{actual_idx}" not in st.session_state:
                    random.shuffle(opts)
                    st.session_state[f"opts_{actual_idx}"] = opts
                
                current_options = st.session_state[f"opts_{actual_idx}"]
                
                # விடைத் தேர்வு
                prev_ans = st.session_state.user_answers.get(actual_idx)
                selected_ans = st.radio("விடைகள்:", current_options, key=f"r_{actual_idx}", 
                                       index=current_options.index(prev_ans) if prev_ans in current_options else None)
                
                if selected_ans:
                    st.session_state.user_answers[actual_idx] = selected_ans

                st.divider()
                
                nav_col1, nav_col2, nav_col3 = st.columns([1, 1, 1])
                with nav_col1:
                    if q_ptr > 0:
                        if st.button("⬅️ முந்தைய", key="prev_action"):
                            st.session_state.current_q_idx -= 1
                            st.rerun()
                with nav_col2:
                    if q_ptr < total_qs - 1:
                        if st.button("அடுத்தது ➡️", key="next_action"):
                            st.session_state.current_q_idx += 1
                            st.rerun()
                with nav_col3:
                    if (q_ptr + 1) % section_limit == 0 or (q_ptr + 1) == total_qs:
                        if st.button("மதிப்பீடு செய் 🚩", type="primary", key="eval_action"):
                            st.session_state.page = 'choice'
                            st.rerun()

            with col_nav:
                st.markdown("<h5 style='text-align:center;'>🔢 வினா பலகம்</h5>", unsafe_allow_html=True)
                grid = st.columns(5)
                start_sec = (q_ptr // section_limit) * section_limit
                end_sec = min(start_sec + section_limit, total_qs)
                
                for i in range(start_sec, end_sec):
                    idx = st.session_state.shuffled_indices[i]
                    with grid[(i - start_sec) % 5]:
                        is_answered = idx in st.session_state.user_answers
                        is_current = (i == q_ptr)
                        
                        bg = "#007bff" if is_current else ("#28a745" if is_answered else "#f0f2f6")
                        txt = "white" if (is_current or is_answered) else "black"
                        brdr = "#0056b3" if is_current else ("#1e7e34" if is_answered else "#ccc")

                        st.markdown(f"""
                            <style>
                            button[key="nav_btn_{i}"] {{
                                background-color: {bg} !important;
                                color: {txt} !important;
                                border: 2px solid {brdr} !important;
                                border-radius: 50% !important;
                                width: 45px !important;
                                height: 45px !important;
                                padding: 0 !important;
                                font-weight: bold !important;
                            }}
                            </style>
                        """, unsafe_allow_html=True)

                        if st.button(f"{i+1}", key=f"nav_btn_{i}"):
                            st.session_state.current_q_idx = i
                            st.rerun()

        # --- 3. மற்ற பக்கங்கள் ---
        elif st.session_state.page == 'choice':
            st.subheader("📍 இந்தப் பகுதி நிறைவுற்றது")
            c1, c2 = st.columns(2)
            with c1:
                if st.button("மதிப்பீடு செய் (Result) ✅", type="primary", key="final_eval"):
                    st.session_state.page = 'evaluate'
                    st.rerun()
            with c2:
                if (st.session_state.current_q_idx + 1) < total_qs:
                    if st.button("அடுத்த பகுதிக்குச் செல் ➡️", key="go_next_sec"):
                        st.session_state.current_q_idx += 1
                        st.session_state.page = 'quiz'
                        st.rerun()

        elif st.session_state.page == 'evaluate':
            st.header(f"📊 தேர்வு மதிப்பீடு: {st.session_state.user_name}")
            overall_score = 0
            limit = st.session_state.current_q_idx + 1
            for i in range(limit):
                idx = st.session_state.shuffled_indices[i]
                u_ans = st.session_state.user_answers.get(idx, "பதிலளிக்கவில்லை")
                correct = str(df.iloc[idx]['Answer'])
                is_ok = (str(u_ans) == correct)
                if is_ok: overall_score += 1
                with st.expander(f"வினா {i+1}: {'✅ சரி' if is_ok else '❌ தவறு'}"):
                    st.write(f"**கேள்வி:** {df.iloc[idx]['Question Text']}")
                    st.write(f"உங்கள் விடை: {u_ans} | சரியான விடை: {correct}")

            st.divider()
            if limit < total_qs:
                if st.button("அடுத்த பகுதிக்குத் தொடரவும் ➡️", type="primary", key="cont_btn"):
                    st.session_state.current_q_idx += 1
                    st.session_state.page = 'quiz'
                    st.rerun()
            else:
                st.balloons()
                st.markdown(f"""<div class="certificate-box"><h1>வெற்றிச் சான்றிதழ்</h1><p>மாணவர் <b>{st.session_state.user_name}</b></p><h2>{overall_score} / {total_qs}</h2><p>{datetime.now().strftime('%d-%m-%Y')}</p></div>""", unsafe_allow_html=True)
                if st.button("🔄 மீண்டும் தேர்வு எழுத", key="restart_btn"):
                    st.session_state.clear()
                    st.rerun()
    else:
        st.warning("தரவு ஏதும் இல்லை. கூகிள் ஷீட்டைச் சரிபார்க்கவும்.")

except Exception as e:
    st.error(f"ஒரு எதிர்பாராத பிழை ஏற்பட்டது: {e}")
