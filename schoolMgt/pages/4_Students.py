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
st.title("🧑‍🎓 மாணவர் மேலாண்மை & இனம் சார்ந்த புள்ளிவிவரம்")

# விரிவான இனப்பிரிவுகள் (Community Options)
COMMUNITY_OPTIONS = [
    "Hindu BC-Others", "Hindu MBC", "Hindu DNC", "Hindu SC-Others",
    "Hindu SC-Arunthathiyar (SCA)", "Hindu ST", "Hindu OC",
    "Muslim BC-Muslim (BCM)", "Muslim MBC", "Muslim SC-Others",
    "Muslim ST", "Muslim OC", "Christian BC", "Christian MBC",
    "Christian SC-Others", "Christian ST"
]

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

# --- Tab 1: புதிய மாணவர் சேர்க்கை ---
with tab1:
    with st.form("single_add", clear_on_submit=True):
        st.subheader("🆕 புதிய மாணவர் சேர்க்கை")
        c1, c2 = st.columns(2)
        emis = c1.text_input("EMIS / சேர்க்கை எண்").strip()
        name = c2.text_input("மாணவர் பெயர்").upper().strip()
        
        c3, c4, c5 = st.columns(3)
        gender = c3.selectbox("பாலினம்", ["Male", "Female", "Transgender"])
        s_class = c4.selectbox("வகுப்பு", ["-- தேர்வு செய்க --"] + class_list)
        community = c5.selectbox("இனம் (Community)", ["-- தேர்வு செய்க --"] + COMMUNITY_OPTIONS)
        
        if st.form_submit_button("💾 மாணவரைச் சேமி"):
            if emis and name and s_class != "-- தேர்வு செய்க --" and community != "-- தேர்வு செய்க --":
                try:
                    supabase.table("students").insert({
                        "emis_no": emis, 
                        "student_name": name, 
                        "gender": gender, 
                        "class_name": s_class,
                        "community": community
                    }).execute()
                    st.success(f"மாணவர் {name} வெற்றிகரமாகச் சேர்க்கப்பட்டார்!")
                    st.cache_data.clear()
                    st.rerun()
                except Exception as e:
                    st.error(f"பிழை: {e}")
            else:
                st.warning("அனைத்து விபரங்களையும் (இனம் உட்பட) பூர்த்தி செய்யவும்.")

# --- Tab 2: Bulk Upload ---
with tab2:
    st.subheader("📤 எக்செல்/CSV மூலம் மொத்தமாகப் பதிவேற்றவும்")
    st.info("தலைப்புகள்: **emis_no, student_name, gender, class_name, community**")
    
    upload_file = st.file_uploader("கோப்பைத் தேர்ந்தெடுக்கவும்", type=['csv', 'xlsx'])
    
    if upload_file:
        try:
            df_up = pd.read_csv(upload_file, dtype={'emis_no': str}) if upload_file.name.endswith('.csv') else pd.read_excel(upload_file, dtype={'emis_no': str})
            df_up.columns = [c.lower().strip() for c in df_up.columns]
            
            if st.button("🚀 அனைத்தையும் பதிவேற்று"):
                with st.spinner("சேமிக்கப்படுகிறது..."):
                    # தரவு சுத்தம் செய்தல்
                    for col in df_up.columns:
                        df_up[col] = df_up[col].astype(str).str.strip()
                    if 'student_name' in df_up.columns: df_up['student_name'] = df_up['student_name'].str.upper()
                    
                    data_list = df_up.to_dict(orient='records')
                    supabase.table("students").insert(data_list).execute()
                    st.success(f"{len(data_list)} மாணவர்கள் சேர்க்கப்பட்டனர்!")
                    st.cache_data.clear()
                    st.rerun()
        except Exception as e:
            st.error(f"பதிவேற்றுவதில் பிழை: {e}")

st.divider()

# --- மாணவர் பட்டியல் & வடிகட்டிகள் ---
students_data = fetch_data("students")
if students_data:
    df_main = pd.DataFrame(students_data)
    st.subheader("📋 மாணவர் பட்டியல்")
    
    col_f1, col_f2, col_f3 = st.columns([2, 1, 1])
    search = col_f1.text_input("தேடுக (பெயர்/எண்):")
    f_class = col_f2.selectbox("வகுப்பு:", ["All"] + class_list)
    f_comm = col_f3.selectbox("இனம்:", ["All"] + COMMUNITY_OPTIONS)
    
    # Filtering
    final_df = df_main.copy()
    if f_class != "All": final_df = final_df[final_df['class_name'] == f_class]
    if f_comm != "All": final_df = final_df[final_df['community'] == f_comm]
    if search:
        final_df = final_df[final_df['student_name'].str.contains(search.upper(), na=False) | final_df['emis_no'].str.contains(search, na=False)]

    # Sorting
    final_df = final_df.sort_values(by=['class_name', 'student_name'])
    
    st.dataframe(final_df[['emis_no', 'student_name', 'gender', 'class_name', 'community']], use_container_width=True, hide_index=True)

    # --- திருத்துதல் பகுதி ---
    st.divider()
    st.subheader("⚙️ மேலாண்மை (Edit/Delete)")
    edit_list = final_df.apply(lambda x: f"{x['emis_no']} - {x['student_name']}", axis=1).tolist()
    sel_st = st.selectbox("மாணவரைத் தேர்வு செய்க:", ["-- தேர்வு செய்க --"] + edit_list)
    
    if sel_st != "-- தேர்வு செய்க --":
        s_emis = sel_st.split(" - ")[0]
        s_row = df_main[df_main['emis_no'] == s_emis].iloc[0]
        
        ce1, ce2 = st.columns(2)
        with ce1:
            new_n = st.text_input("பெயர்:", value=s_row['student_name']).upper()
            new_c = st.selectbox("வகுப்பு:", class_list, index=class_list.index(s_row['class_name']) if s_row['class_name'] in class_list else 0)
            
            # Community Update
            curr_comm = s_row.get('community', "")
            new_comm = st.selectbox("இனம்:", COMMUNITY_OPTIONS, 
                                   index=COMMUNITY_OPTIONS.index(curr_comm) if curr_comm in COMMUNITY_OPTIONS else 0)
            
            if st.button("🆙 Update"):
                supabase.table("students").update({"student_name": new_n, "class_name": new_c, "community": new_comm}).eq("emis_no", s_emis).execute()
                st.success("வெற்றிகரமாக மாற்றப்பட்டது!")
                st.cache_data.clear()
                st.rerun()
        with ce2:
            if st.button(f"❌ {s_emis}-ஐ நீக்கு", type="primary"):
                supabase.table("students").delete().eq("emis_no", s_emis).execute()
                st.cache_data.clear()
                st.rerun()
