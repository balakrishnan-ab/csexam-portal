import streamlit as st
import pandas as pd
import random
import requests
from datetime import datetime

# 1. பக்க அமைப்பு
st.set_page_config(page_title="GHSS Devanankurichi - Exam Portal", layout="wide")

# --- CSS வடிவமைப்பு ---
st.markdown("""
    <style>
    .school-header { text-align: center; background-color: #f0f7ff; padding: 15px; border-radius: 12px; border: 2px solid #1E88E5; margin-bottom: 20px; }
    .school-name { color: #0D47A1; font-size: 2rem !important; font-weight: bold; margin: 0; }
    .q-box { border: 1px solid #ddd; padding: 20px; border-radius: 10px; background: white; margin-bottom: 10px; }
    .option-box { padding: 12px; border-radius: 8px; margin: 6px 0; border: 1px solid #ddd; }
    .opt-correct { background-color: #d4edda; border-left: 10px solid #28a745; font-weight: bold; }
    .opt-wrong { background-color: #f8d7da; border-left: 10px solid #dc3545; font-weight: bold; }
    div[data-testid="stColumn"] button { padding: 5px !important; height: 40px !important; width: 100% !important; }
    </style>
    """, unsafe_allow_html=True)

# --- மதிப்பெண் சேமிக்கும் செயல்பாடு (உங்கள் தலைப்புகளுக்கு ஏற்ப மாற்றப்பட்டது) ---
def save_score(name, std, subject, score, total):
    API_URL = "https://sheetdb.io/api/v1/w7ktpqhwxaiy9" 
    
    # உங்கள் ஷீட்டில் உள்ள தலைப்புகள் (Case Sensitive)
    data = {
        "name": name,             # 'n' சிறிய எழுத்து
        "Standard": str(std),     # 'S' பெரிய எழுத்து
        "Datetime": datetime.now().strftime("%d-%m-%Y %H:%M"),
        "Subject": subject,
        "Score": score,
        "Total": total
    }
    try:
        response = requests.post(API_URL, json={"data": [data]})
        return response.status_code == 201
    except:
        return False

@st.cache_data(ttl=60)
def get_data(url):
    try:
        data = pd.read_csv(url)
        data.columns = data.columns.str.strip()
        return data.dropna(subset=['Question Text'])
    except: return pd.DataFrame()

SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSQwApSEm-2EfhP7PVMuZVBUcrD0XGr3tMXMTpX2j-9m5gB3xPgECBEsXjqTtBmW7lnFcrIVuOycN7V/pub?output=csv"

# செஷன் ஸ்டேட் (வினாக்கள் மீண்டும் வராமல் தடுக்க 'seen_ids' பயன்படுத்தப்படுகிறது)
if 'page' not in st.session_state: st.session_state.page = 'login'
if 'seen_ids' not in st.session_state: st.session_state.seen_ids = set()
if 'user_answers' not in st.session_state: st.session_state.user_answers = {}
if 'visited' not in st.session_state: st.session_state.visited = set()
if 'marked' not in st.session_state: st.session_state.marked = set()
if 'current_q_idx' not in st.session_state: st.session_state.current_q_idx = 0

