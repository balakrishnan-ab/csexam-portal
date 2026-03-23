import streamlit as st
import pandas as pd
import random
from datetime import datetime

# 1. பக்க அமைப்பு
st.set_page_config(page_title="GHSS Devanankurichi - Exam Portal", layout="wide")

# --- CSS: மறுபார்வை மற்றும் வடிவமைப்பு ---
st.markdown("""
    <style>
    .school-header { text-align: center; background-color: #f0f7ff; padding: 20px; border-radius: 12px; border: 2px solid #1E88E5; margin-bottom: 20px; }
    .q-box { border: 1px solid #ddd; padding: 20px; border-radius: 10px; background: white; margin-bottom: 10px; }
    
    /* மறுபார்வை அட்டைகள் - பிழை வராமல் இருக்க */
    .review-card {
        padding: 15px; 
        border-radius: 10px; 
        margin-bottom: 12px; 
        border-left: 10px solid;
        line-height: 1.6;
    }
    .correct-card { border-left-color: #28a745; background-color: #f4fff6; }
    .wrong-card { border-left-color: #dc3545; background-color: #fff5f5; }

    div.stButton > button { width: 100% !important; border-radius: 8px !important; height: 50px !important; font-weight: bold !important; }
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

# செஷன் ஸ்டேட் மேலாண்மை
if 'page' not in st.session_state: st.session_state.page = 'login'
if 'user_answers' not in st.session_state: st.session_state.user_answers = {}
if 'visited' not in st.session_state: st.session_state.visited = set()
if 'marked' not in st.session_state: st.session_state.marked = set()
if 'current_q_idx' not in st.session_state: st.session_state.current_q_idx = 0
if 'options_map' not in st.session_state: st.session_state.options_map = {}

try:
    df_raw = get_data(SHEET_URL)

    # --- 1. லாகின் பக்கம் ---
    if st.session_state.page == 'login':
        st.markdown("<h1 style='text-align:center;'>அரசு மேல்நிலைப்பள்ளி தேவனாங்குறிச்சி</h1>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1,2,1])
        with col2:
            st.subheader("🎓 தேர்வு அமைப்புகள்")
            name = st.text_input("மாணவர் பெயர்:", value=st.session_state.get('user_name', ''))
            
            if not df_raw.empty:
                med_list = sorted(df_raw['Medium'].unique().tolist()) if 'Medium' in df_raw.columns else ["தமிழ்", "English"]
                sel_med = st.selectbox("பயிற்று மொழி:", med_list)
                
                df_f = df_raw[df_raw['Medium'] == sel_med] if 'Medium' in df_raw.columns else df_raw
                sub_list = sorted(df_f['Subject Code'].unique().tolist())
                sel_sub = st.selectbox("பாடம்:", sub_list)
                
                df_sub = df_f[df_f['Subject Code'] == sel_sub]
                unit_list = sorted(df_sub['Lesson Code'].unique().tolist())
                sel_units = st.multiselect("அலகுகள்:", unit_list)
                
                final_df = df_sub.copy()
                if sel_units: final_df = final_df[final_df['Lesson Code'].isin(sel_units)]
                
                num_q = st.number_input(f"வினாக்கள் எண்ணிக்கை (Max: {len(final_df)}):", 1, len(final_df), min(25, len(final_df)))

                if st.button("தேர்வைத் தொடங்கு ➡️", type="primary") and name:
                    st.session_state.user_name = name
                    st.session_state.selected_subject = sel_sub
                    
                    # வினாக்களைத் தேர்ந்தெடுத்தல்
                    indices = list(range(len(final_df)))
                    random.shuffle(indices)
                    st.session_state.filtered_df = final_df.iloc[indices[:num_q]].reset_index(drop=True)
                    
                    # விடைகளைத் தயார் செய்தல்
                    st.session_state.options_map = {}
                    for i in range(len(st.session_state.filtered_df)):
                        row = st.session_state.filtered_df.iloc[i]
                        opts = [str(row['Ans-1']), str(row['Ans-2']), str(row['Ans-3']), str(row['Ans-4'])]
                        random.shuffle(opts)
                        st.session_state.options_map[i] = opts
                    
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
            st.markdown(f'<div class="q-box"><b>வினா {q_idx + 1} / {len(df)}</b><br><h3>{row["Question Text"]}</h3></div>', unsafe_allow_html=True)
            
            opts = st.session_state.options_map[q_idx]
            current_ans = st.session_state.user_answers.get(q_idx)
            ans = st.radio("விடை:", opts, key=f"r_{q_idx}", 
                           index=opts.index(current_ans) if current_ans in opts else None)
            
            if ans: st.session_state.user_answers[q_idx] = ans
            st.checkbox("🚩 சந்தேகம் (Mark for Review)", value=(q_idx in st.session_state.marked), key=f"m_{q_idx}", 
                        on_change=lambda: st.session_state.marked.add(q_idx) if st.session_state[f"m_{q_idx}"] else st.session_state.marked.discard(q_idx))

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
                label = f"{i+1}"
                is_marked = i in st.session_state.marked
                is_answered = i in st.session_state.user_answers
                
                # வண்ணக் குறியீடுகள்
                bg = "#f8f9fa"; txt = "#333"
                if is_marked and is_answered: label = f"💜 🚩 {i+1}"; bg = "#673AB7"; txt = "white"
                elif is_marked: label = f"🟠 🚩 {i+1}"; bg = "#FF9800"; txt = "white"
                elif is_answered: label = f"✅ {i+1}"; bg = "#28a745"; txt = "white"
                elif i in st.session_state.visited: label = f"👁️ {i+1}"; bg = "#2196F3"; txt = "white"
                else: label = f"⬜ {i+1}"

                with grid[i % 3]:
                    if st.button(label, key=f"btn_{i}"): st.session_state.current_q_idx = i; st.rerun()
                    st.markdown(f"<style>button[key='btn_{i}'] {{ background-color: {bg} !important; color: {txt} !important; border: {'3px solid black' if i==q_idx else '1px solid #ccc'} !important; }}</style>", unsafe_allow_html=True)

    # --- 3. முடிவு பக்கம் ---
    elif st.session_state.page == 'result':
        df = st.session_state.filtered_df
        score = sum(1 for i in range(len(df)) if str(st.session_state.user_answers.get(i)) == str(df.iloc[i]['Answer']))
        st.balloons()
        
        st.markdown(f"""
        <div style="border:12px double #1E88E5; padding:30px; text-align:center; background-color: white;">
            <h2>அரசு மேல்நிலைப்பள்ளி - தேவனாங்குறிச்சி</h2>
            <hr><p>மாணவர் <b>{st.session_state.user_name}</b></p>
            <h1 style="font-size:3.5rem; color:#d32f2f;">{score} / {len(df)}</h1>
            <p><i>"வெள்ளத் தனைய மலர்நீட்டம் மாந்தர்தம் உள்ளத் தனையது உயர்வு"</i></p>
        </div>
        """, unsafe_allow_html=True)

        st.divider()
        c1, c2, c3 = st.columns(3)
        with c1:
            if st.button("🔄 அதே வினாக்களை மீண்டும் எழுத"):
                st.session_state.user_answers = {}; st.session_state.visited = set(); st.session_state.marked = set()
                st.session_state.current_q_idx = 0
                st.session_state.filtered_df = st.session_state.filtered_df.sample(frac=1).reset_index(drop=True)
                st.session_state.options_map = {}
                for i in range(len(st.session_state.filtered_df)):
                    row = st.session_state.filtered_df.iloc[i]; opts = [str(row['Ans-1']), str(row['Ans-2']), str(row['Ans-3']), str(row['Ans-4'])]
                    random.shuffle(opts); st.session_state.options_map[i] = opts
                st.session_state.page = 'quiz'; st.rerun()
        with c2:
            if st.button("🆕 புதிய தேர்வு"):
                uname = st.session_state.user_name; st.session_state.clear(); st.session_state.user_name = uname; st.session_state.page = 'login'; st.rerun()
        with c3:
            if st.button("🔍 மறுபார்வை"): st.session_state.page = 'review'; st.rerun()

    # --- 4. மறுபார்வை பக்கம் (பிழை சரிசெய்யப்பட்டது) ---
    elif st.session_state.page == 'review':
        df = st.session_state.filtered_df
        st.markdown("### 🔍 வினா வாரியான மறுபார்வை")
        
        for i in range(len(df)):
            u = st.session_state.user_answers.get(i, "பதிலளிக்கவில்லை")
            c = str(df.iloc[i]['Answer'])
            is_c = (str(u) == c)
            
            # வினா அட்டை (Review Card)
            card_class = "correct-card" if is_c else "wrong-card"
            color_text = "#28a745" if is_c else "#dc3545"
            
            # HTML-ல் எந்த பிழையும் வராதவாறு சுத்தமான குறியீடு
            st.markdown(f"""
            <div class="review-card {card_class}">
                <b>வினா {i+1}:</b> {df.iloc[i]['Question Text']}<br>
                உங்கள் விடை: <span style="color:{color_text}; font-weight:bold;">{u}</span><br>
                {"" if is_c else f"<span style='color:#28a745; font-weight:bold;'>சரியான விடை: {c}</span>"}
            </div>
            """, unsafe_allow_html=True)
            
        if st.button("⬅️ முடிவுகளுக்குச் செல்ல"): st.session_state.page = 'result'; st.rerun()

except Exception as e: st.error(f"பி
