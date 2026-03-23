import streamlit as st
import pandas as pd
import random
from datetime import datetime

# 1. பக்க அமைப்பு
st.set_page_config(page_title="GHSS Devanankurichi - Pro Exam Portal", layout="wide")

# --- CSS: மேம்படுத்தப்பட்ட வண்ணக் குறியீடுகள் ---
st.markdown("""
    <style>
    .school-header { text-align: center; background-color: #f0f7ff; padding: 20px; border-radius: 10px; border: 2px solid #1E88E5; margin-bottom: 20px; }
    .q-box { border: 1px solid #ddd; padding: 20px; border-radius: 10px; background: white; margin-bottom: 10px; }
    
    /* வினா பலக பொத்தான்கள் பொதுவானவை */
    div.stButton > button { width: 100% !important; font-weight: bold !important; border-radius: 8px !important; transition: 0.3s; }
    
    /* சான்றிதழ் */
    .certificate-border { border: 10px double #1E88E5; padding: 30px; text-align: center; background: #fff; margin-bottom: 20px; }
    .review-card { padding: 15px; border-radius: 8px; margin-bottom: 10px; border-left: 8px solid; }
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
            st.subheader("📝 மாணவர் விவரம்")
            name = st.text_input("மாணவர் பெயர்:")
            
            if not df_raw.empty:
                # பயிற்று மொழி (Medium) - CSV-ல் 'Medium' காலம் இருந்தால் அதிலிருந்து எடுக்கும்
                if 'Medium' in df_raw.columns:
                    med_list = sorted(df_raw['Medium'].unique().tolist())
                else:
                    med_list = ["தமிழ்", "English"] # காலம் இல்லையெனில் மேனுவல்
                
                sel_med = st.selectbox("பயிற்று மொழி (Medium) தேர்ந்தெடுக்கவும்:", med_list)
                
                # பாடம் (Subject)
                df_filtered = df_raw.copy()
                if 'Medium' in df_raw.columns:
                    df_filtered = df_filtered[df_filtered['Medium'] == sel_med]
                
                sub_list = sorted(df_filtered['Subject Code'].unique().tolist())
                sel_sub = st.selectbox("பாடம் (Subject) தேர்ந்தெடுக்கவும்:", sub_list)
                
                df_sub = df_filtered[df_filtered['Subject Code'] == sel_sub]
                unit_list = sorted(df_sub['Lesson Code'].unique().tolist())
                sel_units = st.multiselect("அலகுகள் (விருப்பமானவை):", unit_list)
                
                final_df = df_sub.copy()
                if sel_units: final_df = final_df[final_df['Lesson Code'].isin(sel_units)]
                
                max_q = len(final_df)
                num_q = st.number_input(f"வினாக்கள் எண்ணிக்கை (அதிகபட்சம் {max_q}):", 1, max_q, min(15, max_q))

                if st.button("தேர்வைத் தொடங்கு ➡️", type="primary"):
                    if name:
                        st.session_state.user_name = name
                        st.session_state.selected_subject = sel_sub
                        indices = list(range(len(final_df)))
                        random.shuffle(indices)
                        st.session_state.filtered_df = final_df.iloc[indices[:num_q]].reset_index(drop=True)
                        st.session_state.page = 'quiz'
                        st.rerun()
                    else: st.error("பெயரை உள்ளிடவும்!")

    # --- 2. வினாடி வினா பக்கம் ---
    elif st.session_state.page == 'quiz':
        df = st.session_state.filtered_df
        q_idx = st.session_state.current_q_idx
        row = df.iloc[q_idx]
        st.session_state.visited.add(q_idx) # பார்த்த வினா

        st.markdown(f'<div class="school-header"><h3>{st.session_state.selected_subject} - தேர்வு</h3></div>', unsafe_allow_html=True)

        m_col, n_col = st.columns([7, 3])
        with m_col:
            st.markdown(f'<div class="q-box"><b>வினா {q_idx + 1} / {len(df)}</b><br><h3>{row["Question Text"]}</h3></div>', unsafe_allow_html=True)
            
            opts = [str(row['Ans-1']), str(row['Ans-2']), str(row['Ans-3']), str(row['Ans-4'])]
            if f"opts_{q_idx}" not in st.session_state:
                random.shuffle(opts)
                st.session_state[f"opts_{q_idx}"] = opts
            
            # விடை தேர்வு
            current_ans = st.session_state.user_answers.get(q_idx)
            ans = st.radio("சரியான விடை:", st.session_state[f"opts_{q_idx}"], key=f"r_{q_idx}", 
                           index=st.session_state[f"opts_{q_idx}"].index(current_ans) if current_ans in st.session_state[f"opts_{q_idx}"] else None)
            
            if ans: st.session_state.user_answers[q_idx] = ans

            # சந்தேகம் (Mark for Review)
            is_m = st.checkbox("🚩 சந்தேகம் (Mark for Review)", value=(q_idx in st.session_state.marked), key=f"m_{q_idx}")
            if is_m: st.session_state.marked.add(q_idx)
            else: st.session_state.marked.discard(q_idx)

            st.divider()
            b1, b2, b3 = st.columns(3)
            with b1:
                if q_idx > 0 and st.button("⬅️ முந்தைய"): st.session_state.current_q_idx -= 1; st.rerun()
            with b2:
                if q_idx < len(df)-1 and st.button("அடுத்தது ➡️"): st.session_state.current_q_idx += 1; st.rerun()
            with b3:
                if st.button("🏁 தேர்வை முடி", type="primary"): st.session_state.page = 'result'; st.rerun()

        with n_col:
            st.markdown("##### 🔢 வினா பலகம்")
            st.markdown("<small>🟢 விடை | 🔵 பார்த்தது | 🟠 சந்தேகம் | ⚪ பார்க்காதது</small>", unsafe_allow_html=True)
            grid = st.columns(4)
            for i in range(len(df)):
                # வண்ணத் தர்க்கம் (Priority: Marked > Answered > Visited)
                bg = "#f8f9fa" # Default (White)
                txt = "#333"
                
                if i in st.session_state.marked:
                    bg = "#FF9800"; txt = "white" # Orange
                elif i in st.session_state.user_answers:
                    bg = "#28a745"; txt = "white" # Green
                elif i in st.session_state.visited:
                    bg = "#2196F3"; txt = "white" # Blue
                
                # தற்போதைய வினா பார்டர்
                border = "2px solid #000" if i == q_idx else "1px solid #ccc"

                with grid[i % 4]:
                    if st.button(f"{i+1}", key=f"btn_{i}"):
                        st.session_state.current_q_idx = i
                        st.rerun()
                    # நேரடி CSS இன்ஜெக்ஷன் (வண்ணம் மாற இதுவே சிறந்த வழி)
                    st.markdown(f"""<style>button[key='btn_{i}'] {{ background-color: {bg} !important; color: {txt} !important; border: {border} !important; }}</style>""", unsafe_allow_html=True)

    # --- 3. முடிவு & மறுபார்வை ---
    elif st.session_state.page == 'result':
        df = st.session_state.filtered_df
        score = sum(1 for i in range(len(df)) if str(st.session_state.user_answers.get(i)) == str(df.iloc[i]['Answer']))
        st.balloons()
        st.markdown(f'<div class="certificate-border"><h2>அரசு மேல்நிலைப்பள்ளி தேவனாங்குறிச்சி</h2><hr><h4>மாணவர்: {st.session_state.user_name}</h4><h1>{score} / {len(df)}</h1></div>', unsafe_allow_html=True)
        
        st.subheader("🔍 வினா வாரியான மறுபார்வை")
        for i in range(len(df)):
            u = st.session_state.user_answers.get(i, "பதிலளிக்கவில்லை")
            c = str(df.iloc[i]['Answer'])
            is_c = (str(u) == c)
            
            bc = "border-left: 8px solid " + ("#28a745;" if is_c else "#dc3545;")
            bgc = "background-color: " + ("#f4fff6;" if is_c else "#fff5f5;")
            
            st.markdown(f"""<div class="review-card" style="{bc} {bgc}">
                <b>வினா {i+1}:</b> {df.iloc[i]['Question Text']}<br>
                உங்கள் விடை: <span style="color:{'green' if is_c else 'red'}">{u}</span><br>
                {"" if is_c else f"<span style='color:green'>சரியான விடை: {c}</span>"}
            </div>""", unsafe_allow_html=True)

        if st.button("🔄 மீண்டும் எழுத"): st.session_state.clear(); st.rerun()

except Exception as e: st.error(f"Error: {e}")
