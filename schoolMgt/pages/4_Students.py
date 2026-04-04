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
st.title("🧑‍🎓 மாணவர் மேலாண்மை (நெகிழ்வான & வரிசைப்படுத்தப்பட்ட முறை)")

# ⚡ தரவுகளைப் பெறுதல் (Caching)
@st.cache_data(ttl=60)
def fetch_data(table_name):
    try:
        response = supabase.table(table_name).select("*").execute()
        return response.data
    except:
        return []

# அடிப்படைத் தரவுகள்
classes_data = fetch_data("classes")
class_list = sorted([c['class_name'] for c in classes_data]) if classes_data else []

# --- தாவல்கள் (Tabs) ---
tab1, tab2 = st.tabs(["📝 தனித்தனியாகச் சேர்க்க", "📤 எக்செல் மூலம் மொத்தமாகச் சேர்க்க"])

# --- Tab 1: ஒரு மாணவரை மட்டும் சேர்த்தல் ---
with tab1:
    with st.form("single_add", clear_on_submit=True):
        st.subheader("🆕 புதிய மாணவர் சேர்க்கை")
        c1, c2, c3, c4 = st.columns([2, 3, 2, 2])
        emis = c1.text_input("EMIS / சேர்க்கை எண்").strip()
        name = c2.text_input("மாணவர் பெயர்").upper().strip()
        gender = c3.selectbox("பாலினம்", ["Male", "Female", "Transgender"])
        s_class = c4.selectbox("வகுப்பு", ["-- தேர்வு செய்க --"] + class_list)
        
        if st.form_submit_button("💾 மாணவரைச் சேமி"):
            if emis and name and s_class != "-- தேர்வு செய்க --":
                try:
                    supabase.table("students").insert({
                        "emis_no": emis, "student_name": name, 
                        "gender": gender, "class_name": s_class
                    }).execute()
                    st.success(f"மாணவர் {name} வெற்றிகரமாகச் சேர்க்கப்பட்டார்!")
                    st.cache_data.clear()
                    st.rerun()
                except Exception as e:
                    st.error(f"பிழை: {e}")
            else:
                st.warning("அனைத்து விபரங்களையும் சரியாகப் பூர்த்தி செய்யவும்.")

# --- Tab 2: Bulk Upload (Excel/CSV) ---
with tab2:
    st.subheader("📤 எக்செல்/CSV கோப்பை பதிவேற்றவும்")
    st.info("தலைப்புகள்: **emis_no, student_name, gender, class_name** (சிறிய எழுத்துக்களில் இருக்க வேண்டும்)")
    
    upload_file = st.file_uploader("கோப்பைத் தேர்ந்தெடுக்கவும்", type=['csv', 'xlsx'])
    
    if upload_file:
        try:
            if upload_file.name.endswith('.csv'):
                df_up = pd.read_csv(upload_file, dtype={'emis_no': str})
            else:
                df_up = pd.read_excel(upload_file, dtype={'emis_no': str})
            
            # தலைப்புகளைச் சிறிய எழுத்துக்களுக்கு மாற்றுதல் (Error Prevention)
            df_up.columns = [c.lower().strip() for c in df_up.columns]
            
            st.write("தரவு மாதிரி:")
            st.dataframe(df_up.head())
            
            if st.button("🚀 அனைத்தையும் பதிவேற்று"):
                with st.spinner("சேமிக்கப்படுகிறது..."):
                    for col in df_up.columns:
                        df_up[col] = df_up[col].astype(str).str.strip()
                    
                    if 'student_name' in df_up.columns:
                        df_up['student_name'] = df_up['student_name'].str.upper()
                    
                    data_list = df_up.to_dict(orient='records')
                    supabase.table("students").insert(data_list).execute()
                    
                    st.success(f"{len(data_list)} மாணவர்கள் சேர்க்கப்பட்டனர்!")
                    st.cache_data.clear()
                    st.rerun()
        except Exception as e:
            st.error(f"பதிவேற்றுவதில் பிழை: {e}")

st.divider()

# --- 2. மாணவர் பட்டியல் & வரிசைப்படுத்துதல் ---
students_data = fetch_data("students")
if students_data:
    df_main = pd.DataFrame(students_data)
    st.subheader("📋 மாணவர் பட்டியல்")
    
    # தேடுதல் மற்றும் வடிகட்டிகள்
    col_f1, col_f2 = st.columns([2, 1])
    search = col_f1.text_input("பெயர் அல்லது எண் மூலம் தேடுக:")
    f_class = col_f2.selectbox("வகுப்பு வாரியாகப் பார்க்க:", ["All"] + class_list)
    
    # 1. வடித்தல் (Filtering)
    final_df = df_main.copy()
    if f_class != "All":
        final_df = final_df[final_df['class_name'] == f_class]
    if search:
        final_df = final_df[
            final_df['student_name'].str.contains(search.upper(), na=False) | 
            final_df['emis_no'].str.contains(search, na=False)
        ]

    # 2. வரிசைப்படுத்துதல் (Sorting) - முக்கியமான மாற்றம்
    # முன்னுரிமை: 1.வகுப்பு, 2.பாலினம், 3.பெயர்
    final_df = final_df.sort_values(
        by=['class_name', 'gender', 'student_name'], 
        ascending=[True, True, True]
    )
    
    # 3. அட்டவணையாகக் காட்டுதல்
    st.info(f"காண்பிக்கப்படும் மாணவர்கள் எண்ணிக்கை: {len(final_df)}")
    st.dataframe(
        final_df[['emis_no', 'student_name', 'gender', 'class_name']], 
        use_container_width=True, 
        hide_index=True
    )

    # --- 3. திருத்துதல் / நீக்குதல் ---
    st.divider()
    st.subheader("⚙️ மேலாண்மை (Edit/Delete)")
    # EMIS மற்றும் பெயரை இணைத்துத் தேர்வுப் பட்டியலாகக் காட்டுதல்
    edit_options = final_df.apply(lambda x: f"{x['emis_no']} - {x['student_name']}", axis=1).tolist()
    sel_st = st.selectbox("மாணவரைத் தேர்வு செய்க:", ["-- தேர்வு செய்க --"] + edit_options)
    
    if sel_st != "-- தேர்வு செய்க --":
        s_emis = sel_st.split(" - ")[0]
        s_row = df_main[df_main['emis_no'] == s_emis].iloc[0]
        
        ce1, ce2 = st.columns(2)
        with ce1:
            new_n = st.text_input("புதிய பெயர்:", value=s_row['student_name']).upper()
            new_c = st.selectbox("புதிய வகுப்பு:", class_list, 
                                index=class_list.index(s_row['class_name']) if s_row['class_name'] in class_list else 0)
            if st.button("🆙 Update"):
                supabase.table("students").update({"student_name": new_n, "class_name": new_c}).eq("emis_no", s_emis).execute()
                st.success("விபரங்கள் மாற்றப்பட்டன!")
                st.cache_data.clear()
                st.rerun()
        
        with ce2:
            st.write("⚠️ மாணவரை நீக்க")
            if st.button(f"❌ {s_emis}-ஐ நீக்கு", type="primary"):
                supabase.table("students").delete().eq("emis_no", s_emis).execute()
                st.warning("மாணவர் நீக்கப்பட்டார்!")
                st.cache_data.clear()
                st.rerun()
else:
    st.info("மாணவர்கள் விபரங்கள் இன்னும் இல்லை.")
