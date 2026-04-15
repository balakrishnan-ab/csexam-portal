import streamlit as st
import pandas as pd
from supabase import create_client, Client

# --- 1. SUPABASE CONNECTION ---
try:
    url: str = st.secrets["SUPABASE_URL"]
    key: str = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(url, key)
except Exception as e:
    st.error("Secrets விவரங்கள் சரியாக இல்லை!")
    st.stop()

st.set_page_config(page_title="Staff Allotment", layout="wide", page_icon="📝")
st.title("👨‍🏫 ஆசிரியர் பாடவேளை ஒதுக்கீடு (Staff Allotment)")

# --- ⚡ FETCH DATA FROM YOUR TABLES ---

@st.cache_data(ttl=60)
def fetch_teachers_data():
    """teachers அட்டவணையில் இருந்து சுருக்கப் பெயரை எடுக்க"""
    try:
        res = supabase.table("teachers").select("id, short_name").order("short_name").execute()
        return {t['short_name']: t['id'] for t in res.data}
    except Exception:
        return {}

@st.cache_data(ttl=60)
def fetch_classes_data():
    """classes அட்டவணையில் இருந்து வகுப்புப் பெயர்களை எடுக்க"""
    try:
        res = supabase.table("classes").select("class_name").order("class_name").execute()
        return [c['class_name'] for c in res.data]
    except Exception:
        return []

@st.cache_data(ttl=60)
def fetch_subjects_data():
    """subjects அட்டவணையில் இருந்து பாடங்களை எடுக்க"""
    try:
        res = supabase.table("subjects").select("subject_name").order("subject_name").execute()
        return [s['subject_name'] for s in res.data]
    except Exception:
        return []

@st.cache_data(ttl=60)
def fetch_current_allotments():
    """ஒதுக்கீடு செய்யப்பட்ட விவரங்களை எடுக்க"""
    # staff_allotment அட்டவணையை teachers-உடன் இணைத்து எடுக்கிறோம்
    res = supabase.table("staff_allotment").select("*, teachers(short_name)").execute()
    return res.data

# தரவுகளைப் பெறுதல்
teachers_dict = fetch_teachers_data()
classes_list = fetch_classes_data()
subjects_list = fetch_subjects_data()

# --- 2. ALLOTMENT FORM ---
with st.form("allotment_form", clear_on_submit=True):
    st.subheader("🆕 புதிய வகுப்பு ஒதுக்கீடு")
    
    col1, col2, col3, col4 = st.columns([2, 2, 2, 1])
    
    with col1:
        if teachers_dict:
            selected_teacher = st.selectbox("ஆசிரியர் (Teachers Table-ல் இருந்து):", list(teachers_dict.keys()))
        else:
            st.error("Teachers அட்டவணையில் தரவு இல்லை!")
            
    with col2:
        if classes_list:
            selected_class = st.selectbox("வகுப்பு (Classes Table-ல் இருந்து):", classes_list)
        else:
            selected_class = st.text_input("வகுப்பு (நேரடியாக உள்ளிடவும்):")
            
    with col3:
        if subjects_list:
            selected_subject = st.selectbox("பாடம்:", subjects_list)
        else:
            selected_subject = st.text_input("பாடம் (Type manually):")
            
    with col4:
        periods = st.number_input("பாடவேளைகள்:", min_value=1, max_value=40, value=5)
    
    if st.form_submit_button("💾 ஒதுக்கீட்டைச் சேமி"):
        if teachers_dict and selected_teacher and selected_class:
            try:
                supabase.table("staff_allotment").insert({
                    "teacher_id": teachers_dict[selected_teacher],
                    "class_name": selected_class,
                    "subject_name": selected_subject,
                    "periods_per_week": periods
                }).execute()
                st.success(f"வெற்றிகரமாகச் சேமிக்கப்பட்டது!")
                st.cache_data.clear()
                st.rerun()
            except Exception as e:
                st.error(f"பிழை: {e}")
        else:
            st.warning("தேவையான விவரங்களைத் தேர்ந்தெடுக்கவும்.")

st.divider()

# --- 3. DISPLAY & ANALYSIS ---
allotment_data = fetch_current_allotments()

if allotment_data:
    df = pd.DataFrame(allotment_data)
    # ஆசிரியரின் சுருக்கப் பெயரை மட்டும் பிரித்தெடுத்தல்
    df['Teacher'] = df['teachers'].apply(lambda x: x['short_name'] if x else "தெரியவில்லை")
    
    col_list, col_total = st.columns([2, 1])
    
    with col_list:
        st.subheader("📋 ஒதுக்கீடு பட்டியல்")
        display_df = df[['Teacher', 'class_name', 'subject_name', 'periods_per_week']]
        display_df.columns = ['ஆசிரியர்', 'வகுப்பு', 'பாடம்', 'பாடவேளைகள்']
        st.dataframe(display_df, use_container_width=True, hide_index=True)

    with col_total:
        st.subheader("🔢 மொத்தப் பணிச்சுமை (Total Workload)")
        workload = display_df.groupby('ஆசிரியர்')['பாடவேளைகள்'].sum().reset_index()
        workload.columns = ['ஆசிரியர்', 'மொத்த பீரியடுகள்']
        st.table(workload)
        
        # 28-க்கு மேல் இருந்தால் எச்சரிக்கை
        high_load_list = workload[workload['மொத்த பீரியடுகள்'] > 28]['ஆசிரியர்'].tolist()
        if high_load_list:
            st.error(f"⚠️ அதிக பணிச்சுமை: {', '.join(high_load_list)}")

    # --- 4. DELETE SECTION ---
    with st.expander("🗑️ ஒரு ஒதுக்கீட்டை நீக்க"):
        del_options = {f"{row['Teacher']} - {row['class_name']} ({row['subject_name']})": row['id'] for _, row in df.iterrows()}
        to_del = st.selectbox("நீக்க வேண்டியதை தேர்வு செய்க:", ["-- தேர்வு செய்க --"] + list(del_options.keys()))
        if st.button("Delete Now") and to_del != "-- தேர்வு செய்க --":
            supabase.table("staff_allotment").delete().eq("id", del_options[to_del]).execute()
            st.cache_data.clear()
            st.rerun()
else:
    st.info("ℹ️ இன்னும் ஒதுக்கீடுகள் செய்யப்படவில்லை.")
