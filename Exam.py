import streamlit as st
import pandas as pd
import random
import requests
from datetime import datetime

# 1. பக்க அமைப்பு
st.set_page_config(page_title="GHSS Devanankurichi - Exam Portal", layout="wide")

# --- CSS: குறியீடுகள் மற்றும் வடிவமைப்பு ---
st.markdown("""
    <style>
    .school-header { text-align: center; background-color: #f0f7ff; padding: 20px; border-radius: 12px; border: 2px solid #1E88E5; margin-bottom: 20px; }
    .school-name { color: #0D47A1; font-size: 2.5rem !important; font-weight: bold; margin: 0; }
    .q-box { border: 1px solid #ddd; padding: 20px; border-radius: 10px; background: white; margin-bottom: 10px; }
    
    /* வினா பலக பொத்தான்கள் */
    div.stButton > button { width: 100% !important; border-radius: 8px !important; height: 50px !important; font-weight: bold !important; font-size: 1rem !important; }
    
    /* மறுபார்வை */
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

    if st.session_state.page == 'login':
        st.markdown('<div class="school-header"><p class="school-name">அரசு மேல்நிலைப்பள்ளி தேவனாங்குறிச்சி</p></div>', unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1,2,1])
        with col2:
            st.subheader("🎓 மாணவர் லாகின்")
            name = st.text_input("மாணவர் பெயர்:")
            if not df_raw.empty:
                std_list = sorted(df_raw['Standard'].unique().tolist()) if 'Standard' in df_raw.columns else ["10", "12"]
                sel_std = st.selectbox("வகுப்பு (Standard):", std_list)
                df_std = df_raw[df_raw['Standard'].astype(str) == str(sel_std)] if 'Standard' in df_raw.columns else df_raw
                med_list = sorted(df_std['Medium'].unique().tolist()) if 'Medium' in df_std.columns else ["தமிழ்"]
                sel_med = st.selectbox("பயிற்று மொழி:", med_list)
                df_med = df_std[df_std['Medium'] == sel_med] if 'Medium' in df_std.columns else df_std
                sub_list = sorted(df_med['Subject Code'].unique().tolist())
                sel_sub = st.selectbox("பாடம்:", sub_list)
                df_sub = df_med[df_med['Subject Code'] == sel_sub]
                num_q = st.number_input(f"வினாக்கள் எண்ணிக்கை:", 1, len(df_sub), min(25, len(df_sub)))
                
                if st.button("தேர்வைத் தொடங்கு ➡️", type="primary") and name:
                    st.session_state.user_name, st.session_state.selected_std, st.session_state.selected_subject = name, sel_std, sel_sub
                    st.session_state.filtered_df = df_sub.sample(n=num_q).reset_index(drop=True)
                    st.session_state.options_map = {i: random.sample([str(df_sub.iloc[i][f'Ans-{j}']) for j in range(1,5)], 4) for i in range(len(st.session_state.filtered_df))}
                    st.session_state.score_saved, st.session_state.page = False, 'quiz'
                    st.rerun()

    elif st.session_state.page == 'quiz':
        df, q_idx = st.session_state.filtered_df, st.session_state.current_q_idx
        row = df.iloc[q_idx]
        st.session_state.visited.add(q_idx)
        st.markdown('<div class="school-header"><p class="school-name">அரசு மேல்நிலைப்பள்ளி தேவனாங்குறிச்சி</p></div>', unsafe_allow_html=True)
        m_col, n_col = st.columns([7, 3])
        with m_col:
            st.markdown(f'<div class="q-box"><b>வகுப்பு {st.session_state.selected_std} | வினா {q_idx + 1} / {len(df)}</b><br><h3>{row["Question Text"]}</h3></div>', unsafe_allow_html=True)
            opts = st.session_state.options_map[q_idx]
            curr_ans = st.session_state.user_answers.get(q_idx)
            ans = st.radio("விடை:", opts, key=f"r_{q_idx}", index=opts.index(curr_ans) if curr_ans in opts else None)
            if ans: st.session_state.user_answers[q_idx] = ans
            st.checkbox("🚩 சந்தேகம் (Mark for Review)", value=(q_idx in st.session_state.marked), key=f"m_{q_idx}", on_change=lambda: st.session_state.marked.add(q_idx) if st.session_state[f"m_{q_idx}"] else st.session_state.marked.discard(q_idx))
            st.divider()
            b1, b2, b3 = st.columns(3)
            with b1: 
                if q_idx > 0 and st.button("⬅️ முந்தைய"): st.session_state.current_q_idx -= 1; st.rerun()
            with b2:
                if q_idx < len(df)-1 and st.button("அடுத்தது ➡️"): st.session_state.current_q_idx += 1; st.rerun()
            with b3:
                if st.button("🏁 முடி (Submit)", type="primary"): st.session_state.page = 'result'; st.rerun()
        
        with n_col:
            st.markdown("##### 🔢 வினா பலகம்")
            grid = st.columns(3)
            for i in range(len(df)):
                # வண்ணங்கள் மற்றும் ஐகான்கள் தர்க்கம்
                lbl = f"{i+1}"; bg = "#f8f9fa"; txt = "#333"
                is_m = i in st.session_state.marked; is_a = i in st.session_state.user_answers
                
                if is_m and is_a: lbl = f"💜🚩{i+1}"; bg = "#673AB7"; txt = "white"
                elif is_m: lbl = f"🟠🚩{i+1}"; bg = "#FF9800"; txt = "white"
                elif is_a: lbl = f"✅{i+1}"; bg = "#28a745"; txt = "white"
                elif i in st.session_state.visited: lbl = f"🔵{i+1}"; bg = "#2196F3"; txt = "white"
                
                with grid[i % 3]:
                    if st.button(lbl, key=f"btn_{i}"): st.session_state.current_q_idx = i; st.rerun()
                    st.markdown(f"<style>button[key='btn_{i}'] {{ background-color: {bg} !important; color: {txt} !important; border: {'3px solid black' if i==q_idx else '1px solid #ccc'} !important; }}</style>", unsafe_allow_html=True)

    elif st.session_state.page == 'result':
        df = st.session_state.filtered_df
        total = len(df)
        score = sum(1 for i in range(total) if str(st.session_state.user_answers.get(i)) == str(df.iloc[i]['Answer']))
        if not st.session_state.score_saved:
            save_score(st.session_state.user_name, st.session_state.selected_std, st.session_state.selected_subject, score, total)
            st.session_state.score_saved = True
        
        percent = (score / total) * 100
        if percent >= 80: st.snow()
        elif percent >= 40: st.balloons()
        
        st.markdown(f'<div style="border:10px solid #1E88E5; padding:30px; text-align:center; background-color:white;"><h2>அரசு மேல்நிலைப்பள்ளி - தேவனாங்குறிச்சி</h2><hr><h4>{st.session_state.user_name}</h4><h1 style="font-size:3.5rem; color:#d32f2f;">{score} / {total}</h1></div>', unsafe_allow_html=True)
        col_res1, col_res2 = st.columns(2)
        with col_res1:
            if st.button("🆕 புதிய தேர்வு"): st.session_state.clear(); st.session_state.page = 'login'; st.rerun()
        with col_res2:
            if st.button("🔍 மறுபார்வை"): st.session_state.page = 'review'; st.rerun()

    elif st.session_state.page == 'review':
        df = st.session_state.filtered_df
        st.markdown("### 🔍 வினா வாரியான மறுபார்வை")
        for i in range(len(df)):
            row = df.iloc[i]; u_ans = st.session_state.user_answers.get(i, "பதிலளிக்கவில்லை"); c_ans = str(row['Answer'])
            st.markdown(f"**வினா {i+1}: {row['Question Text']}**")
            for j in range(1, 5):
                opt = str(row[f'Ans-{j}']); css = "option-box"
                if opt == c_ans: css += " opt-correct"
                elif opt == u_ans and u_ans != c_ans: css += " opt-wrong"
                st.markdown(f'<div class="{css}">{opt}</div>', unsafe_allow_html=True)
            st.divider()
        if st.button("⬅️ திரும்பு"): st.session_state.page = 'result'; st.rerun()

except Exception as e: st.error(f"பிழை: {e}")
