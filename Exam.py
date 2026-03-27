import streamlit as st
import pandas as pd
import random
import requests
from datetime import datetime

# 1. பக்க அமைப்பு
st.set_page_config(page_title="GHSS Devanankurichi - Pro Exam Portal", layout="wide")

# --- CSS: பள்ளி பெயர், கொண்டாட்டம் மற்றும் மறுபார்வை வடிவமைப்பு ---
st.markdown("""
    <style>
    .school-header { text-align: center; background-color: #f0f7ff; padding: 25px; border-radius: 12px; border: 2px solid #1E88E5; margin-bottom: 20px; }
    .school-name { color: #0D47A1; font-size: 2.5rem !important; font-weight: bold; margin: 0; }
    .q-box { border: 1px solid #ddd; padding: 20px; border-radius: 10px; background: white; margin-bottom: 10px; }
    
    /* மறுபார்வை விருப்பங்கள் */
    .option-box { padding: 12px; border-radius: 8px; margin: 6px 0; border: 1px solid #ddd; font-size: 1.1rem; }
    .opt-correct { background-color: #d4edda; border-color: #28a745; color: #155724; font-weight: bold; border-left: 10px solid #28a745; }
    .opt-wrong { background-color: #f8d7da; border-color: #dc3545; color: #721c24; font-weight: bold; border-left: 10px solid #dc3545; }
    .opt-normal { background-color: #f8f9fa; }
    
    div.stButton > button { width: 100% !important; border-radius: 8px !important; height: 55px !important; font-weight: bold !important; font-size: 1.1rem !important; }
    </style>
    """, unsafe_allow_html=True)

