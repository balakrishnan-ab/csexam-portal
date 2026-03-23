import streamlit as st
import pandas as pd
import random
from datetime import datetime

# 1. பக்க அமைப்பு
st.set_page_config(page_title="GHSS Devanankurichi - Exam Review", layout="wide")

# --- CSS: நேர்த்தியான மறுபார்வை அட்டைகள் ---
st.markdown("""
    <style>
    .school-header { text-align: center; background-color: #f0f7ff; padding: 20px; border-radius: 10px; border: 2px solid #1E88E5; margin-bottom: 20px; }
    
    /* மறுபார்வை அட்டைகள் (Review Cards) */
    .review-card {
        padding: 20px; border-radius: 10px; margin-bottom: 15px; border-left: 10px solid;
        background-color: #fdfdfd; box-shadow: 2px 2px 5px rgba(0,0,0,0.05);
    }
    .correct-card { border-left-color: #28a745; background-color: #f4fff6; }
    .wrong-card { border-left-color: #dc3545; background-color: #fff5f5; }
    
    .status-badge { padding: 3px 10px; border-radius: 5px; font-weight: bold; color: white; margin-bottom: 10px; display: inline-block; }
    .bg-correct { background-color: #28a745; }
    .bg-wrong { background-color: #dc3545; }

    /* வினா பலகம் பொத்தான்கள் */
    div.stButton > button { width: 100% !important; font-weight: bold !important; }
    .certificate-border { border: 10px double #1E88E5; padding: 30px; text-align: center; background: #fff; margin-bottom: 20px; }
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
if 'current_q_idx' not in st.session_state: st.session_state.current_q_idx = 0

try:
    df_raw = get_data(SHEET_URL)

    # --- 1. லாகின் பக்கம் ---
    if st.session_state.page == 'login':
        st.markdown("<h1 style='text-align:center;'>அரசு மேல்நிலைப்பள்ளி தேவனாங்குறிச்சி</h1>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1,2,1])
        with col2:
            st.subheader("📝 தேர்வு விவரம்")
            name = st.text_input("மாணவர் பெயர்:")
            
            if not df_raw.empty:
                available_subs = sorted(df_raw['Subject Code'].unique().tolist())
                sel_sub = st.selectbox("பாடம் தேர்வு செய்க:", available_subs)
                
                df_sub = df_raw[df_raw['Subject Code'] == sel_sub]
                available_units = sorted(df_sub['Lesson Code'].unique().tolist())
                sel_units = st.multiselect("அலகுகள்:", available_units)
                
                final_df = df_sub.copy()
                if sel_units: final_df = final_df[final_df['Lesson Code'].isin(sel_units)]
                
                max_q = len(final_df)
                num_q = st.number_input(f"வினாக்களின் எண்ணிக்கை (அதிகபட்சம் {max_q}):", 1, max_q, min(10, max_q))

                if st.button("தேர்வைத் தொடங்கு ➡️", type="primary") and name:
                    st.session_state.user_name = name
                    st.session_state.selected_subject = sel_sub
                    indices = list(range(len(final_df)))
                    random.shuffle(indices)
                    st.session_state.filtered_df = final_df.iloc[indices[:num_q]].reset_index(drop=True)
                    st.session_state.page = 'quiz'
                    st.rerun()

    # --- 2. வினாடி வினா பக்கம் ---
    elif st.session_state.page == 'quiz':
        df = st.session_state.filtered_df
        q_idx = st.session_state.current_q_idx
        row = df.iloc[q_idx]
        st.session_state.visited.add(q_idx)

        st.markdown(f'<div class="school-header"><h3>{st.session_state.selected_subject} - தேர்வு</h3></div>', unsafe_allow_html=True)

        m_col, n_col = st.columns([7, 3])
        with m_col:
            st.write(f"**வினா {q_idx + 1} / {len(df)}**")
            st.write(f"### {row['Question Text']}")
            
            opts = [str(row['Ans-1']), str(row['Ans-2']), str(row['Ans-3']), str(row['Ans-4'])]
            if f"opts_{q_idx}" not in st.session_state:
                random.shuffle(opts)
                st.session_state[f"opts_{q_idx}"] = opts
            
            user_ans = st.radio("விடையைத் தேர்ந்தெடுக்கவும்:", st.session_state[f"opts_{q_idx}"], 
                               key=f"ans_{q_idx}", 
                               index=st.session_state[f"opts_{q_idx}"].index(st.session_state.user_answers[q_idx]) if q_idx in st.session_state.user_answers else None)
            
            if user_ans: st.session_state.user_answers[q_idx] = user_ans
            st.checkbox("🚩 சந்தேகம் (Mark for Review)", value=(q_idx in st.session_state.marked), key=f"m_{q_idx}", on_change=lambda: st.session_state.marked.add(q_idx) if st.session_state[f"m_{q_idx}"] else st.session_state.marked.discard(q_idx))

            st.divider()
            b1, b2, b3 = st.columns([1,1,1])
            with b1:
                if q_idx > 0 and st.button("⬅️ முந்தைய"): st.session_state.current_q_idx -= 1; st.rerun()
            with b2:
                if q_idx < len(df)-1 and st.button("அடுத்தது ➡️"): st.session_state.current_q_idx += 1; st.rerun()
            with b3:
                if st.button("🏁 தேர்வை முடி", type="primary"): st.session_state.page = 'result'; st.rerun()

        with n_col:
            st.markdown("##### 🔢 வினா பலகம்")
            grid = st.columns(4)
            for i in range(len(df)):
                bg = "#eee"; txt = "black"
                if i in st.session_state.marked: bg = "#FF9800"; txt = "white"
                elif i in st.session_state.user_answers: bg = "#28a745"; txt = "white"
                elif i in st.session_state.visited: bg = "#2196F3"; txt = "white"
                
                with grid[i % 4]:
                    if st.button(f"{i+1}", key=f"nv_{i}"): st.session_state.current_q_idx = i; st.rerun()
                    st.markdown(f"<style>button[key='nv_{i}'] {{ background-color: {bg} !important; color: {txt} !important; border: {'2px solid red' if i==q_idx else '1px solid #ccc'} !important; }}</style>", unsafe_allow_html=True)

    # --- 3. முடிவு மற்றும் மறுபார்வை பக்கம் ---
    elif st.session_state.page == 'result':
        df = st.session_state.filtered_df
        score = 0
        results = []
        for i in range(len(df)):
            u_ans = st.session_state.user_answers.get(i, "பதிலளிக்கவில்லை")
            c_ans = str(df.iloc[i]['Answer'])
            is_correct = (str(u_ans) == c_ans)
            if is_correct: score += 1
            results.append({"q": df.iloc[i]['Question Text'], "u": u_ans, "c": c_ans, "is": is_correct})

        st.balloons()
        st.markdown(f"""<div class="certificate-border">
            <h2>அரசு மேல்நிலைப்பள்ளி தேவனாங்குறிச்சி</h2>
            <hr>
            <h4>மாணவர்: {st.session_state.user_name} | பாடம்: {st.session_state.selected_subject}</h4>
            <h1 style="color:#d32f2f;">{score} / {len(df)}</h1>
            <p>தேதி: {datetime.now().strftime('%d-%m-%Y')}</p>
        </div>""", unsafe_allow_html=True)

        st.subheader("🔍 வினா வாரியான மறுபார்வை (Detailed Review)")
        
        for i, res in enumerate(results):
            card_class = "correct-card" if res['is'] else "wrong-card"
            badge_text = "சரி ✅" if res['is'] else "தவறு ❌"
            badge_class = "bg-correct" if res['is'] else "bg-wrong"
            
            st.markdown(f"""
            <div class="review-card {card_class}">
                <div class="status-badge {badge_class}">{badge_text}</div>
                <p><b>வினா {i+1}:</b> {res['q']}</p>
                <p>உங்கள் விடை: <span style="color:{'#28a745' if res['is'] else '#dc3545'}">{res['u']}</span></p>
                {" " if res['is'] else f"<p style='color:#28a745'><b>சரியான விடை: {res['c']}</b></p>"}
            </div>
            """, unsafe_allow_html=True)

        if st.button("🔄 மீண்டும் தேர்வு எழுத"): st.session_state.clear(); st.rerun()

except Exception as e: st.error(f"Error: {e}")
