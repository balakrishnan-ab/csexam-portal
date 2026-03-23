import streamlit as st
import pandas as pd
import random
from datetime import datetime

# 1. பக்க அமைப்பு
st.set_page_config(page_title="GHSS Devanankurichi - Custom Exam", layout="wide")

# --- CSS: நேர்த்தியான வடிவமைப்பு ---
st.markdown("""
    <style>
    .block-container { padding-top: 2rem !important; }
    .school-header { text-align: center; background-color: #f0f7ff; padding: 25px; border-radius: 15px; border: 2px solid #1E88E5; margin-bottom: 20px; }
    .school-name { color: #0D47A1; font-size: 2.5rem !important; font-weight: bold; margin: 0; }
    div.stButton > button { width: 100% !important; height: 50px !important; font-weight: bold !important; }
    .certificate-border { border: 15px double #1E88E5; padding: 40px; text-align: center; background: #fff; margin: 20px auto; max-width: 800px; }
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
if 'filtered_df' not in st.session_state: st.session_state.filtered_df = None
if 'current_q_idx' not in st.session_state: st.session_state.current_q_idx = 0

try:
    df_raw = get_data(SHEET_URL)
    
    # --- 1. லாகின் & டைனமிக் வடிகட்டுதல் ---
    if st.session_state.page == 'login':
        st.markdown("<h1 style='text-align:center;'>அரசு மேல்நிலைப்பள்ளி தேவனாங்குறிச்சி</h1>", unsafe_allow_html=True)
        st.divider()
        
        col1, col2, col3 = st.columns([1,2,1])
        with col2:
            st.subheader("🎓 தேர்வு அமைப்புகள்")
            name = st.text_input("மாணவர் பெயர்:", placeholder="உங்கள் பெயரை உள்ளிடவும்")
            
            if not df_raw.empty:
                # CSV-ல் உள்ள தரவுகளை மட்டும் கொண்டு பட்டியலை உருவாக்குதல்
                
                # 1. பயிற்று மொழி (Medium) - CSV-ல் இருந்தால்
                if 'Medium' in df_raw.columns:
                    available_mediums = sorted(df_raw['Medium'].unique().tolist())
                    selected_medium = st.selectbox("பயிற்று மொழி (Medium) தேர்ந்தெடுக்கவும்:", available_mediums)
                    df_med = df_raw[df_raw['Medium'] == selected_medium]
                else:
                    selected_medium = "தமிழ்" # Default
                    df_med = df_raw

                # 2. பாடம் (Subject) - CSV-ல் உள்ளவை மட்டும்
                available_subjects = sorted(df_med['Subject Code'].unique().tolist())
                selected_sub = st.selectbox("பாடம் (Subject) தேர்ந்தெடுக்கவும்:", available_subjects)
                df_sub = df_med[df_med['Subject Code'] == selected_sub]
                
                # 3. அலகு (Units) - அந்தப் பாடத்தில் உள்ளவை மட்டும்
                available_units = sorted(df_sub['Lesson Code'].unique().tolist())
                selected_units = st.multiselect("அலகு (Unit) - (ஏதும் இல்லை எனில் அனைத்தும்):", available_units)
                
                # இறுதி வடிகட்டுதல்
                final_filtered = df_sub.copy()
                if selected_units:
                    final_filtered = final_filtered[final_filtered['Lesson Code'].isin(selected_units)]
                
                max_avail = len(final_filtered)
                num_q = st.number_input(f"வினாக்களின் எண்ணிக்கை (கிடைப்பவை: {max_avail}):", min_value=1, max_value=max_avail, value=min(25, max_avail))
                
                if st.button("தேர்வைத் தொடங்கு ➡️", type="primary"):
                    if name and max_avail > 0:
                        st.session_state.user_name = name
                        st.session_state.selected_subject = selected_sub
                        
                        # வினாக்களைத் தேர்ந்தெடுத்தல்
                        indices = list(range(max_avail))
                        random.shuffle(indices)
                        st.session_state.filtered_df = final_filtered.iloc[indices[:num_q]].reset_index(drop=True)
                        
                        st.session_state.current_q_idx = 0
                        st.session_state.page = 'quiz'
                        st.rerun()
                    elif max_avail == 0:
                        st.error("தேர்வு செய்த பாடத்தில் வினாக்கள் இல்லை!")
                    else: st.error("பெயரை உள்ளிடவும்!")

    # --- 2. வினாடி வினா பக்கம் ---
    elif st.session_state.page == 'quiz':
        df = st.session_state.filtered_df
        q_ptr = st.session_state.current_q_idx
        row = df.iloc[q_ptr]
        st.session_state.visited.add(q_ptr)
        
        st.markdown(f"""
        <div class="school-header">
            <span class="school-name">அரசு மேல்நிலைப்பள்ளி தேவனாங்குறிச்சி</span>
            <div style="margin-top:10px; font-weight:bold; color:#1E88E5;">
                வினா {q_ptr + 1} / {len(df)} | {st.session_state.selected_subject}
            </div>
        </div>
        """, unsafe_allow_html=True)

        # வினா மற்றும் விடைகள் (முந்தைய அதே நேர்த்தியான அமைப்பு)
        st.write(f"### {row['Question Text']}")
        opts = [str(row['Ans-1']), str(row['Ans-2']), str(row['Ans-3']), str(row['Ans-4'])]
        if f"opts_{q_ptr}" not in st.session_state:
            random.shuffle(opts)
            st.session_state[f"opts_{q_ptr}"] = opts
        
        ans = st.radio("விடை:", st.session_state[f"opts_{q_ptr}"], key=f"r_{q_ptr}", 
                       index=st.session_state[f"opts_{q_ptr}"].index(st.session_state.user_answers[q_ptr]) if q_ptr in st.session_state.user_answers else None)
        if ans: st.session_state.user_answers[q_ptr] = ans

        st.divider()
        c1, c2 = st.columns(2)
        with c1:
            if q_ptr > 0 and st.button("⬅️ முந்தைய"): st.session_state.current_q_idx -= 1; st.rerun()
        with c2:
            if q_ptr < len(df) - 1:
                if st.button("அடுத்தது ➡️"): st.session_state.current_q_idx += 1; st.rerun()
            else:
                if st.button("தேர்வை முடிக்க 🏁", type="primary"): st.session_state.page = 'evaluate'; st.rerun()

    # --- 3. மதிப்பீடு & சான்றிதழ் ---
    elif st.session_state.page == 'evaluate':
        df = st.session_state.filtered_df
        score = 0
        for i in range(len(df)):
            if str(st.session_state.user_answers.get(i)) == str(df.iloc[i]['Answer']): score += 1
        
        st.balloons()
        now = datetime.now().strftime("%d-%m-%Y %I:%M %p")
        st.markdown(f"""
        <div class="certificate-border">
            <h1 style="color:#1E88E5;">அரசு மேல்நிலைப்பள்ளி - தேவனாங்குறிச்சி</h1>
            <p>நாமக்கல் மாவட்டம்</p><hr>
            <p style="font-size:1.4rem;">மாணவர் <b>{st.session_state.user_name}</b> அவர்கள் இப்பள்ளியில்</p>
            <p style="font-size:1.5rem; color:#d32f2f; font-weight:bold;">{st.session_state.selected_subject}</p>
            <p style="font-size:1.2rem;">தேர்வு எழுதி பெற்ற மதிப்பெண்கள்</p>
            <div style="font-size:3.5rem; font-weight:bold; color:#1E88E5;">{score} / {len(df)}</div>
            <p>நாள்: {now}</p>
            <p><i>"வெள்ளத் தனைய மலர்நீட்டம் மாந்தர்தம் உள்ளத் தனையது உயர்வு"</i></p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("🔄 புதிய தேர்வு எழுத"): st.session_state.clear(); st.rerun()

except Exception as e: st.error(f"பிழை: {e}")
