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
    """பெயரை அடிப்படையாகக் கொண்டு நிலையான வண்ணத்தை உருவாக்கும்"""
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

# தரவுகள்
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
            p_count = st.number_input("பாடவேளைகள்:", min_value=1, value=7)
            st.write("")
            submit = st.form_submit_button("💾 ஒதுக்கீட்டைச் சேமி", use_container_width=True)
        
        if submit:
            if not is_teacher_selected:
                st.warning("தயவுசெய்து ஒரு ஆசிரியரைத் தேர்வு செய்யவும்!")
            else:
                supabase.table("staff_allotment").insert({
                    "teacher_id": e_id, 
                    "teacher_name": f"{t_full} ({t_short})", 
                    "class_name": c_name, 
                    "subject_name": s_name, 
                    "periods_per_week": p_count
                }).execute()
                st.cache_data.clear()
                st.rerun()

with col_visual:
    # --- 🏫 வகுப்பு சில்லுகள் (Row of 6) ---
    st.markdown("##### 🏫 வகுப்பு வாரியாக")
    class_totals = {c: 0 for c in base_classes}
    if not df_allot.empty:
        for _, entry in df_allot.iterrows():
            target, periods = entry['class_name'], entry['periods_per_week']
            if target in comb_groups:
                for sub in comb_groups[target]:
                    if sub in class_totals: class_totals[sub] += periods
            elif target in class_totals: class_totals[target] += periods

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

    st.divider()

    # --- 👨‍🏫 ஆசிரியர் சில்லுகள் (Row of 6) ---
    st.markdown("##### 👨‍🏫 ஆசிரியர் வாரியாக (மொத்த பீரியட்கள்)")
    if not df_allot.empty:
        t_workload = df_allot.groupby('teacher_name')['periods_per_week'].sum().reset_index()
        t_rows = [t_workload.iloc[i:i+6] for i in range(0, len(t_workload), 6)]
        for row_df in t_rows:
            cols = st.columns(6)
            for idx, (_, r) in enumerate(row_df.iterrows()):
                name_to_show = r['teacher_name'].split('(')[-1].replace(')', '')
                bg = get_color(name_to_show)
                cols[idx].markdown(f"""<div style="background:{bg}; padding:2px; border-radius:4px; border:1px solid #ccc; text-align:center; margin-bottom:4px; height:50px;">
                    <div style="font-size:10px; font-weight:bold; color:black;">{name_to_show}</div>
                    <div style="font-size:16px; font-weight:bold; color:black;">{r['periods_per_week']}</div>
                </div>""", unsafe_allow_html=True)

# --- 📊 அட்டவணை பகுதி ---
st.divider()
if is_teacher_selected:
    mask = df_allot['teacher_id'] == e_id if not df_allot.empty else False
    display_df = df_allot[mask].copy() if not df_allot.empty else pd.DataFrame()
    st.subheader(f"📊 {selected_teacher_label} - ஒதுக்கீடு விவரம்")
else:
    display_df = df_allot.copy() if not df_allot.empty else pd.DataFrame()
    st.subheader("📊 அனைத்து ஆசிரியர் ஒதுக்கீடு விவரங்கள்")

if not display_df.empty:
    df_show = display_df[['teacher_name', 'class_name', 'subject_name', 'periods_per_week']].copy()
    df_show.columns = ['ஆசிரியர் (முழுபெயர்)', 'வகுப்பு', 'பாடம்', 'பீரியட்கள்']
    
    # பிழையைச் சரிசெய்ய map பயன்படுத்தப்பட்டுள்ளது (applymap-க்கு பதிலாக)
    st.dataframe(
        df_show.style.map(lambda x: f'background-color: {get_color(str(x))}; color: black;', subset=['பாடம்']), 
        use_container_width=True, 
        hide_index=True
    )
    
    with st.expander("🗑️ ஒரு ஒதுக்கீட்டை நீக்க"):
        del_dict = {f"{r['teacher_name']} - {r['class_name']} ({r['subject_name']})": r['id'] for _, r in display_df.iterrows()}
        to_del = st.selectbox("தேர்வு செய்க:", ["-- Select --"] + list(del_dict.keys()))
        if st.button("Delete Now", type="primary") and to_del != "-- Select --":
            supabase.table("staff_allotment").delete().eq("id", del_dict[to_del]).execute()
            st.cache_data.clear()
            st.rerun()
else:
    st.info("தகவல்கள் எதுவும் இல்லை.")
