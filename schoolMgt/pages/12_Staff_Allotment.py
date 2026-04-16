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
    hash_object = hashlib.md5(text.encode())
    hex_hash = hash_object.hexdigest()
    r = (int(hex_hash[:2], 16) % 100) + 155
    g = (int(hex_hash[2:4], 16) % 100) + 155
    b = (int(hex_hash[4:6], 16) % 100) + 155
    return f'#{r:02x}{g:02x}{b:02x}'

# --- ⚡ FETCH DATA ---
@st.cache_data(ttl=60)
def fetch_teachers():
    res = supabase.table("teachers").select("emis_id, full_name, short_name").order("full_name").execute()
    return {f"{t['full_name']} ({t['short_name']})": (t['emis_id'], t['short_name']) for t in res.data}

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

# தரவுகளைத் தயார் செய்தல்
teachers_data = fetch_teachers()
subjects_list = fetch_subjects()
base_classes = fetch_classes_only()
comb_groups = fetch_combined_data()
all_dropdown_classes = base_classes + list(comb_groups.keys())
allotment_list = fetch_allotment_data()
df_allot = pd.DataFrame(allotment_list) if allotment_list else pd.DataFrame()

st.title("👨‍🏫 ஆசிரியர் பாடவேளை ஒதுக்கீடு மேலாண்மை")

# --- 📐 LAYOUT ---
col_form, col_visual = st.columns([1.6, 1.4])

with col_form:
    # --- 🔎 LIVE TEACHER STATUS ---
    st.subheader("📝 ஒதுக்கீடு படிவம்")
    
    # ஆசிரியரைத் தேர்ந்தெடுக்கும் போதே அவர் நிலையைத் தெரிந்துகொள்ள
    selected_teacher_label = st.selectbox("ஆசிரியரைத் தேர்வு செய்க:", list(teachers_data.keys()), key="main_teacher_sel")
    e_id, t_short = teachers_data[selected_teacher_label]
    
    # தற்போதைய ஆசிரியரின் தரவை மட்டும் பிரித்தெடுத்தல்
    teacher_allotments = df_allot[df_allot['teacher_id'] == e_id] if not df_allot.empty else pd.DataFrame()
    total_assigned = teacher_allotments['periods_per_week'].sum() if not teacher_allotments.empty else 0

    # ஆசிரியர் நிலை - கார்டு
    c_m1, c_m2 = st.columns([1, 2])
    c_m1.metric("ஒதுக்கப்பட்ட பீரியட்கள்", f"{total_assigned} / 28")
    
    if not teacher_allotments.empty:
        with c_m2:
            st.caption(f"{t_short}-க்கு ஏற்கனவே ஒதுக்கப்பட்டவை:")
            summary_text = ", ".join([f"{r['class_name']}({r['periods_per_week']})" for _, r in teacher_allotments.iterrows()])
            st.info(summary_text)

    # --- 폼 (Form) ---
    with st.form("allotment_form", clear_on_submit=True):
        f_col1, f_col2 = st.columns(2)
        with f_col1:
            c_name = st.selectbox("வகுப்பு / குழு:", all_dropdown_classes)
            s_name = st.selectbox("பாடம்:", subjects_list)
        with f_col2:
            p_count = st.number_input("பாடவேளைகள்:", min_value=1, value=7)
            st.write("") # இடைவெளிக்காக
            submit = st.form_submit_button("💾 ஒதுக்கீட்டைச் சேமி", use_container_width=True)
        
        if submit:
            supabase.table("staff_allotment").insert({
                "teacher_id": e_id,
                "teacher_name": t_short,
                "class_name": c_name,
                "subject_name": s_name,
                "periods_per_week": p_count
            }).execute()
            st.cache_data.clear()
            st.rerun()

    st.divider()
    
    # --- 🗑️ DELETE SECTION (Easier to access) ---
    with st.expander("🗑️ ஒதுக்கீடுகளை நீக்க"):
        if not df_allot.empty:
            del_opt = {f"{r['teacher_name']} - {r['class_name']} ({r['subject_name']})": r['id'] for _, r in df_allot.iterrows()}
            to_del = st.selectbox("நீக்க வேண்டியதைத் தேர்வு செய்க:", ["-- Select --"] + list(del_opt.keys()))
            if st.button("Delete Now", type="primary") and to_del != "-- Select --":
                supabase.table("staff_allotment").delete().eq("id", del_opt[to_del]).execute()
                st.cache_data.clear()
                st.rerun()

with col_visual:
    st.subheader("🏫 வகுப்பு வாரியான பணிச்சுமை")
    
    class_totals = {c: 0 for c in base_classes}
    if not df_allot.empty:
        for _, entry in df_allot.iterrows():
            target = entry['class_name']
            periods = entry['periods_per_week']
            if target in comb_groups:
                for sub_class in comb_groups[target]:
                    if sub_class in class_totals: class_totals[sub_class] += periods
            elif target in class_totals:
                class_totals[target] += periods

    cols_per_row = 5
    class_items = list(class_totals.items())
    for i in range(0, len(class_items), cols_per_row):
        row_cols = st.columns(cols_per_row)
        for j in range(cols_per_row):
            if i + j < len(class_items):
                cls, total = class_items[i + j]
                bg_color = get_color(cls)
                border = "2px solid red" if total > 45 else "1px solid #ddd"
                row_cols[j].markdown(f"""
                    <div style="background-color:{bg_color}; padding:5px; border-radius:5px; border:{border}; text-align:center; margin-bottom:5px;">
                        <div style="font-size:12px; font-weight:bold;">{cls}</div>
                        <div style="font-size:20px; font-weight:bold;">{total}</div>
                    </div>
                """, unsafe_allow_html=True)

# --- 📊 FULL TABLE AT THE BOTTOM (With Filters) ---
st.divider()
st.subheader("📊 முழு ஒதுக்கீடு பட்டியல்")
if not df_allot.empty:
    search_q = st.text_input("🔍 பட்டியலில் தேட (ஆசிரியர் பெயர் அல்லது வகுப்பு):", "")
    
    # Filtering Logic
    filtered_df = df_allot[
        df_allot['teacher_name'].str.contains(search_q, case=False) | 
        df_allot['class_name'].str.contains(search_q, case=False)
    ]
    
    df_display = filtered_df[['teacher_name', 'class_name', 'subject_name', 'periods_per_week']]
    df_display.columns = ['ஆசிரியர்', 'வகுப்பு', 'பாடம்', 'பீரியட்கள்']
    
    def style_row(val):
        return f'background-color: {get_color(val)}; color: black;'

    st.dataframe(df_display.style.map(style_row, subset=['பாடம்']), use_container_width=True)
else:
    st.info("ஒதுக்கீடுகள் இன்னும் செய்யப்படவில்லை.")
