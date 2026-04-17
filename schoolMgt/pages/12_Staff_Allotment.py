import streamlit as st
import pandas as pd
import hashlib
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

# --- 🎨 COLOR GENERATOR ---
def get_color(text):
    hash_object = hashlib.md5(text.encode()).hexdigest()
    r = (int(hash_object[:2], 16) % 100) + 155
    g = (int(hash_object[2:4], 16) % 100) + 155
    b = (int(hash_object[4:6], 16) % 100) + 155
    return f'#{r:02x}{g:02x}{b:02x}'

# --- ⚡ FETCH DATA ---
@st.cache_data(ttl=60)
def fetch_teachers():
    """ஆசிரியர்களின் பெயர், EMIS மற்றும் முதன்மைப் பாடத்தை எடுக்க"""
    res = supabase.table("teachers").select("emis_id, full_name, short_name, subject").order("full_name").execute()
    # பாடம் (Subject) விவரத்தையும் சேர்த்து சேமிக்கிறோம்
    return {f"{t['full_name']} ({t['short_name']})": (t['emis_id'], t['short_name'], t['full_name'], t.get('subject', '')) for t in res.data}

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
    res = supabase.table("staff_allotment").select("*").execute()
    return res.data

# தரவுகள் தயார் செய்தல்
teachers_dict = fetch_teachers()
subjects_list = fetch_subjects()
base_classes = fetch_classes_only()
comb_groups = fetch_combined_data()
all_dropdown_classes = base_classes + list(comb_groups.keys())
allotment_list = fetch_allotment_data()
df_allot = pd.DataFrame(allotment_list) if allotment_list else pd.DataFrame()

st.title("👨‍🏫 ஆசிரியர் பாடவேளை ஒதுக்கீடு")

# --- 📐 LAYOUT ---
col_form, col_visual = st.columns([1.3, 1.7])

with col_form:
    st.subheader("📝 ஒதுக்கீடு படிவம்")
    
    teacher_options = ["Select Teacher"] + list(teachers_dict.keys())
    selected_teacher_label = st.selectbox("ஆசிரியரைத் தேர்வு செய்க:", teacher_options)
    
    is_teacher_selected = selected_teacher_label != "Select Teacher"
    
    # ஆசிரியருக்கான இயல்புநிலைப் பாடத்தைக் கண்டறிதல் (Default Subject)
    default_sub_index = 0
    if is_teacher_selected:
        e_id, t_short, t_full, t_sub = teachers_dict[selected_teacher_label]
        # ஆசிரியரின் பாடம் பாடங்கள் பட்டியலில் இருந்தால் அதன் இன்டெக்ஸை எடுக்கவும்
        if t_sub in subjects_list:
            default_sub_index = subjects_list.index(t_sub)
    
    with st.form("allotment_form", clear_on_submit=True):
        f1, f2 = st.columns(2)
        with f1:
            c_name = st.selectbox("வகுப்பு / குழு:", all_dropdown_classes)
            # இங்கு index=default_sub_index கொடுக்கப்பட்டுள்ளது
            s_name = st.selectbox("பாடம்:", subjects_list, index=default_sub_index)
        with f2:
            p_count = st.number_input("பாடவேளைகள்:", min_value=1, value=7)
            st.write("")
            submit = st.form_submit_button("💾 ஒதுக்கீட்டைச் சேமி", use_container_width=True)
        
        if submit:
            if not is_teacher_selected:
                st.error("தயவுசெய்து ஒரு ஆசிரியரைத் தேர்வு செய்யவும்!")
            else:
                supabase.table("staff_allotment").insert({
                    "teacher_id": e_id, 
                    "teacher_name": f"{t_full} ({t_short})",
                    "class_name": c_name, 
                    "subject_name": s_name, 
                    "periods_per_week": p_count
                }).execute()
                st.cache_data.clear()
                st.success("சேமிக்கப்பட்டது!")
                st.rerun()

# --- வலதுபுறம் மற்றும் அட்டவணைப் பகுதிகள் முந்தைய குறியீட்டைப் போலவே இருக்கும் ---
# (சுருக்கம் கருதி இங்கு தவிர்க்கப்பட்டுள்ளது, மாற்றங்கள் தேவையில்லை)
