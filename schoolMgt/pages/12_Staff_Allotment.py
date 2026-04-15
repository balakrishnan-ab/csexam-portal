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
    # id (uuid) மற்றும் short_name, emis_id ஆகிய மூன்றையும் எடுக்கிறோம்
    res = supabase.table("teachers").select("id, short_name, emis_id").order("short_name").execute()
    # லேபிளில் பெயரைக் காட்டிவிட்டு, வேல்யூவாக UUID-ஐ வைத்துக் கொள்கிறோம்
    return {f"{t['short_name']} ({t['emis_id']})": t['id'] for t in res.data}

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
    # teachers டேபிளில் இருந்து short_name மற்றும் emis_id-ஐயும் சேர்த்து எடுக்கிறோம் (Join)
    res = supabase.table("staff_allotment").select("*, teachers(short_name, emis_id)").execute()
    return res.data

# தரவுகளைத் தயார் செய்தல்
teachers_dict = fetch_teachers()
subjects_list = fetch_subjects()
final_classes_list = fetch_all_classes()
allotment_data = fetch_current_allotments()

# --- 2. LAYOUT ---
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
                # இங்கு teachers_dict[t_label] என்பது ஆசிரியரின் UUID-ஐத் தரும்
                supabase.table("staff_allotment").insert({
                    "teacher_id": teachers_dict[t_label], 
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
        # Join செய்யப்பட்ட விவரங்களைச் சீரமைத்தல்
        df_allot['ஆசிரியர்'] = df_allot['teachers'].apply(lambda x: x['short_name'] if x else "N/A")
        df_allot['EMIS ID'] = df_allot['teachers'].apply(lambda x: x['emis_id'] if x else "N/A")
        
        st.dataframe(df_allot[['EMIS ID', 'ஆசிரியர்', 'class_name', 'subject_name', 'periods_per_week']], use_container_width=True, hide_index=True)
        
        with st.expander("🗑️ நீக்குதல்"):
            del_opt = {f"{r['teachers']['short_name']} - {r['class_name']}": r['id'] for r in allotment_data}
            to_del = st.selectbox("நீக்க வேண்டியதை தேர்வு செய்க:", ["-- Select --"] + list(del_options.keys()) if 'del_options' in locals() else list(del_opt.keys()))
            if st.button("Delete") and to_del != "-- Select --":
                supabase.table("staff_allotment").delete().eq("id", del_opt[to_del]).execute()
                st.cache_data.clear()
                st.rerun()

with col_summary:
    st.subheader("🏫 வகுப்பு வாரியாகப் பாடவேளைகள்")
    if allotment_data:
        df_sum = pd.DataFrame(allotment_data)
        class_summary = df_sum.groupby('class_name')['periods_per_week'].sum().reset_index()
        class_summary.columns = ['வகுப்பு', 'மொத்த பீரியடுகள்']
        st.dataframe(class_summary, use_container_width=True, hide_index=True)
    else:
        st.info("ஒதுக்கீடுகள் இன்னும் இல்லை.")
