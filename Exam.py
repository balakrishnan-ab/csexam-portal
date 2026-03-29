import streamlit as st
import pandas as pd
import random
import requests
from datetime import datetime

# 1. பக்க அமைப்பு
st.set_page_config(page_title="GHSS Devanankurichi - Pro Exam Portal", layout="wide")

# --- CSS வடிவமைப்பு: அனிமேஷன் மற்றும் பலகம் ---
st.markdown("""
    <style>
    .school-header { text-align: center; background-color: #f0f7ff; padding: 15px; border-radius: 12px; border: 2px solid #1E88E5; margin-bottom: 20px; }
    .school-name { color: #0D47A1; font-size: 2.2rem !important; font-weight: bold; margin: 0; }
    .q-box { border: 1px solid #ddd; padding: 20px; border-radius: 10px; background: white; margin-bottom: 10px; }
    .option-box { padding: 12px; border-radius: 8px; margin: 6px 0; border: 1px solid #ddd; }
    .opt-correct { background-color: #d4edda; border-left: 10px solid #28a745; font-weight: bold; }
    .opt-wrong { background-color: #f8d7da; border-left: 10px solid #dc3545; font-weight: bold; }
    .kural-box { background-color: #fff9c4; padding: 15px; border-radius: 10px; border-left: 5px solid #fbc02d; font-style: italic; margin-top: 10px; text-align: center; }
    
    /* வினா பலக பொத்தான்கள் */
    div[data-testid="stColumn"] button {
        padding: 2px !important; height: 48px !important; width: 100% !important;
        font-size: 0.8rem !important; font-weight: bold !important; border-radius: 8px !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. தரவுத்தள செயல்பாடுகள் ---

def get_attempt_count(name, subject):
    # SheetDB API மூலம் தேடுதல் (Case Sensitive சரிபார்க்கப்பட்டது)
    API_URL = f"https://sheetdb.io/api/v1/w7ktpqhwxaiy9/search?Name={name}&Subject={subject}"
    try:
        response = requests.get(API_URL, timeout=5)
        if response.status_code == 200:
            past_data = response.json()
            return len(past_data) + 1
        return 1
    except: return 1

def save_score(name, std, subject, correct, total, attempted, attempt_no):
    API_URL = "https://sheetdb.io/api/v1/w7ktpqhwxaiy9" 
    payload = {
        "data": [{
            "Name": str(name), "Standard": str(std), "Datetime": datetime.now().strftime("%d-%m-%Y %H:%M"),
            "Subject": str(subject), "Total qus": str(total), "Attan": str(attempted),
            "Correct": str(correct), "Wrong": str(attempted - correct), 
            "Score": f"{(correct/total)*100:.1f}%", "Attempt_No": str(attempt_no)
        }]
    }
    try:
        requests.post(API_URL, json=payload, timeout=10)
        return True
    except: return False

@st.cache_data(ttl=60)
def get_data(url):
    try:
        data = pd.read_csv(url)
        data.columns = data.columns.str.strip()
        return data.dropna(subset=['Question Text'])
    except: return pd.DataFrame()

# திருக்குறள் பட்டியல்
KURALS = [
    "தொட்டனைத் தூறும் மணற்கேணி மாந்தர்க்குக்<br>கற்றனைத் தூறும் அறிவு.",
    "கற்க கசடறக் கற்பவை கற்றபின்<br>நிற்க அதற்குத் தக.",
    "எண்ணென்ப ஏனை எழுத்தென்ப இவ்விரண்டும்<br>கண்ணென்ப வாழும் உயிர்க்கு.",
    "கேடில் விழுச்செல்வம் கல்வி ஒருவற்கு<br>மாடல்ல மற்றை யவை.",
    "எப்பொருள் யார்யார்வாய்க் கேட்பினும் அப்பொருள்<br>மெய்ப்பொருள் காண்ப தறிவு."
]

SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSQwApSEm-2EfhP7PVMuZVBUcrD0XGr3tMXMTpX2j-9m5gB3xPgECBEsXjqTtBmW7lnFcrIVuOycN7V/pub?output=csv"

# --- 3. செஷன் ஸ்டேட் ---
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
                
                l_col = 'Lesson Code' if 'Lesson Code' in df_sub.columns else 'Lesson'
                l_list = sorted(df_sub[l_col].unique().tolist()) if l_col in df_sub.columns else []
                sel_l = st.multiselect("அலகுகள் (Lessons):", l_list)
                pool = df_sub[df_sub[l_col].isin(sel_l)] if sel_l else df_sub
                
                rem = [idx for idx in pool.index if idx not in st.session_state.seen_ids]
                if not rem: st.session_state.seen_ids = set(); rem = list(pool.index)
                num_q = st.number_input(f"வினாக்கள் எண்ணிக்கை:", 1, len(rem), min(len(rem), 25))
                
                if st.button("தேர்வைத் தொடங்கு ➡️", type="primary") and u_name:
                    st.session_state.attempt_no = get_attempt_count(u_name, sel_sub)
                    st.session_state.user_name = u_name
                    st.session_state.selected_std, st.session_state.selected_subject = sel_std, sel_sub
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
                is_m, is_a, is_v = i in st.session_state.marked, i in st.session_state.user_answers, i in st.session_state.visited
                if is_m and is_a: lbl, bg, txt = f"💜🚩{i+1}", "#673AB7", "white"
                elif is_m: lbl, bg, txt = f"🟠🚩{i+1}", "#FF9800", "white"
                elif is_a: lbl, bg, txt = f"✅{i+1}", "#28A745", "white"
                elif is_v: lbl, bg, txt = f"🔵{i+1}", "#2196F3", "white"
                else: lbl, bg, txt = f"{i+1}", "#F8F9FA", "#333"
                with grid[i % 5]:
                    if st.button(lbl, key=f"btn_{i}"): st.session_state.current_q_idx = i; st.rerun()
                    st.markdown(f"<style>button[key='btn_{i}'] {{ background-color: {bg} !important; color: {txt} !important; border: {'2px solid black' if i==q_idx else '1px solid #CCC'} !important; }}</style>", unsafe_allow_html=True)

    elif st.session_state.page == 'result':
        df, total = st.session_state.filtered_df, len(st.session_state.filtered_df)
        score = sum(1 for i in range(total) if str(st.session_state.user_answers.get(i)) == str(df.iloc[i]['Answer']))
        perc = (score / total) * 100
        
        if not st.session_state.score_saved:
            save_score(st.session_state.user_name, st.session_state.selected_std, st.session_state.selected_subject, score, total, len(st.session_state.user_answers), st.session_state.attempt_no)
            st.session_state.score_saved = True

        st.markdown(f'<div style="border:10px solid #1E88E5; padding:30px; text-align:center; background-color:white;"><h2>அரசு மேல்நிலைப்பள்ளி - தேவனாங்குறிச்சி</h2><hr><h1>சரியானவை: {score} / {total} ({perc:.1f}%)</h1></div>', unsafe_allow_html=True)
        
        # --- அனிமேஷன் மற்றும் பாராட்டு ---
        if perc >= 80:
            st.balloons(); st.snow(); st.success("🌟 அருமை! (Excellent)"); st.markdown("🎈🌸🎈🌸🎈")
        elif perc >= 60:
            st.snow(); st.info("🌸 சிறப்பு! (Very Good)"); st.markdown("🌸🌸🌸")
        elif perc >= 50:
            st.warning("🦋 நன்று! (Good)"); st.markdown("🦋🦋🦋")
        else:
            st.error("🔥 முயற்சி செய்! (Try Harder)"); st.markdown("🔥🔥🔥")

        # திருக்குறள் சான்றிதழ் பகுதி
        st.markdown(f'<div class="kural-box"><b>திருக்குறள்:</b><br>{random.choice(KURALS)}</div>', unsafe_allow_html=True)
        
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
        l_col = 'Lesson Code' if 'Lesson Code' in df.columns else 'Lesson'
        for i in range(len(df)):
            row = df.iloc[i]; u_ans = st.session_state.user_answers.get(i); c_ans = str(row['Answer'])
            st.markdown(f"**வினா {i+1}:** <span class='lesson-tag'>அலகு: {row[l_col] if l_col in df.columns else 'N/A'}</span>", unsafe_allow_html=True)
            st.markdown(f"**{row['Question Text']}**")
            for j in range(1, 5):
                opt = str(row[f'Ans-{j}']); css = "option-box"
                if opt == c_ans: css += " opt-correct"
                elif u_ans is not None and opt == str(u_ans) and str(u_ans) != c_ans: css += " opt-wrong"
                st.markdown(f'<div class="{css}">{opt}</div>', unsafe_allow_html=True)
            st.divider()
        if st.button("⬅️ திரும்பு"): st.session_state.page = 'result'; st.rerun()

except Exception as e: st.error(f"பிழை: {e}")
