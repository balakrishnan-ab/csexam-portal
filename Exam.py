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
    .school-header { text-align: center; background-color: #f0f7ff; padding: 15px; border-radius: 12px; border: 2px solid #1E88E5; margin-bottom: 20px; }
    .school-name { color: #0D47A1; font-size: 2rem !important; font-weight: bold; margin: 0; }
    .q-box { border: 1px solid #ddd; padding: 20px; border-radius: 10px; background: white; margin-bottom: 10px; }
    
    /* வினா பலக பொத்தான்கள் */
    div[data-testid="stColumn"] button {
        padding: 2px !important;
        height: 48px !important;
        width: 100% !important;
        font-size: 0.8rem !important;
        font-weight: bold !important;
    }
    
    .option-box { padding: 12px; border-radius: 8px; margin: 6px 0; border: 1px solid #ddd; }
    .opt-correct { background-color: #d4edda; border-left: 10px solid #28a745; font-weight: bold; }
    .opt-wrong { background-color: #f8d7da; border-left: 10px solid #dc3545; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- மதிப்பெண் சேமிக்கும் செயல்பாடு ---
def save_score(name, std, subject, correct, total, attempted):
    API_URL = "https://sheetdb.io/api/v1/w7ktpqhwxaiy9" 
    payload = {
        "data": [{
            "name": str(name), "Standard": str(std), "Datetime": datetime.now().strftime("%d-%m-%Y %H:%M"),
            "Subject": str(subject), "Total qus": str(total), "Attan": str(attempted),
            "Correct": str(correct), "Wrong": str(attempted - correct), "Score": f"{(correct/total)*100:.1f}%"
        }]
    }
    try:
        response = requests.post(API_URL, json=payload, timeout=10)
        return response.status_code in [200, 201]
    except: return False

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
                
                l_col = 'Lesson Code' if 'Lesson Code' in df_sub.columns else ('Lesson' if 'Lesson' in df_sub.columns else None)
                l_list = sorted(df_sub[l_col].unique().tolist()) if l_col else []
                sel_l = st.multiselect("அலகுகள் (Lessons):", l_list)
                pool = df_sub[df_sub[l_col].isin(sel_l)] if sel_l else df_sub
                
                rem = [idx for idx in pool.index if idx not in st.session_state.seen_ids]
                if not rem: st.session_state.seen_ids = set(); rem = list(pool.index)
                num_q = st.number_input(f"புதிய வினாக்கள் எண்ணிக்கை:", 1, len(rem), min(len(rem), 25))
                
                if st.button("தேர்வைத் தொடங்கு ➡️", type="primary") and u_name:
                    st.session_state.user_name, st.session_state.selected_std, st.session_state.selected_subject = u_name, sel_std, sel_sub
                    cur_sel = random.sample(rem, num_q)
                    st.session_state.filtered_df = pool.loc[cur_sel].reset_index(drop=True)
                    for idx in cur_sel: st.session_state.seen_ids.add(idx)
                    st.session_state.options_map = {i: random.sample([str(st.session_state.filtered_df.iloc[i][f'Ans-{j}']) for j in range(1,5)], 4) for i in range(len(st.session_state.filtered_df))}
                    st.session_state.user_answers, st.session_state.visited, st.session_state.marked = {}, set(), set()
                    st.session_state.current_q_idx, st.session_state.score_saved, st.session_state.page = 0, False, 'quiz'; st.rerun()

    elif st.session_state.page == 'quiz':
        df, q_idx = st.session_state.filtered_df, st.session_state.current_q_idx
        row = df.iloc[q_idx]; st.session_state.visited.add(q_idx)
        st.markdown('<div class="school-header"><p class="school-name">அரசு மேல்நிலைப்பள்ளி தேவனாங்குறிச்சி</p></div>', unsafe_allow_html=True)
        m_col, n_col = st.columns([7.5, 2.5])
        with m_col:
            st.markdown(f'<div class="q-box"><b>வினா {q_idx + 1} / {len(df)}</b><br><h3>{row["Question Text"]}</h3></div>', unsafe_allow_html=True)
            opts = st.session_state.options_map[q_idx]; curr_ans = st.session_state.user_answers.get(q_idx)
            ans = st.radio("விடை:", opts, key=f"r_{q_idx}", index=opts.index(curr_ans) if curr_ans in opts else None)
            if ans: st.session_state.user_answers[q_idx] = ans
            st.checkbox("🚩 சந்தேகம் (Review)", value=(q_idx in st.session_state.marked), key=f"m_{q_idx}", on_change=lambda: st.session_state.marked.add(q_idx) if st.session_state[f"m_{q_idx}"] else st.session_state.marked.discard(q_idx))
            st.divider()
            b1, b2, b3 = st.columns(3)
            with b1: 
                if q_idx > 0 and st.button("⬅️ முந்தைய"): st.session_state.current_q_idx -= 1; st.rerun()
            with b2:
                if q_idx < len(df)-1 and st.button("அடுத்தது ➡️"): st.session_state.current_q_idx += 1; st.rerun()
            with b3:
                if st.button("🏁 முடி (Submit)", type="primary"): st.session_state.page = 'result'; st.rerun()
        
        with n_col:
            st.markdown("<p style='text-align:center; font-weight:bold;'>🔢 வினா பலகம்</p>", unsafe_allow_html=True)
            grid = st.columns(5)
            for i in range(len(df)):
                is_m = i in st.session_state.marked
                is_a = i in st.session_state.user_answers
                is_v = i in st.session_state.visited
                
                # நீங்கள் கேட்ட வண்ணக் குறியீடுகள்
                if is_m and is_a: lbl, bg, txt = f"💜🚩{i+1}", "#673AB7", "white"
                elif is_m: lbl, bg, txt = f"🟠🚩{i+1}", "#FF9800", "white"
                elif is_a: lbl, bg, txt = f"✅{i+1}", "#28A745", "white"
                elif is_v: lbl, bg, txt = f"🔵{i+1}", "#2196F3", "white"
                else: lbl, bg, txt = f"{i+1}", "#F8F9FA", "#333"
                
                with grid[i % 5]:
                    if st.button(lbl, key=f"btn_{i}"): st.session_state.current_q_idx = i; st.rerun()
                    st.markdown(f"<style>button[key='btn_{i}'] {{ background-color: {bg} !important; color: {txt} !important; border: {'2px solid black' if i==q_idx else '1px solid #CCC'} !important; }}</style>", unsafe_allow_html=True)

    elif st.session_state.page == 'result':
        df = st.session_state.filtered_df; total = len(df)
        attempted = len(st.session_state.user_answers)
        correct = sum(1 for i in range(total) if str(st.session_state.user_answers.get(i)) == str(df.iloc[i]['Answer']))
        if not st.session_state.get('score_saved', False):
            success = save_score(st.session_state.user_name, st.session_state.selected_std, st.session_state.selected_subject, correct, total, attempted)
            st.session_state.score_saved = True
            if success: st.success("மதிப்பெண் சேமிக்கப்பட்டது! ✅")
        st.markdown(f'<div style="border:10px solid #1E88E5; padding:30px; text-align:center; background-color:white;"><h2>அரசு மேல்நிலைப்பள்ளி - தேவனாங்குறிச்சி</h2><hr><h1>சரியானவை: {correct} / {total}</h1></div>', unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3)
        with c1:
            if st.button("🔄 மீண்டும் (அதே வினாக்கள்)"):
                st.session_state.user_answers, st.session_state.visited, st.session_state.marked = {}, set(), set()
                st.session_state.current_q_idx, st.session_state.score_saved, st.session_state.page = 0, False, 'quiz'; st.rerun()
        with c2:
            if st.button("🆕 புதிய வினாக்கள்"): st.session_state.page = 'login'; st.rerun()
        with c3:
            if st.button("🔍 மறுபார்வை"): st.session_state.page = 'review'; st.rerun()

    elif st.session_state.page == 'review':
        df = st.session_state.filtered_df; st.markdown("### 🔍 வினா வாரியான மறுபார்வை")
        for i in range(len(df)):
            row = df.iloc[i]; u_ans = st.session_state.user_answers.get(i); c_ans = str(row['Answer'])
            st.markdown(f"**வினா {i+1}: {row['Question Text']}**")
            for j in range(1, 5):
                opt = str(row[f'Ans-{j}']); css = "option-box"
                if opt == c_ans: css += " opt-correct"
                elif u_ans is not None and opt == str(u_ans) and str(u_ans) != c_ans: css += " opt-wrong"
                st.markdown(f'<div class="{css}">{opt}</div>', unsafe_allow_html=True)
            st.divider()
        if st.button("⬅️ திரும்பு"): st.session_state.page = 'result'; st.rerun()

except Exception as e: st.error(f"பிழை: {e}")
