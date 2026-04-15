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

# --- ⚡ FETCH DATA ---
@st.cache_data(ttl=60)
def fetch_teachers():
    res = supabase.table("teachers").select("emis_id, short_name").order("short_name").execute()
    # லேபிளில் பெயரையும் EMIS ID-யையும் காட்டி, வேல்யூவாக EMIS ID-யையே வைக்கிறோம்
    return {f"{t['short_name']} ({t['emis_id']})": (t['emis_id'], t['short_name']) for t in res.data}

@st.cache_data(ttl=60)
def fetch_subjects():
    res = supabase.table("subjects").select("subject_name").order("subject_name").execute()
    return [s['subject_name'] for s in res.data]

@st.cache_data(ttl=60)
def fetch_classes_only():
    res = supabase.table("classes").select("class_name").order("class_name").execute()
    return [c['class_name'] for c in res.data]

@st.cache_data(ttl=60)
def fetch_combined_data():
    res = supabase.table("combined_groups").select("*").execute()
    return {g['group_name']: g['class_list'] for g in res.data}

@st.cache_data(ttl=60)
def fetch_allotment_data():
    # இப்போது நேரடியாக டேபிளில் உள்ள டேட்டாவையே எடுக்கலாம்
    res = supabase.table("staff_allotment").select("*").execute()
    return res.data

# தரவுகளைத் தயார் செய்தல்
teachers_data = fetch_teachers()
subjects_list = fetch_subjects()
base_classes = fetch_classes_only()
comb_groups = fetch_combined_data()
all_dropdown_classes = base_classes + list(comb_groups.keys())
allotment_list = fetch_allotment_data()

st.title("👨‍🏫 ஆசிரியர் பாடவேளை ஒதுக்கீடு (Staff Allotment)")

# --- 📐 LAYOUT ---
col_form, col_visual = st.columns([1.8, 1.2])

with col_form:
    with st.form("allotment_form", clear_on_submit=True):
        st.subheader("🆕 புதிய ஒதுக்கீடு")
        c1, c2 = st.columns(2)
        with c1:
            selected_label = st.selectbox("ஆசிரியர்:", list(teachers_data.keys()))
            c_name = st.selectbox("வகுப்பு / குழு:", all_dropdown_classes)
        with c2:
            s_name = st.selectbox("பாடம்:", subjects_list)
            p_count = st.number_input("பாடவேளைகள்:", min_value=1, value=5)
        
        if st.form_submit_button("💾 ஒதுக்கீட்டைச் சேமி"):
            e_id, t_name = teachers_data[selected_label]
            supabase.table("staff_allotment").insert({
                "teacher_id": e_id,    # EMIS ID சேமிக்கப்படும்
                "teacher_name": t_name, # ஆசிரியர் பெயரும் சேமிக்கப்படும்
                "class_name": c_name,
                "subject_name": s_name,
                "periods_per_week": p_count
            }).execute()
            st.cache_data.clear()
            st.rerun()

    # ஒதுக்கீடு பட்டியல்
    if allotment_list:
        st.subheader("📋 ஒதுக்கீடு பட்டியல்")
        df_allot = pd.DataFrame(allotment_list)
        # SUPABASE-ல் உள்ள காலம்களைத் தெளிவாகக் காட்டுதல்
        df_display = df_allot[['teacher_id', 'teacher_name', 'class_name', 'subject_name', 'periods_per_week']]
        df_display.columns = ['EMIS ID', 'ஆசிரியர்', 'வகுப்பு', 'பாடம்', 'பீரியட்கள்']
        st.dataframe(df_display, use_container_width=True, hide_index=True)

with col_visual:
    st.subheader("🏫 வகுப்பு வாரியான பாடவேளைகள்")
    
    # கணக்கீடு
    class_totals = {c: 0 for c in base_classes}
    for entry in allotment_list:
        target = entry['class_name']
        periods = entry['periods_per_week']
        if target in comb_groups:
            for sub_class in comb_groups[target]:
                if sub_class in class_totals: class_totals[sub_class] += periods
        elif target in class_totals:
            class_totals[target] += periods

    # கார்டுகள் (Visual Cards)
    v_col1, v_col2 = st.columns(2)
    for i, (cls, total) in enumerate(class_totals.items()):
        target_col = v_col1 if i % 2 == 0 else v_col2
        box_color = "#FF4B4B" if total > 45 else "#F0F2F6"
        text_color = "white" if total > 45 else "#31333F"
        
        target_col.markdown(f"""
            <div style="background-color: {box_color}; padding: 12px; border-radius: 8px; border: 1px solid #ddd; text-align: center; margin-bottom: 8px;">
                <h5 style="margin: 0; color: {text_color};">{cls}</h5>
                <p style="font-size: 20px; font-weight: bold; margin: 0; color: {text_color};">{total}</p>
            </div>
        """, unsafe_allow_html=True)
