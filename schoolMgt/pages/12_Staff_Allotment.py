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
    res = supabase.table("teachers").select("emis_id, full_name, short_name, subject").order("full_name").execute()
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
emis_to_full_display = {val[0]: key for key, val in teachers_dict.items()}

st.title("👨‍🏫 ஆசிரியர் பாடவேளை ஒதுக்கீடு")

# --- 📐 LAYOUT ---
col_form, col_visual = st.columns([1.5, 1.5])

with col_form:
    st.subheader("📝 ஒதுக்கீடு படிவம்")
    teacher_options = ["Select Teacher"] + list(teachers_dict.keys())
    selected_teacher_label = st.selectbox("ஆசிரியரைத் தேர்வு செய்க:", teacher_options)
    
    is_teacher_selected = selected_teacher_label != "Select Teacher"
    default_sub_index = 0
    
    if is_teacher_selected:
        e_id, t_short, t_full, t_sub = teachers_dict[selected_teacher_label]
        if t_sub in subjects_list:
            default_sub_index = subjects_list.index(t_sub)
    
    with st.form("allotment_form", clear_on_submit=True):
        f1, f2 = st.columns(2)
        with f1:
            c_name = st.selectbox("வகுப்பு / குழு:", all_dropdown_classes)
            s_name = st.selectbox("பாடம்:", subjects_list, index=default_sub_index)
        with f2:
            p_count = st.number_input("வாரத்தின் மொத்த பீரியட்கள்:", min_value=1, value=7)
            # 🆕 வாரத்திற்கு எத்தனை முறை Double Period வர வேண்டும்?
            double_freq = st.number_input("தொடர் பாடவேளைகளின் எண்ணிக்கை (No. of Double Periods):", 
                                         min_value=0, max_value=5, value=0, 
                                         help="வாரத்திற்கு எத்தனை முறை 2 பீரியட்கள் தொடர்ந்து வர வேண்டும்?")
            
            submit = st.form_submit_button("💾 ஒதுக்கீட்டைச் சேமி", use_container_width=True)
        
        if submit:
            if not is_teacher_selected:
                st.warning("தயவுசெய்து ஒரு ஆசிரியரைத் தேர்வு செய்யவும்!")
            elif (double_freq * 2) > p_count:
                st.error(f"பிழை: {double_freq} முறை தொடர் பீரியட்கள் ஒதுக்க மொத்த பீரியட்கள் போதாது!")
            else:
                try:
                    supabase.table("staff_allotment").insert({
                        "teacher_id": e_id, 
                        "teacher_name": f"{t_full} ({t_short})", 
                        "class_name": c_name, 
                        "subject_name": s_name, 
                        "periods_per_week": p_count,
                        "double_period_count": double_freq
                    }).execute()
                    st.cache_data.clear()
                    st.success("வெற்றிகரமாகச் சேமிக்கப்பட்டது!")
                    st.rerun()
                except Exception as e:
                    st.error(f"சேமிப்பதில் பிழை: {e}")

# (வகுப்பு மற்றும் ஆசிரியர் சில்லுகள் - காட்சிப்படுத்துதல்)
with col_visual:
    st.markdown("##### 🏫 வகுப்பு வாரியாக சுமை")
    # ... (முந்தைய குறியீட்டில் உள்ள அதே காட்சிப்படுத்தல் லாஜிக்) ...
    st.info("இங்கு வகுப்பு மற்றும் ஆசிரியர் வாரியான பணிச்சுமை (Workload) தோன்றும்.")

# --- 📊 அட்டவணை பகுதி ---
st.divider()
st.subheader("📊 அனைத்து ஆசிரியர் ஒதுக்கீடு விவரங்கள்")

if not df_allot.empty:
    # முழுப் பெயரைச் சரியாகக் காட்டுதல்
    df_allot['ஆசிரியர்'] = df_allot['teacher_id'].map(emis_to_full_display).fillna(df_allot['teacher_name'])
    
    df_show = df_allot[['ஆசிரியர்', 'class_name', 'subject_name', 'periods_per_week', 'double_period_count']].copy()
    df_show.columns = ['ஆசிரியர் பெயர்', 'வகுப்பு', 'பாடம்', 'மொத்த பீரியட்கள்', 'தொடர் பீரியட்கள் எண்ணிக்கை']
    
    st.dataframe(
        df_show.style.map(lambda x: f'background-color: {get_color(str(x))}; color: black;', subset=['பாடம்']), 
        use_container_width=True, 
        hide_index=True
    )
else:
    st.info("தகவல்கள் எதுவும் இல்லை.")
