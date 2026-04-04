import streamlit as st
import pandas as pd
from supabase import create_client

# --- Supabase இணைப்பு ---
def get_supabase_client():
    if "supabase_instance" not in st.session_state:
        st.session_state.supabase_instance = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
    return st.session_state.supabase_instance

supabase = get_supabase_client()

st.set_page_config(page_title="Result Analysis", layout="wide")

st.markdown("""
    <style>
    .stDataFrame td { font-weight: bold !important; font-size: 16px !important; }
    .centum-card { background-color: #fef3c7; border-left: 5px solid #f59e0b; padding: 15px; border-radius: 8px; margin-bottom: 10px; }
    .stat-card { background-color: #ecfdf5; border-left: 5px solid #10b981; padding: 15px; border-radius: 8px; margin-bottom: 10px; font-weight: bold; }
    .fail-detail { color: #b91c1c; font-size: 14px; font-weight: normal; }
    </style>
    """, unsafe_allow_html=True)

st.title("📊 வகுப்பு வாரி விரிவான தேர்ச்சிப் பகுப்பாய்வு")

# --- 1. தரவுகள் ---
exams_data =
