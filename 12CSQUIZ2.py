import streamlit as st
import pandas as pd
import random
from datetime import datetime

# 1. பக்க அமைப்பு
st.set_page_config(page_title="தேர்வு மையம்", layout="wide")

# --- CSS: துல்லியமான வடிவமைப்பு ---
st.markdown("""
    <style>
    .block-container { padding-top: 1.5rem; }
    .header-row { display: flex; justify-content: space-between; align-items: center; width: 100%; margin-bottom: 10px; }
    .school-name { color: #1E88E5; font-size: clamp(1.2rem, 3vw, 2.2rem); font-weight: bold; margin: 0; }
    
    /* வினா பலக வட்டங்கள் மட்டும் */
    .nav-btn {
        border-radius: 50% !important;
        width: 45px !important;
        height: 45px !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        font-weight: bold !important;
        margin: auto !important;
        border: 2px solid #ccc !important;
    }

    /* விடை அளித்திருந்தால் பச்சை நிறம் (உள்ளே எண் தெரியும்) */
    .answered-btn {
        background-color: #28a745 !important;
        color: white !important;
        border-color: #1e7e34 !important;
    }

    /* தற்போதைய வினா - நீல நிறம் */
    .current-btn {
        background-color: #007bff !important;
        color: white !important;
        border-color: #0056b3 !important;
    }

    /* சாதாரண பொத்தான்கள் (அடுத்து, முந்தைய) - செவ்வக வடிவம் */
    .stButton > button:not(.nav-btn) {
        border-radius: 5px !important;
        width: auto !important;
        height: auto !important;
        padding: 8px 20px !important;
    }
    
    .certificate-box { border: 10px double #1E88E5; padding: 40px; text-align: center; background: white; margin-top: 20px; }
    </style>
    """, unsafe_allow_html=True)

@st.cache_data(ttl=60)
def get_data(url):
    data = pd.read_csv(url)
    data.columns = data.columns.str.strip()
    return data

SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSQwApSEm-2EfhP7PVMuZVBUcrD0XGr3tMXMTpX2j-9m5gB3xPgECBEsXjqTtBmW7lnFcrIVuOycN7V/pub?output=csv" 

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

    # --- 1. லாகின் ---
    if st.session_state.page == 'login':
        st.markdown("<h1 style='text-align:center;'>அரசு மேல்நிலைப்பள்ளி தேவனாங்குறிச்சி</h1>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1,2,1])
        with col2:
            name = st.text_input("மாணவர் பெயர்:")
            if st.button("தேர்வைத் தொடங்கு ➡️", type="primary", use_container_width=True):
                if name:
                    st.session_state.user_name = name
                    st.session_state.page = 'quiz'
                    st.rerun()
                else: st.error("பெயரை உள்ளிடவும்!")

    # --- 2. வினாடி வினா ---
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
            
            opts = [str(row['Ans-1']), str(row['Ans-2']), str(row['Ans-3']), str(row['Ans-4'])]
            if f"opts_{actual_idx}" not in st.session_state:
                random.shuffle(opts)
                st.session_state[f"opts_{actual_idx}"] = opts
            
            ans = st.radio("விடைகள்:", st.session_state[f"opts_{actual_idx}"], key=f"r_{actual_idx}", 
                           index=st.session_state[f"opts_{actual_idx}"].index(st.session_state.user_answers[actual_idx]) if actual_idx in st.session_state.user_answers else None)
            if ans: 
                st.session_state.user_answers[actual_idx] = ans
                st.rerun() # விடை அளித்தவுடன் பலகத்தில் நிறம் மாற

            st.divider()
            b1, b2, b3 = st.columns([1, 1, 1])
            with b1:
                if q_ptr > 0 and st.button("⬅️ முந்தைய", use_container_width=True):
                    st.session_state.current_q_idx -= 1
                    st.rerun()
            with b2:
                if q_ptr < total_qs - 1 and st.button("அடுத்தது ➡️", use_container_width=True):
                    st.session_state.current_q_idx += 1
                    st.rerun()
            with b3:
                if (q_ptr + 1) % section_limit == 0 or (q_ptr + 1) == total_qs:
                    if st.button("மதிப்பீடு செய் 🚩", type="primary", use_container_width=True):
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
                    
                    # ஸ்டைல் முடிவு செய்தல்
                    btn_label = f"{i+1}"
                    if is_current:
                        st.markdown(f'<style>button[key="btn_{i}"] {{ background-color: #007bff !important; color: white !important; border-radius: 50% !important; width: 45px !important; height: 45px !important; font-weight: bold !important; border: 2px solid #0056b3 !important; padding: 0 !important; }}</style>', unsafe_allow_html=True)
                    elif is_answered:
                        st.markdown(f'<style>button[key="btn_{i}"] {{ background-color: #28a745 !important; color: white !important; border-radius: 50% !important; width: 45px !important; height: 45px !important; font-weight: bold !important; border: 2px solid #1e7e34 !important; padding: 0 !important; }}</style>', unsafe_allow_html=True)
                    else:
                        st.markdown(f'<style>button[key="btn_{i}"] {{ border-radius: 50% !important; width: 45px !important; height: 45px !important; font-weight: bold !important; border: 2px solid #ccc !important; padding: 0 !important; }}</style>', unsafe_allow_html=True)

                    if st.button(btn_label, key=f"btn_{i}"):
                        st.session_state.current_q_idx = i
                        st.rerun()

    # --- 3. மற்ற பக்கங்கள் (மதிப்பீடு/சான்றிதழ்) ---
    elif st.session_state.page == 'choice':
        st.subheader("📍 இந்தப் பகுதி நிறைவுற்றது")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("மதிப்பீடு செய் (Result) ✅", use_container_width=True, type="primary"):
                st.session_state.page = 'evaluate'
                st.rerun()
        with c2:
            if (st.session_state.current_q_idx + 1) < total_qs:
                if st.button("அடுத்த பகுதிக்குச் செல் ➡️", use_container_width=True):
                    st.session_state.current_q_idx += 1
                    st.session_state.page = 'quiz'
                    st.rerun()
            else: st.warning("இதுவே கடைசிப் பகுதி.")

    elif st.session_state.page == 'evaluate':
        st.header(f"📊 தேர்வு மதிப்பீடு: {st.session_state.user_name}")
        overall_score = 0
        limit = st.session_state.current_q_idx + 1
        for i in range(limit):
            idx = st.session_state.shuffled_indices[i]
            u_ans = st.session_state.user_answers.get(idx, "பதிலளிக்கவில்லை")
            correct = str(df.iloc[idx]['Answer'])
            is_ok = (u_ans == correct)
            if is_ok: overall_score += 1
            with st.expander(f"வினா {i+1}: {'✅ சரி' if is_ok else '❌ தவறு'}"):
                st.write(f"**கேள்வி:** {df.iloc[idx]['Question Text']}")
                st.write(f"உங்கள் விடை: {u_ans} | சரியான விடை: {correct}")

        st.divider()
        if limit < total_qs:
            if st.button("அடுத்த பகுதிக்குத் தொடரவும் ➡️", type="primary"):
                st.session_state.current_q_idx += 1
                st.session_state.page = 'quiz'
                st.rerun()
        else:
            st.balloons()
            st.markdown(f"""<div class="certificate-box"><h1>வெற்றிச் சான்றிதழ்</h1><p>மாணவர் <b>{st.session_state.user_name}</b></p><h2>{overall_score} / {total_qs}</h2><p>{datetime.now().strftime('%d-%m-%Y')}</p></div>""", unsafe_allow_html=True)
            if st.button("மீண்டும் தேர்வு எழுத 🔄"):
                st.session_state.clear()
                st.rerun()

except Exception as e:
    st.error(f"பிழை: {e}")