try:
    df_raw = get_data(SHEET_URL)

    # --- 1. லாகின் பக்கம் ---
    if st.session_state.page == 'login':
        st.markdown('<div class="school-header"><p class="school-name">அரசு மேல்நிலைப்பள்ளி தேவனாங்குறிச்சி</p></div>', unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1,2,1])
        with col2:
            st.subheader("🎓 மாணவர் லாகின்")
            name_input = st.text_input("மாணவர் பெயர்:", value=st.session_state.get('user_name', ''))
            
            if not df_raw.empty:
                std_list = sorted(df_raw['Standard'].unique().tolist())
                sel_std = st.selectbox("வகுப்பு:", std_list)
                df_std = df_raw[df_raw['Standard'].astype(str) == str(sel_std)]

                med_list = sorted(df_std['Medium'].unique().tolist())
                sel_med = st.selectbox("பயிற்று மொழி:", med_list)
                df_med = df_std[df_std['Medium'] == sel_med]
                
                sub_list = sorted(df_med['Subject Code'].unique().tolist())
                sel_sub = st.selectbox("பாடம்:", sub_list)
                df_sub = df_med[df_med['Subject Code'] == sel_sub]
                
                lesson_col = 'Lesson Code' if 'Lesson Code' in df_sub.columns else 'Lesson'
                lesson_list = sorted(df_sub[lesson_col].unique().tolist())
                sel_lessons = st.multiselect("அலகுகள் (Lessons):", lesson_list)
                
                pool = df_sub[df_sub[lesson_col].isin(sel_lessons)] if sel_lessons else df_sub
                
                # --- வினாக்கள் மீண்டும் வராமல் தடுக்கும் பகுதி ---
                # வினாக்களின் ID அல்லது Index-ஐ வைத்து வடிகட்டுதல்
                remaining_indices = [idx for idx in pool.index if idx not in st.session_state.seen_ids]
                
                if not remaining_indices:
                    st.warning("அனைத்து வினாக்களையும் முடித்துவிட்டீர்கள்! மீண்டும் ஆரம்பத்தில் இருந்து வினாக்கள் வரும்.")
                    st.session_state.seen_ids = set()
                    remaining_indices = list(pool.index)

                num_q = st.number_input(f"புதிய வினாக்கள் எண்ணிக்கை (மீதம்: {len(remaining_indices)}):", 1, len(remaining_indices), min(len(remaining_indices), 25))
                
                if st.button("தேர்வைத் தொடங்கு ➡️", type="primary") and name_input:
                    st.session_state.user_name = name_input
                    st.session_state.selected_std = sel_std
                    st.session_state.selected_subject = sel_sub
                    
                    # புதிய வினாக்களைத் தேர்ந்தெடுத்தல்
                    current_selection = random.sample(remaining_indices, num_q)
                    st.session_state.filtered_df = pool.loc[current_selection].reset_index(drop=True)
                    
                    # பார்த்த வினாக்களைச் சேமித்தல்
                    for idx in current_selection: st.session_state.seen_ids.add(idx)
                    
                    # ஆப்ஷன்களை கலைத்தல்
                    st.session_state.options_map = {i: random.sample([str(st.session_state.filtered_df.iloc[i][f'Ans-{j}']) for j in range(1,5)], 4) for i in range(len(st.session_state.filtered_df))}
                    
                    st.session_state.user_answers = {}; st.session_state.visited = set(); st.session_state.marked = set()
                    st.session_state.current_q_idx = 0; st.session_state.score_saved = False
                    st.session_state.page = 'quiz'; st.rerun()

    # --- 2. வினாடி வினா பக்கம் ---
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
                lbl = "✅" if i in st.session_state.user_answers else ("🚩" if i in st.session_state.marked else f"{i+1}")
                bg = "#28a745" if i in st.session_state.user_answers else ("#FF9800" if i in st.session_state.marked else "#f8f9fa")
                with grid[i % 5]:
                    if st.button(lbl, key=f"btn_{i}"): st.session_state.current_q_idx = i; st.rerun()
                    st.markdown(f"<style>button[key='btn_{i}'] {{ background-color: {bg} !important; color: {'white' if bg!='#f8f9fa' else '#333'} !important; }}</style>", unsafe_allow_html=True)

    # --- 3. முடிவு பக்கம் ---
    elif st.session_state.page == 'result':
        df = st.session_state.filtered_df
        total = len(df)
        score = sum(1 for i in range(total) if str(st.session_state.user_answers.get(i)) == str(df.iloc[i]['Answer']))
        
        if not st.session_state.score_saved:
            # மதிப்பெண் சேமிப்பு முயற்சி
            success = save_score(st.session_state.user_name, st.session_state.selected_std, st.session_state.selected_subject, score, total)
            st.session_state.score_saved = True
            if success: st.success("மதிப்பெண் ஆசிரியருக்கு அனுப்பப்பட்டது! ✅")
            else: st.error("மதிப்பெண் சேமிக்கப்படவில்லை. Google Sheet தலைப்புகளைச் சரிபார்க்கவும்.")

        st.markdown(f'<div style="border:10px solid #1E88E5; padding:30px; text-align:center; background-color:white;"><h2>அரசு மேல்நிலைப்பள்ளி - தேவனாங்குறிச்சி</h2><hr><h1>மதிப்பெண்: {score} / {total}</h1></div>', unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3)
        with c1:
            if st.button("🔄 மீண்டும் பயிற்சி (அதே வினாக்கள்)"):
                st.session_state.user_answers = {}; st.session_state.visited = set(); st.session_state.marked = set()
                st.session_state.current_q_idx = 0; st.session_state.score_saved = False; st.session_state.page = 'quiz'; st.rerun()
        with col_c2 := c2:
            if st.button("🆕 புதிய வினாக்கள் (அடுத்த தொகுப்பு)"):
                st.session_state.page = 'login'; st.rerun()
        with c3:
            if st.button("🔍 மறுபார்வை"): st.session_state.page = 'review'; st.rerun()

    # --- 4. மறுபார்வை பக்கம் ---
    elif st.session_state.page == 'review':
        df = st.session_state.filtered_df
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
