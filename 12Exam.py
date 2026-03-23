import streamlit as st
import pandas as pd
import random
from datetime import datetime

# 1. பக்க அமைப்பு
st.set_page_config(page_title="GHSS Devanankurichi - Advanced Exam Portal", layout="wide")

# --- CSS: மேம்படுத்தப்பட்ட வண்ணக் குறியீடுகள் ---
st.markdown("""
    <style>
    .school-header { text-align: center; background-color: #f0f7ff; padding: 20px; border-radius: 10px; border: 2px solid #1E88E5; margin-bottom: 20px; }
    .q-box { border: 1px solid #ddd; padding: 20px; border-radius: 10px; background: white; margin-bottom: 10px; }
    
    /* சான்றிதழ் வடிவமைப்பு */
    .cert-container {
        border: 15px double #1E88E5; padding: 30px; text-align: center; 
        background-color: white; color: #333; margin: 10px auto; max-width: 850px;
    }
    
    /* பொத்தான்கள் */
    div.stButton > button { width: 100% !important; border-radius: 5px !important; height: 50px !important; font-weight: bold !important; }
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
            st.subheader("📝 மாணவர் லாகின்")
            name = st.text_input("மாணவர் பெயர்:")
            
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
                
                max_q = len(final_df)
                num_q = st.number_input(f"வினாக்கள் எண்ணிக்கை:", 1, max_q, min(25, max_q))

                if st.button("தேர்வைத் தொடங்கு ➡️", type="primary"):
                    if name:
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
            st.markdown(f'<div class="q-box"><b>வினா {q_idx + 1} / {len(df)}</b><br><h3>{row["Question Text"]}</h3></div>', unsafe_allow_html=True)
            
            opts = [str(row['Ans-1']), str(row['Ans-2']), str(row['Ans-3']), str(row['Ans-4'])]
            if f"opts_{q_idx}" not in st.session_state:
                random.shuffle(opts)
                st.session_state[f"opts_{q_idx}"] = opts
            
            current_ans = st.session_state.user_answers.get(q_idx)
            ans = st.radio("விடை:", st.session_state[f"opts_{q_idx}"], key=f"r_{q_idx}", 
                           index=st.session_state[f"opts_{q_idx}"].index(current_ans) if current_ans in st.session_state[f"opts_{q_idx}"] else None)
            if ans: st.session_state.user_answers[q_idx] = ans

            st.checkbox("🚩 இந்த வினாவில் சந்தேகம் உள்ளது", value=(q_idx in st.session_state.marked), key=f"m_{q_idx}", 
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
                # வண்ணத் தர்க்கம்
                label = f"{i+1}"
                bg = "#f8f9fa"; txt = "#333"
                
                is_marked = i in st.session_state.marked
                is_answered = i in st.session_state.user_answers
                
                if is_marked and is_answered:
                    label = f"💜 🚩 {i+1}"; bg = "#673AB7"; txt = "white" # விடையளித்த சந்தேகம்
                elif is_marked:
                    label = f"🟠 🚩 {i+1}"; bg = "#FF9800"; txt = "white" # விடையளிக்காத சந்தேகம்
                elif is_answered:
                    label = f"✅ {i+1}"; bg = "#28a745"; txt = "white" # விடையளித்தது
                elif i in st.session_state.visited:
                    label = f"👁️ {i+1}"; bg = "#2196F3"; txt = "white" # பார்த்தது
                else:
                    label = f"⬜ {i+1}"

                with grid[i % 3]:
                    if st.button(label, key=f"btn_{i}"):
                        st.session_state.current_q_idx = i; st.rerun()
                    st.markdown(f"<style>button[key='btn_{i}'] {{ background-color: {bg} !important; color: {txt} !important; border: {'3px solid black' if i==q_idx else '1px solid #ccc'} !important; }}</style>", unsafe_allow_html=True)

    # --- 3. முடிவு & மறுபார்வை ---
    elif st.session_state.page == 'result':
        df = st.session_state.filtered_df
        score = sum(1 for i in range(len(df)) if str(st.session_state.user_answers.get(i)) == str(df.iloc[i]['Answer']))
        st.balloons()
        
        st.markdown(f"""
        <div class="cert-container">
            <p style="font-size:2rem; color:#1E88E5; font-weight:bold;">அரசு மேல்நிலைப்பள்ளி - தேவனாங்குறிச்சி</p>
            <p>நாமக்கல் மாவட்டம்</p><hr>
            <p style="font-size:1.4rem;">மாணவர் <b>{st.session_state.user_name}</b> பெற்ற மதிப்பெண்கள்</p>
            <h1 style="font-size:4rem; color:#d32f2f;">{score} / {len(df)}</h1>
            <p><i>"வெள்ளத் தனைய மலர்நீட்டம் மாந்தர்தம் உள்ளத் தனையது உயர்வு"</i></p>
        </div>
        """, unsafe_allow_html=True)

        st.subheader("🔍 மறுபார்வை")
        for i in range(len(df)):
            u = st.session_state.user_answers.get(i, "பதிலளிக்கவில்லை")
            c = str(df.iloc[i]['Answer'])
            is_c = (str(u) == c)
            clr = "#28a745" if is_c else "#dc3545"
            bgc = "#f4fff6" if is_c else "#fff5f5"
            
            st.markdown(f"""<div style="padding:15px; border-radius:10px; margin-bottom:10px; border-left:8px solid {clr}; background-color:{bgc};">
                <b>வினா {i+1}:</b> {df.iloc[i]['Question Text']}<br>
                உங்கள் விடை: <span style="color:{clr}">{u}</span><br>
                {"" if is_c else f"<span style='color:#28a745'>சரியான விடை: {c}</span>"}
            </div>""", unsafe_allow_html=True)
        if st.button("🔄 மீண்டும் எழுத"): st.session_state.clear(); st.rerun()

except Exception as e: st.error(f"Error: {e}")
