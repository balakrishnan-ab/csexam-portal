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
    """பெயரை அடிப்படையாகக் கொண்டு ஒரு நிலையான வண்ணத்தை (Hex Code) உருவாக்கும்"""
    hash_object = hashlib.md5(text.encode())
    hex_hash = hash_object.hexdigest()
    # அடர் வண்ணங்களைத் தவிர்க்க வெளிர் வண்ணங்களாக (Pastel Colors) மாற்றுதல்
    color = f"#{hex_hash[:6]}"
    return color

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

st.title("👨‍🏫 ஆசிரியர் பாடவேளை ஒதுக்கீடு")

# --- 📐 LAYOUT ---
col_form, col_visual = st.columns([1.6, 1.4])

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
        
        # அட்டவணையில் பாடங்களுக்கு நிலையான வண்ணம் பூசுதல்
        def highlight_subjects(val):
            color = get_color(val)
            return f'background-color: {color}; color: black; font-weight: bold'

        df_display = df_allot[['teacher_id', 'teacher_name', 'class_name', 'subject_name', 'periods_per_week']]
        df_display.columns = ['EMIS ID', 'ஆசிரியர்', 'வகுப்பு', 'பாடம்', 'பீரியட்கள்']
        
        st.dataframe(df_display.style.applymap(highlight_subjects, subset=['பாடம்']), use_container_width=True, hide_index=True)
        
        with st.expander("🗑️ நீக்குதல்"):
            del_opt = {f"{r['teacher_name']} - {r['class_name']} ({r['subject_name']})": r['id'] for r in allotment_list}
            to_del = st.selectbox("தேர்வு செய்க:", ["-- Select --"] + list(del_opt.keys()))
            if st.button("Delete Now") and to_del != "-- Select --":
                supabase.table("staff_allotment").delete().eq("id", del_opt[to_del]).execute()
                st.cache_data.clear()
                st.rerun()

with col_visual:
    st.subheader("🏫 வகுப்பு வாரியான பாடவேளைகள்")
    
    # --- 🧮 கணக்கீடு ---
    class_totals = {c: 0 for c in base_classes}
    for entry in allotment_list:
        target = entry['class_name']
        periods = entry['periods_per_week']
        if target in comb_groups:
            for sub_class in comb_groups[target]:
                if sub_class in class_totals: class_totals[sub_class] += periods
        elif target in class_totals:
            class_totals[target] += periods

    # --- 🎨 Grid Layout (1 வரிசைக்கு 4 முதல் 6 வகுப்புகள்) ---
    cols_per_row = 5 
    class_list = list(class_totals.items())
    
    for i in range(0, len(class_list), cols_per_row):
        row_cols = st.columns(cols_per_row)
        for j in range(cols_per_row):
            if i + j < len(class_list):
                cls, total = class_list[i + j]
                
                # வகுப்பிற்கான நிலையான வண்ணம்
                bg_color = get_color(cls)
                # 45-க்கு மேல் போனால் பார்டர் சிவப்பாக மாறும்
                border_style = "3px solid red" if total > 45 else f"1px solid {bg_color}"
                
                row_cols[j].markdown(f"""
                    <div style="
                        background-color: {bg_color};
                        padding: 10px;
                        border-radius: 8px;
                        border: {border_style};
                        text-align: center;
                        margin-bottom: 10px;
                        box-shadow: 2px 2px 5px rgba(0,0,0,0.1);
                    ">
                        <div style="font-size: 14px; font-weight: bold; color: black;">{cls}</div>
                        <div style="font-size: 22px; font-weight: 900; color: black;">{total}</div>
                    </div>
                """, unsafe_allow_html=True)
