import streamlit as st
import pandas as pd
import random
import requests
from datetime import datetime

# 1. பக்க அமைப்பு
st.set_page_config(page_title="GHSS Devanankurichi - Pro Exam Portal", layout="wide")

# --- CSS: கச்சிதமான வடிவமைப்பு ---
st.markdown("""
    <style>
    .school-header { text-align: center; background-color: #f0f7ff; padding: 20px; border-radius: 12px; border: 2px solid #1E88E5; margin-bottom: 20px; }
    .school-name { color: #0D47A1; font-size: 2.2rem !important; font-weight: bold; margin: 0; }
    .q-box { border: 1px solid #ddd; padding: 20px; border-radius: 10px; background: white; margin-bottom: 10px; }
    div[data-testid="stColumn"] button { padding: 5px !important; height: 45px !important; width: 100% !important; font-size: 0.9rem !important; }
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

# செஷன் ஸ்டேட் தொடக்கம்
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
                # 1. வகுப்பு தேர்வு
                std_list = sorted(df_raw['Standard'].unique().tolist()) if 'Standard' in df_raw.columns else ["10", "12"]
                sel_std = st.selectbox("வகுப்பு:", std_list)
                df_std = df_raw[df_raw['Standard'].astype(str) == str(sel_std)]
                
                # 2. பாடம் தேர்வு
                sub_list = sorted(df_std['Subject Code'].unique().tolist())
                sel_sub = st.selectbox("பாடம்:", sub_list)
                df_sub = df_std[df_std['Subject Code'] == sel_sub]
                
                # 3. அலகு (Lesson) தேர்வு - புதிய வசதி
                lesson_col = 'Lesson Code' if 'Lesson Code' in df_sub.columns else ('Lesson' if 'Lesson' in df_sub.columns else None)
                final_df = df_sub.copy()
                
                if lesson_col:
                    lesson_list = sorted(df_sub[lesson_col].unique().tolist())
                    sel_lessons = st.multiselect("அலகுகள் (Lessons) - அனைத்திற்கும் காலியாக விடவும்:", lesson_list)
                    if sel_lessons:
                        final_df = df_sub[df_sub[lesson_col].isin(sel_lessons)]
                
                # 4. வினாக்கள் எண்ணிக்கை
                num_q = st.number_input(f"வினாக்கள் எண்ணிக்கை (அதிகபட்சம் {len(final_df)}):", 1, len(final_df), min(len(final_df), 25))
                
                if st.button("தேர்வைத் தொடங்கு ➡️", type="primary") and name:
                    st.session_state.user_name, st.session_state.selected_std, st.session_state.selected_subject = name, sel_std, sel_sub
                    st.session_state.filtered_df = final_df.sample(n=num_q).reset_index(drop=True)
                    st.session_state.options_map = {i: random.sample([str(st.session_state.filtered_df.iloc[i][f'Ans-{j}']) for j in range(1,5)], 4) for i in range(len(st.session_state.filtered_df))}
                    st.session_state.score_saved = False
                    st.session_state.page = 'quiz'; st.rerun()

    # --- 2. வினாடி வினா ---
    elif st.session_state.page == 'quiz':
        df, q_idx = st.session_state.filtered_df, st.session_state.current_q_idx
        row = df.iloc[q_idx]
        st.session_state.visited.add(q_idx)
        st.markdown('<div class="school-header"><p class="school-name">அரசு மேல்நிலைப்பள்ளி தேவனாங்குறிச்சி</p></div>', unsafe_allow_html=True)
        
        m_col, n_col = st.columns([7.5, 2.5])
        with m_col:
            st.markdown(f'<div class="q-box"><b>வினா {q_idx + 1} / {len(df)}</b><br><h3>{row["Question Text"]}</h3></div>', unsafe_allow_html=True)
            opts = st.session_state.options_map[q_idx]
            curr_ans = st.session_state.user_answers.get(q_idx)
            ans = st.radio("விடை:", opts, key=f"r_{q_idx}", index=opts.index(curr_ans) if curr_ans in opts else None)
            if ans: st.session_state.user_answers[q_idx] = ans
            st.checkbox("🚩 சந்தேகம்", value=(q_idx in st.session_state.marked), key=f"m_{q_idx}", on_change=lambda: st.session_state.marked.add(q_idx) if st.session_state[f"m_{q_idx}"] else st.session_state.marked.discard(q_idx))
            st.divider()
            b1, b2, b3 = st.columns(3)
            with b1: 
                if q_idx > 0 and st.button("⬅️ முந்தைய"): st.session_state.current_q_idx -= 1; st.rerun()
            with b2:
                if q_idx < len(df)-1 and st.button("அடுத்தது ➡️"): st.session_state.current_q_idx += 1; st.rerun()
            with b3:
                if st.button("🏁 முடி (Submit)", type="primary"): st.session_state.page = 'result'; st.rerun()
        
        with n_col:
            grid = st.columns(5)
            for i in range(len(df)):
                lbl = f"{i+1}"; bg = "#f8f9fa"; txt = "#333"
                if i in st.session_state.marked: lbl = "🚩"; bg = "#FF9800"; txt = "white"
                elif i in st.session_state.user_answers: lbl = "✅"; bg = "#28a745"; txt = "white"
                elif i in st.session_state.visited: bg = "#2196F3"; txt = "white"
                with grid[i % 5]:
                    if st.button(lbl if lbl in ["🚩","✅"] else f"{i+1}", key=f"btn_{i}"):
                        st.session_state.current_q_idx = i; st.rerun()
                    st.markdown(f"<style>button[key='btn_{i}'] {{ background-color: {bg} !important; color: {txt} !important; border: {'3px solid black' if i==q_idx else '1px solid #ccc'} !important; }}</style>", unsafe_allow_html=True)

    # --- 3. முடிவு ---
    elif st.session_state.page == 'result':
        df = st.session_state.filtered_df
        score = sum(1 for i in range(len(df)) if str(st.session_state.user_answers.get(i)) == str(df.iloc[i]['Answer']))
        if not st.session_state.score_saved:
            save_score(st.session_state.user_name, st.session_state.selected_std, st.session_state.selected_subject, score, len(df))
            st.session_state.score_saved = True
        
        st.markdown(f'<div style="border:10px solid #1E88E5; padding:30px; text-align:center; background-color:white;"><h2>அரசு மேல்நிலைப்பள்ளி - தேவனாங்குறிச்சி</h2><hr><h1>{score} / {len(df)}</h1></div>', unsafe_allow_html=True)
        
        c1, c2, c3 = st.columns(3)
        with c1:
            if st.button("🔄 அதே வினாக்களை மீண்டும் எழுத"):
                st.session_state.user_answers = {}; st.session_state.visited = set(); st.session_state.marked = set()
                st.session_state.current_q_idx = 0; st.session_state.score_saved = False
                st.session_state.page = 'quiz'; st.rerun()
        with c2:
            if st.button("🆕 புதிய தேர்வு"):
                un = st.session_state.user_name; st.session_state.clear(); st.session_state.user_name = un
                st.session_state.page = 'login'; st.rerun()
        with c3:
            if st.button("🔍 மறுபார்வை"): st.session_state.page = 'review'; st.rerun()

    # --- 4. மறுபார்வை ---
    elif st.session_state.page == 'review':
        df = st.session_state.filtered_df
        st.markdown("### 🔍 வினா வாரியான மறுபார்வை")
        for i in range(len(df)):
            row = df.iloc[i]; u_ans = st.session_state.user_answers.get(i); c_ans = str(row['Answer'])
            st.markdown(f"**வினா {i+1}: {row['Question Text']}**")
            if u_ans is None: st.warning("⚠️ நீங்கள் பதிலளிக்கவில்லை")
            for j in range(1, 5):
                opt = str(row[f'Ans-{j}']); css = "option-box"
                if opt == c_ans: css += " opt-correct"
                elif u_ans is not None and opt == str(u_ans) and str(u_ans) != c_ans: css += " opt-wrong"
                st.markdown(f'<div class="{css}">{opt}</div>', unsafe_allow_html=True)
            st.divider()
        if st.button("⬅️ திரும்பு"): st.session_state.page = 'result'; st.rerun()

except Exception as e: st.error(f"பிழை: {e}")
