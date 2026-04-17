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
emis_to_full = {val[0]: key for key, val in teachers_dict.items()}

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
            # நீங்கள் கேட்டபடி லேபிள் சுருக்கப்பட்டுள்ளது
            double_freq = st.number_input("தொடர் பாடவேளைகள்:", min_value=0, max_value=5, value=0)
            
            submit = st.form_submit_button("💾 ஒதுக்கீட்டைச் சேமி", use_container_width=True)
        
        if submit:
            if not is_teacher_selected:
                st.warning("ஆசிரியரைத் தேர்வு செய்யவும்!")
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
                    st.rerun()
                except Exception as e:
                    st.error(f"பிழை: {e}")

with col_visual:
    # --- 🏫 வகுப்பு சில்லுகள் ---
    st.markdown("##### 🏫 வகுப்பு வாரியாக சுமை")
    class_totals = {c: 0 for c in base_classes}
    if not df_allot.empty:
        for _, entry in df_allot.iterrows():
            target, p = entry['class_name'], entry['periods_per_week']
            if target in comb_groups:
                for sub_c in comb_groups[target]:
                    if sub_c in class_totals: class_totals[sub_c] += p
            elif target in class_totals:
                class_totals[target] += p

    c_rows = [list(class_totals.items())[i:i+6] for i in range(0, len(class_totals), 6)]
    for row in c_rows:
        cols = st.columns(6)
        for idx, (cls, tot) in enumerate(row):
            bg = get_color(cls)
            border = "2px solid red" if tot > 45 else "1px solid #ddd"
            cols[idx].markdown(f"""<div style="background:{bg}; padding:2px; border-radius:4px; border:{border}; text-align:center; margin-bottom:4px; height:50px;">
                <div style="font-size:10px; font-weight:bold; color:black;">{cls}</div>
                <div style="font-size:16px; font-weight:bold; color:black;">{tot}</div>
            </div>""", unsafe_allow_html=True)

# --- 📊 அட்டவணை பகுதி (KeyError பிழை நீக்கப்பட்டது) ---
st.divider()
st.subheader("📊 அனைத்து ஆசிரியர் ஒதுக்கீடு விவரங்கள்")

if not df_allot.empty:
    # 1. EMIS ID மூலம் ஆசிரியரின் முழுப் பெயரை உருவாக்குதல்
    df_allot['ஆசிரியர்_முழுப்பெயர்'] = df_allot['teacher_id'].map(emis_to_full).fillna(df_allot['teacher_name'])
    
    # 2. பிழையைத் தவிர்க்க, தேவையான நெடுவரிசைகள் இருப்பதை உறுதி செய்து எடுத்தல்
    cols_to_show = ['ஆசிரியர்_முழுப்பெயர்', 'class_name', 'subject_name', 'periods_per_week']
    if 'double_period_count' in df_allot.columns:
        cols_to_show.append('double_period_count')
    
    df_show = df_allot[cols_to_show].copy()
    
    # 3. நெடுவரிசை பெயர்களைத் தமிழில் மாற்றுதல்
    column_mapping = {
        'ஆசிரியர்_முழுப்பெயர்': 'ஆசிரியர்',
        'class_name': 'வகுப்பு',
        'subject_name': 'பாடம்',
        'periods_per_week': 'மொத்த பீரியட்கள்',
        'double_period_count': 'தொடர் பாடவேளைகள்'
    }
    df_show.rename(columns=column_mapping, inplace=True)
    
    st.dataframe(
        df_show.style.map(lambda x: f'background-color: {get_color(str(x))}; color: black;', subset=['பாடம்']), 
        use_container_width=True, 
        hide_index=True
    )
    
    with st.expander("🗑️ ஒரு ஒதுக்கீட்டை நீக்க"):
        del_dict = {f"{r['ஆசிரியர்']} - {r['வகுப்பு']} ({r['பாடம்']})": r_id for r_id, r in zip(df_allot['id'], df_show.to_dict('records'))}
        to_del = st.selectbox("தேர்வு செய்க:", ["-- Select --"] + list(del_dict.keys()))
        if st.button("Delete") and to_del != "-- Select --":
            supabase.table("staff_allotment").delete().eq("id", del_dict[to_del]).execute()
            st.cache_data.clear()
            st.rerun()
else:
    st.info("தகவல்கள் எதுவும் இல்லை.")
