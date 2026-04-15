import streamlit as st
import pandas as pd
from supabase import create_client, Client

# --- 1. SUPABASE CONNECTION ---
try:
    url: str = st.secrets["SUPABASE_URL"]
    key: str = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(url, key)
except Exception as e:
    st.error("Secrets விவரங்கள் சரியாக இல்லை! .streamlit/secrets.toml கோப்பைச் சரிபார்க்கவும்.")
    st.stop()

st.set_page_config(page_title="Staff Allotment", layout="wide", page_icon="📝")
st.title("👨‍🏫 ஆசிரியர் பாடவேளை ஒதுக்கீடு (Staff Allotment)")

# --- ⚡ FETCH DATA (Caching) ---

@st.cache_data(ttl=60)
def fetch_teachers():
    """ஆசிரியர்களின் சுருக்கப் பெயர்களை எடுக்க"""
    res = supabase.table("teachers").select("id, short_name").order("short_name").execute()
    return {t['short_name']: t['id'] for t in res.data}

@st.cache_data(ttl=60)
def fetch_subjects():
    """பாடங்கள் அட்டவணையில் இருந்து பாடப் பெயர்களை எடுக்க"""
    res = supabase.table("subjects").select("subject_name").order("subject_name").execute()
    return [s['subject_name'] for s in res.data]

@st.cache_data(ttl=60)
def fetch_all_classes():
    """தனி வகுப்புகள் மற்றும் கம்பைன் குரூப்களை இணைத்து எடுக்க"""
    # 1. Classes Table
    res_c = supabase.table("classes").select("class_name").order("class_name").execute()
    classes = [c['class_name'] for c in res_c.data]
    # 2. Combined Groups Table
    res_g = supabase.table("combined_groups").select("group_name").order("group_name").execute()
    groups = [g['group_name'] for g in res_g.data]
    return classes + groups

@st.cache_data(ttl=60)
def fetch_current_allotments():
    """தற்போதைய ஒதுக்கீடுகளை ஆசிரியர்களின் பெயருடன் இணைத்து எடுக்க"""
    res = supabase.table("staff_allotment").select("*, teachers(short_name)").execute()
    return res.data

# தரவுகளைத் தயார் செய்தல்
teachers_dict = fetch_teachers()
subjects_list = fetch_subjects()
final_classes_list = fetch_all_classes()

# --- 2. ஒதுக்கீடு படிவம் ---
with st.form("allotment_form", clear_on_submit=True):
    st.subheader("🆕 புதிய ஒதுக்கீட்டைச் சேர்க்க")
    
    col_t, col_c, col_s, col_p = st.columns([2, 2, 2, 1])
    
    with col_t:
        t_name = st.selectbox("ஆசிரியர்:", list(teachers_dict.keys()) if teachers_dict else ["No Teachers Found"])
    with col_c:
        c_name = st.selectbox("வகுப்பு / கம்பைன் குழு:", final_classes_list if final_classes_list else ["No Classes Found"])
    with col_s:
        s_name = st.selectbox("பாடம்:", subjects_list if subjects_list else ["No Subjects Found"])
    with col_p:
        p_count = st.number_input("பாடவேளைகள்:", min_value=1, max_value=45, value=5)
    
    if st.form_submit_button("💾 ஒதுக்கீட்டைச் சேமி"):
        if teachers_dict and final_classes_list:
            try:
                supabase.table("staff_allotment").insert({
                    "teacher_id": teachers_dict[t_name],
                    "class_name": c_name,
                    "subject_name": s_name,
                    "periods_per_week": p_count
                }).execute()
                st.success(f"✅ வெற்றிகரமாகச் சேமிக்கப்பட்டது!")
                st.cache_data.clear()
                st.rerun()
            except Exception as e:
                st.error(f"பிழை: {e}")

st.divider()

# --- 3. பணிச்சுமை கணக்கீடு மற்றும் காட்சிப்படுத்துதல் ---
allotment_data = fetch_current_allotments()

if allotment_data:
    df = pd.DataFrame(allotment_data)
    # ஆசிரியரின் சுருக்கப் பெயரை மட்டும் பிரித்தெடுத்தல்
    df['ஆசிரியர்'] = df['teachers'].apply(lambda x: x['short_name'] if x else "N/A")
    
    tab1, tab2 = st.tabs(["📋 ஒதுக்கீடு பட்டியல்", "📊 மொத்த பணிச்சுமை (Total Workload)"])
    
    with tab1:
        st.subheader("அனைத்து ஒதுக்கீடுகள்")
        display_df = df[['ஆசிரியர்', 'class_name', 'subject_name', 'periods_per_week']]
        display_df.columns = ['ஆசிரியர்', 'வகுப்பு', 'பாடம்', '
