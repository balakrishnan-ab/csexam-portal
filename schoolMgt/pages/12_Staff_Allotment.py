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

# --- ⚡ FETCH DATA ---

@st.cache_data(ttl=60)
def fetch_teachers():
    res = supabase.table("teachers").select("id, short_name").order("short_name").execute()
    return {t['short_name']: t['id'] for t in res.data}

@st.cache_data(ttl=60)
def fetch_subjects():
    res = supabase.table("subjects").select("subject_name").order("subject_name").execute()
    return [s['subject_name'] for s in res.data]

@st.cache_data(ttl=60)
def fetch_all_classes():
    # 1. தனி வகுப்புகளை எடுத்தல்
    res_classes = supabase.table("classes").select("class_name").order("class_name").execute()
    classes = [c['class_name'] for c in res_classes.data]
    
    # 2. கம்பைன் குரூப்களை எடுத்தல்
    res_combined = supabase.table("combined_groups").select("group_name").order("group_name").execute()
    combined = [g['group_name'] for g in res_combined.data]
    
    return classes + combined

@st.cache_data(ttl=60)
def fetch_current_allotments():
    # staff_allotment அட்டவணையை teachers-உடன் இணைத்து எடுக்கிறோம்
    res = supabase.table("staff_allotment").select("*, teachers(short_name)").execute()
    return res.data

# தரவுகளைப் பெறுதல்
teachers_dict = fetch_teachers()
subjects_list = fetch_subjects()
final_classes_list = fetch_all_classes()

# --- 2. ALLOTMENT FORM ---
with st.form("allotment_form", clear_on_submit=True):
    st.subheader("🆕 புதிய ஒதுக்கீட்டைச் சேர்க்க")
    
    col1, col2, col3, col4 = st.columns([2, 2, 2, 1])
    
    with col1:
        t_name = st.selectbox("ஆசிரியர்:", list(teachers_dict.keys()) if teachers_dict else ["No Teachers"])
    with col2:
        c_name = st.selectbox("வகுப்பு / கம்பைன் குழு:", final_classes_list if final_classes_list else ["No Classes"])
    with col3:
        s_name = st.selectbox("பாடம்:", subjects_list if subjects_list else ["No Subjects"])
    with col4:
        p_count = st.number_input("பாடவேளைகள்:", min_value=1, max_value=45, value=5)
    
    if st.form_submit_button("💾 ஒதுக்கீட்டைச் சேமி"):
        if teachers_dict and final_classes_list and subjects_list:
            try:
                supabase.table("staff_allotment").insert({
                    "teacher_id": teachers_dict[t_name],
                    "class_name": c_name,
                    "subject_name": s_name,
                    "periods_per_week": p_count
                }).execute()
                st.success(f"வெற்றிகரமாகச் சேமிக்கப்பட்டது!")
                st.cache_data.clear()
                st.rerun()
            except Exception as e:
                st.error(f"பிழை: {e}")

st.divider()

# --- 3. DISPLAY & ANALYSIS ---
allotment_data = fetch_current_allotments()

if allotment_data:
    df = pd.DataFrame(allotment_data)
    df['ஆசிரியர்'] = df['teachers'].apply(lambda x: x['short_name'] if x else "Unknown")
    
    tab1, tab2 = st.tabs(["📋 ஒதுக்கீடு பட்டியல்", "📊 மொத்த பணிச்சுமை (Total Workload)"])
    
    with tab1:
        st.subheader("அனைத்து ஒதுக்கீடுகள்")
        display_df = df[['ஆசிரியர்', 'class_name', 'subject_name', 'periods_per_week']]
        display_df.columns = ['ஆசிரியர்', 'வகுப்பு', 'பாடம்', 'பாடவேளைகள்']
        st.dataframe(display_df, use_container_width=True, hide_index=True)

    with tab2:
        st.subheader("🔢 ஒரு வாரத்திற்கான மொத்த பாடவேளைகள்")
        workload = display_df.groupby('ஆசிரியர்')['பாடவேளைகள்'].sum().reset_index()
        workload.columns = ['ஆசிரியர் பெயர்', 'மொத்த பீரியடுகள்']
        
        # 28-க்கு மேல் இருந்தால் எச்சரிக்கை
        st.table(workload.style.applymap(lambda x: 'color: red' if isinstance(x, int) and x > 28 else 'color: black', subset=['மொத்த பீரியடுகள்']))
        st.info("💡 குறிப்பு: கம்பைன் வகுப்புகளுக்கு ஒதுக்கப்பட்ட பீரியடுகள் ஒரு முறை மட்டுமே கணக்கிடப்படும்.")

    # --- 4. DELETE OPTION ---
    st.divider()
    with st.expander("🗑️ ஒதுக்கீட்டை நீக்க"):
        del_options = {f"{row['ஆசிரியர்']} - {row['class_name']} ({row['subject_name']})": row['id'] for _, row in df.iterrows()}
        to_del = st.selectbox("நீக்க வேண்டியதை தேர்வு செய்க:", ["-- Select --"] + list(del_options.keys()))
        if st.button("Delete Now", type="primary") and to_del != "-- Select --":
            supabase.table("staff_allotment").delete().eq("id", del_options[to_del]).execute()
            st.cache_data.clear()
            st.rerun()
else:
    st.info("இன்னும் ஒதுக்கீடுகள் செய்யப்படவில்லை.")
