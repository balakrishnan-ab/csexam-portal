import streamlit as st
import pandas as pd
from supabase import create_client, Client

# 1. Supabase இணைப்பு
try:
    url: str = st.secrets["SUPABASE_URL"]
    key: str = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(url, key)
except Exception as e:
    st.error("Secrets-ல் Supabase விவரங்கள் சரியாக இல்லை!")
    st.stop()

st.set_page_config(page_title="Student Management", layout="wide")
st.title("🧑‍🎓 மாணவர் மேலாண்மை (நெகிழ்வான முறை)")

# ⚡ தரவுகளைப் பெறுதல்
@st.cache_data(ttl=60)
def fetch_data(table_name):
    try:
        response = supabase.table(table_name).select("*").execute()
        return response.data
    except:
        return []

classes_data = fetch_data("classes")
class_list = sorted([c['class_name'] for c in classes_data]) if classes_data else []

# --- தாவல்கள் (Tabs) ---
tab1, tab2 = st.tabs(["📝 தனித்தனியாகச் சேர்க்க", "📤 எக்செல் மூலம் மொத்தமாக (Bulk Upload)"])

# --- Tab 1: தனித்தனி சேர்க்கை ---
with tab1:
    with st.form("single_add", clear_on_submit=True):
        st.subheader("🆕 புதிய மாணவர்")
        c1, c2, c3, c4 = st.columns([2, 3, 2, 2])
        emis = c1.text_input("EMIS / சேர்க்கை எண்").strip()
        name = c2.text_input("மாணவர் பெயர்").upper().strip()
        gender = c3.selectbox("பாலினம்", ["Male", "Female", "Transgender"])
        s_class = c4.selectbox("வகுப்பு", ["-- தேர்வு செய்க --"] + class_list)
        
        if st.form_submit_button("💾 சேமி"):
            if emis and name and s_class != "-- தேர்வு செய்க --":
                try:
                    # இங்கே காலம்கள் கண்டிப்பாக சிறிய எழுத்தில் (lowercase) இருக்க வேண்டும்
                    supabase.table("students").insert({
                        "emis_no": emis, 
                        "student_name": name, 
                        "gender": gender, 
                        "class_name": s_class
                    }).execute()
                    st.success(f"{name} வெற்றிகரமாகச் சேர்க்கப்பட்டார்!")
                    st.cache_data.clear()
                    st.rerun()
                except Exception as e:
                    st.error(f"பிழை: {e}")
            else:
                st.warning("அனைத்து விபரங்களையும் பூர்த்தி செய்யவும்.")

# --- Tab 2: Bulk Upload (Excel/CSV) ---
with tab2:
    st.subheader("📤 எக்செல் அல்லது CSV கோப்பை பதிவேற்றவும்")
    st.info("கோப்பில் இருக்க வேண்டிய தலைப்புகள்: **emis_no, student_name, gender, class_name**")
    
    upload_file = st.file_uploader("கோப்பைத் தேர்ந்தெடுக்கவும்", type=['csv', 'xlsx'])
    
    if upload_file:
        try:
            # கோப்பை வாசித்தல்
            if upload_file.name.endswith('.csv'):
                df_up = pd.read_csv(upload_file, dtype={'emis_no': str})
            else:
                df_up = pd.read_excel(upload_file, dtype={'emis_no': str})
            
            # முக்கியமான பகுதி: தலைப்புகளைச் சிறிய எழுத்துக்களுக்கு மாற்றுதல் (PGRST204 பிழையைத் தவிர்க்க)
            df_up.columns = [c.lower().strip() for c in df_up.columns]
            
            st.write("தரவு மாதிரி (Preview):")
            st.dataframe(df_up.head())
            
            if st.button("🚀 அனைத்தையும் பதிவேற்று"):
                with st.spinner("பதிவேற்றப்படுகிறது..."):
                    # தரவைச் சுத்தம் செய்தல் (Space நீக்குதல் மற்றும் Capitalize செய்தல்)
                    for col in df_up.columns:
                        df_up[col] = df_up[col].astype(str).str.strip()
                    
                    if 'student_name' in df_up.columns:
                        df_up['student_name'] = df_up['student_name'].str.upper()
                    
                    # அகராதியாக (Dictionary) மாற்றிச் சேர்த்தல்
                    data_list = df_up.to_dict(orient='records')
                    supabase.table("students").insert(data_list).execute()
                    
                    st.success(f"வாழ்த்துக்கள்! {len(data_list)} மாணவர்கள் சேர்க்கப்பட்டனர்.")
                    st.cache_data.clear()
                    st.rerun()
        except Exception as e:
            st.error(f"பதிவேற்றுவதில் பிழை: {e}")
            st.info("உங்கள் எக்செல் கோப்பில் தலைப்புகள் (Headers) சரியாக இருப்பதை உறுதி செய்யவும்.")

st.divider()

# --- 2. மாணவர் பட்டியல் ---
students_data = fetch_data("students")
if students_data:
    df = pd.DataFrame(students_data)
    st.subheader("📋 மாணவர் பட்டியல்")
    
    col_f1, col_f2 = st.columns([2, 1])
    search = col_f1.text_input("பெயர் அல்லது எண் மூலம் தேடுக:")
    f_class = col_f2.selectbox("வகுப்பு வடிகட்டி:", ["All"] + class_list)
    
    final_df = df.copy()
    if f_class != "All":
        final_df = final_df[final_df['class_name'] == f_class]
    if search:
        final_df = final_df[
            final_df['student_name'].str.contains(search.upper(), na=False) | 
            final_df['emis_no'].str.contains(search, na=False)
        ]
    
    st.dataframe(
        final_df[['emis_no', 'student_name', 'gender', 'class_name']].sort_values('student_name'), 
        use_container_width=True, hide_index=True
    )

    # --- 3. திருத்துதல் / நீக்குதல் ---
    st.divider()
    st.subheader("⚙️ மேலாண்மை")
    edit_list = final_df.apply(lambda x: f"{x['emis_no']} - {x['student_name']}", axis=1).tolist()
    sel_st = st.selectbox("மாணவரைத் தேர்வு செய்க:", ["-- தேர்வு செய்க --"] + edit_list)
    
    if sel_st != "-- தேர்வு செய்க --":
        s_emis = sel_st.split(" - ")[0]
        s_row = df[df['emis_no'] == s_emis].iloc[0]
        
        ce1, ce2 = st.columns(2)
        with ce1:
            new_n = st.text_input("புதிய பெயர்:", value=s_row['student_name']).upper()
            new_c = st.selectbox("புதிய வகுப்பு:", class_list, index=class_list.index(s_row['class_name']) if s_row['class_name'] in class_list else 0)
            if st.button("🆙 Update"):
                supabase.table("students").update({"student_name": new_n, "class_name": new_c}).eq("emis_no", s_emis).execute()
                st.success("மாற்றப்பட்டது!")
                st.cache_data.clear()
                st.rerun()
        with ce2:
            if st.button(f"❌ {s_emis}-ஐ நீக்கு", type="primary"):
                supabase.table("students").delete().eq("emis_no", s_emis).execute()
                st.warning("நீக்கப்பட்டது!")
                st.cache_data.clear()
                st.rerun()
else:
    st.info("மாணவர்கள் விபரங்கள் இன்னும் இல்லை.")
