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
    # emis_id மற்றும் short_name-ஐ எடுக்கிறோம்
    res = supabase.table("teachers").select("emis_id, short_name").order("short_name").execute()
    return {f"{t['short_name']} ({t['emis_id']})": t['emis_id'] for t in res.data}

@st.cache_data(ttl=60)
def fetch_subjects():
    res = supabase.table("subjects").select("subject_name").order("subject_name").execute()
    return [s['subject_name'] for s in res.data]

@st.cache_data(ttl=60)
def fetch_all_classes():
    res_c = supabase.table("classes").select("class_name").order("class_name").execute()
    classes = [c['class_name'] for c in res_c.data]
    res_g = supabase.table("combined_groups").select("group_name").order("group_name").execute()
    groups = [g['group_name'] for g in res_g.data]
    return classes + groups

@st.cache_data(ttl=60)
def fetch_current_allotments():
    # இப்போது teacher_id-க்கு பதில் emis_id-ஐ வைத்துத் தேடுகிறோம்
    res = supabase.table("staff_allotment").select("*").execute()
    return res.data

# தரவுகளைத் தயார் செய்தல்
teachers_dict = fetch_teachers()
subjects_list = fetch_subjects()
final_classes_list = fetch_all_classes()
allotment_data = fetch_current_allotments()

# --- 2. LAYOUT: இடதுபுறம் படிவம், வலதுபுறம் வகுப்பு கணக்கு ---
col_form, col_summary = st.columns([2, 1])

with col_form:
    with st.form("allotment_form", clear_on_submit=True):
        st.subheader("🆕 புதிய ஒதுக்கீட்டைச் சேர்க்க")
        c1, c2 = st.columns(2)
        with c1:
            t_label = st.selectbox("ஆசிரியர் (EMIS ID அடிப்படையில்):", list(teachers_dict.keys()) if teachers_dict else ["No Teachers Found"])
            c_name = st.selectbox("வகுப்பு / கம்பைன் குழு:", final_classes_list if final_classes_list else ["No Classes Found"])
        with c2:
            s_name = st.selectbox("பாடம்:", subjects_list if subjects_list else ["No Subjects Found"])
            p_count = st.number_input("பாடவேளைகள் (Periods):", min_value=1, max_value=45, value=5)
        
        if st.form_submit_button("💾 ஒதுக்கீட்டைச் சேமி"):
            try:
                supabase.table("staff_allotment").insert({
                    "teacher_id": teachers_dict[t_label], # இங்கு EMIS ID சேமிக்கப்படும்
                    "class_name": c_name,
                    "subject_name": s_name,
                    "periods_per_week": p_count
                }).execute()
                st.success("வெற்றிகரமாகச் சேமிக்கப்பட்டது!")
                st.cache_data.clear()
                st.rerun()
            except Exception as e:
                st.error(f"பிழை: {e}")

    st.divider()
    
    # ஒதுக்கீடு பட்டியல்
    if allotment_data:
        st.subheader("📋 ஒதுக்கீடு பட்டியல்")
        df_allot = pd.DataFrame(allotment_data)
        st.dataframe(df_allot[['teacher_id', 'class_name', 'subject_name', 'periods_per_week']], use_container_width=True, hide_index=True)
        
        with st.expander("🗑️ நீக்குதல்"):
            del_opt = {f"{r['teacher_id']} - {r['class_name']}": r['id'] for r in allotment_data}
            to_del = st.selectbox("தேர்வு செய்க:", ["-- Select --"] + list(del_opt.keys()))
            if st.button("Delete") and to_del != "-- Select --":
                supabase.table("staff_allotment").delete().eq("id", del_opt[to_del]).execute()
                st.cache_data.clear()
                st.rerun()

with col_summary:
    st.subheader("🏫 வகுப்பு வாரியாகப் பாடவேளைகள்")
    if allotment_data:
        df_sum = pd.DataFrame(allotment_data)
        # வகுப்பு வாரியாகக் கூடுதல் (Sum by Class)
        class_summary = df_sum.groupby('class_name')['periods_per_week'].sum().reset_index()
        class_summary.columns = ['வகுப்பு', 'மொத்த பீரியடுகள்']
        
        # அட்டவணையாகக் காட்டுதல்
        st.dataframe(class_summary, use_container_width=True, hide_index=True)
        
        # ஒரு வகுப்புக்கு 45-க்கு மேல் போனால் எச்சரிக்கை
        over_load = class_summary[class_summary['மொத்த பீரியடுகள்'] > 45]
        if not over_load.empty:
            st.warning("⚠️ சில வகுப்புகளுக்குப் பாடவேளைகள் 45-ஐத் தாண்டியுள்ளது!")
    else:
        st.info("ஒதுக்கீடுகள் இன்னும் இல்லை.")