# --- மதிப்பெண் சேமிக்கும் செயல்பாடு ---
def save_score(name, subject, score, total):
    API_URL = "https://sheetdb.io/api/v1/w7ktpqhwxaiy9" 
    data = {
        "Name": name,
        "Datetime": datetime.now().strftime("%d-%m-%Y %H:%M"),
        "Subject": subject,
        "Score": score,
        "Total": total
    }
    try:
        requests.post(API_URL, json={"data": [data]})
    except:
        pass

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

    # --- 1. லாகின் பக்கம் ---
    if st.session_state.page == 'login':
        st.markdown('<div class="school-header"><p class="school-name">அரசு மேல்நிலைப்பள்ளி தேவனாங்குறிச்சி</p></div>', unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1,2,1])
        with col2:
            st.subheader("🎓 மாணவர் லாகின்")
            name = st.text_input("மாணவர் பெயர்:", value=st.session_state.get('user_name', ''))
            if not df_raw.empty:
                med_list = sorted(df_raw['Medium'].unique().tolist()) if 'Medium' in df_raw.columns else ["தமிழ்"]
                sel_med = st.selectbox("பயிற்று மொழி:", med_list)
                df_f = df_raw[df_raw['Medium'] == sel_med] if 'Medium' in df_raw.columns else df_raw
                sub_list = sorted(df_f['Subject Code'].unique().tolist())
                sel_sub = st.selectbox("பாடம்:", sub_list)
                df_sub = df_f[df_f['Subject Code'] == sel_sub]
                
                num_q = st.number_input(f"வினாக்கள் எண்ணிக்கை (Max: {len(df_sub)}):", 1, len(df_sub), min(25, len(df_sub)))
                
                if st.button("தேர்வைத் தொடங்கு ➡️", type="primary") and name:
                    st.session_state.user_name, st.session_state.selected_subject = name, sel_sub
                    st.session_state.filtered_df = df_sub.sample(n=num_q).reset_index(drop=True)
                    st.session_state.options_map = {}
                    for i in range(len(st.session_state.filtered_df)):
                        r = st.session_state.filtered_df.iloc[i]
                        opts = [str(r['Ans-1']), str(r['Ans-2']), str(r['Ans-3']), str(r['Ans-4'])]
                        random.shuffle(opts)
                        st.session_state.options_map[i] = opts
                    st.session_state.score_saved, st.session_state.page = False, 'quiz'
                    st.rerun()

    # --- 2. வினாடி வினா பக்கம் ---
    elif st.session_state.page == 'quiz':
        df, q_idx = st.session_state.filtered_df, st.session_state.current_q_idx
        row = df.iloc[q_idx]
        st.session_state.visited.add(q_idx)
        st.markdown('<div class="school-header"><p class="school-name">அரசு மேல்நிலைப்பள்ளி தேவனாங்குறிச்சி</p></div>', unsafe_allow_html=True)
        m_col, n_col = st.columns([7, 3])
        with m_col:
            st.markdown(f'<div class="q-box"><b>வினா {q_idx + 1} / {len(df)}</b><br><h3>{row["Question Text"]}</h3></div>', unsafe_allow_html=True)
            opts = st.session_state.options_map[q_idx]
            curr_ans = st.session_state.user_answers.get(q_idx)
            ans = st.radio("விடை:", opts, key=f"r_{q_idx}", index=opts.index(curr_ans) if curr_ans in opts else None)
            if ans: st.session_state.user_answers[q_idx] = ans
            st.divider()
            b1, b2, b3 = st.columns(3)
            with b1: 
                if q_idx > 0 and st.button("⬅️ முந்தைய"): st.session_state.current_q_idx -= 1; st.rerun()
            with b2:
                if q_idx < len(df)-1 and st.button("அடுத்தது ➡️"): st.session_state.current_q_idx += 1; st.rerun()
            with b3:
                if st.button("🏁 முடி (Submit)", type="primary"): st.session_state.page = 'result'; st.rerun()
        with n_col:
            grid = st.columns(3)
            for i in range(len(df)):
                bg = "#28a745" if i in st.session_state.user_answers else "#f8f9fa"
                with grid[i % 3]:
                    if st.button(f"{i+1}", key=f"btn_{i}"): st.session_state.current_q_idx = i; st.rerun()

    # --- 3. முடிவு பக்கம் ---
    elif st.session_state.page == 'result':
        df = st.session_state.filtered_df
        total = len(df)
        score = sum(1 for i in range(total) if str(st.session_state.user_answers.get(i)) == str(df.iloc[i]['Answer']))
        percent = (score / total) * 100
        
        if not st.session_state.score_saved:
            save_score(st.session_state.user_name, st.session_state.selected_subject, score, total)
            st.session_state.score_saved = True

        if percent >= 80:
            st.snow(); msg, clr = "மிகவும் சிறப்பு! 🌸", "green"
        elif percent >= 40:
            st.balloons(); msg, clr = "நல்ல முயற்சி! 🎈", "#1E88E5"
        else:
            st.warning("மீண்டும் முயற்சி செய்க! 📚"); msg, clr = "கவனம் தேவை! ⚠️", "#d32f2f"

        st.markdown(f'<div style="border:10px solid {clr}; padding:30px; text-align:center; background-color:white;"><h2>அரசு மேல்நிலைப்பள்ளி - தேவனாங்குறிச்சி</h2><hr><h4>{st.session_state.user_name}</h4><h1 style="font-size:3.5rem; color:{clr};">{score} / {total}</h1><h3>{msg}</h3><p style="color:green;">உங்கள் மதிப்பெண் ஆசிரியருக்கு அனுப்பப்பட்டது! ✅</p></div>', unsafe_allow_html=True)
        
        c1, c2 = st.columns(2)
        with c1:
            if st.button("🆕 புதிய தேர்வு"): st.session_state.clear(); st.session_state.page = 'login'; st.rerun()
        with c2:
            if st.button("🔍 விடைகளைச் சரிபார்க்க"): st.session_state.page = 'review'; st.rerun()

    # --- 4. மறுபார்வை பக்கம் ---
    elif st.session_state.page == 'review':
        df = st.session_state.filtered_df
        st.markdown("### 🔍 விடைகளைச் சரிபார்க்க (Detailed Review)")
        for i in range(len(df)):
            row = df.iloc[i]
            u_ans = st.session_state.user_answers.get(i, "பதிலளிக்கவில்லை")
            c_ans = str(row['Answer'])
            st.markdown(f"**வினா {i+1}: {row['Question Text']}**")
            for opt_key in ['Ans-1', 'Ans-2', 'Ans-3', 'Ans-4']:
                opt_val = str(row[opt_key])
                css = "opt-normal"
                if opt_val == c_ans: css = "opt-correct"
                elif opt_val == u_ans and u_ans != c_ans: css = "opt-wrong"
                st.markdown(f'<div class="option-box {css}">{opt_val}</div>', unsafe_allow_html=True)
            st.divider()
        if st.button("⬅️ திரும்பு"): st.session_state.page = 'result'; st.rerun()

except Exception as e: st.error(f"பிழை: {e}")
