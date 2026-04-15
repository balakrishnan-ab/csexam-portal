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

# --- 🎨 DYNAMIC COLOR GENERATOR ---
def get_color(text):
    """பெயரை அடிப்படையாகக் கொண்டு ஒரு நிலையான வெளிர் வண்ணத்தை உருவாக்கும்"""
    hash_object = hashlib.md5(text.encode())
    hex_hash = hash_object.hexdigest()
    # வெளிர் வண்ணங்களுக்காக (Pastel) RGB மதிப்புகளை உயர்த்துதல்
    r = (int(hex_hash[:2], 16) % 128) + 127
    g = (int(hex_hash[2:4], 16) % 128) + 127
    b = (int(hex_hash[4:6], 16) % 128) + 127
    return f'#{r:02x}{g:02x}{b:02x}'

# --- ⚡ FETCH DATA ---
@st.cache_data(ttl=60)
def fetch_teachers():
    res = supabase.table("teachers").select("emis_id, short_name").order("short_name").execute()
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
col_form, col_visual = st.columns([1.5, 1.5])

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
                "teacher_id": e_id,
                "teacher_name": t_name,
                "class_name": c_name,
                "subject_name": s_name,
                "periods_per_week": p_count
            }).execute()
            st.cache_data.clear()
            st.rerun()

    # --- 📋 ஒதுக்கீடு பட்டியல் ---
    if allotment_list:
        st.subheader("📋 ஒதுக்கீடு பட்டியல்")
        df_allot = pd.DataFrame(allotment_list)
        
        df_display = df_allot[['teacher_id', 'teacher_name', 'class_name', 'subject_name', 'periods_per_week']]
        df_display.columns = ['EMIS ID', 'ஆசிரியர்', 'வகுப்பு', 'பாடம்', 'பீரியட்கள்']
        
        # பிழையைத் தவிர்க்க map பயன்படுத்தப்பட்டுள்ளது
        def style_sub(val):
            return f'background-color: {get_color(val)}; color: black; font-weight: bold'
        
        st.dataframe(df_display.style.map(style_sub, subset=['பாடம்']), use_container_width=True, hide_index=True)
        
        with st.expander("🗑️ நீக்குதல்"):
            del_opt = {f"{r['teacher_name']} - {r['class_name']}": r['id'] for r in allotment_list}
            to_del = st.selectbox("தேர்வு செய்க:", ["-- Select --"] + list(del_opt.keys()))
            if st.button("Delete Now") and to_del != "-- Select --":
                supabase.table("staff_allotment").delete().eq("id", del_opt[to_del]).execute()
                st.cache_data.clear()
                st.rerun()

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

    # --- 🎨 Grid Layout (எண்கள் பெரிதாக்கப்பட்டுள்ளது) ---
    cols_per_row = 4
    class_list = list(class_totals.items())
    
    for i in range(0, len(class_list), cols_per_row):
        row_cols = st.columns(cols_per_row)
        for j in range(cols_per_row):
            if i + j < len(class_list):
                cls, total = class_list[i + j]
                bg_color = get_color(cls)
                # 45-க்கு மேல் போனால் பார்டர் தடிமனாக சிவப்பில் வரும்
                border_style = "3px solid #FF4B4B" if total > 45 else f"1px solid #ddd"
                
                row_cols[j].markdown(f"""
                    <div style="
                        background-color: {bg_color};
                        padding: 15px 5px;
                        border-radius: 10px;
                        border: {border_style};
                        text-align: center;
                        margin-bottom: 10px;
                        box-shadow: 2px 2px 5px rgba(0,0,0,0.05);
                    ">
                        <div style="font-size: 16px; font-weight: bold; color: #333; margin-bottom: 5px;">{cls}</div>
                        <div style="font-size: 32px; font-weight: 900; color: #000; line-height: 1;">{total}</div>
                    </div>
                """, unsafe_allow_html=True)
