import streamlit as st
from supabase import create_client, Client
import pandas as pd

# 1. Supabase இணைப்பு (Secrets-ல் இருந்து URL மற்றும் Key-ஐ எடுக்கும்)
try:
    url: str = st.secrets["SUPABASE_URL"]
    key: str = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(url, key)
except Exception as e:
    st.error("Supabase இணைப்பு தகவல்கள் Secrets-ல் இல்லை!")
    st.stop()

st.set_page_config(page_title="Student Management", layout="wide")

st.title("🧑‍🎓 மாணவர் மேலாண்மை (Supabase)")

# ⚡ தரவுகளை வேகமாகப் பெறுதல் (Caching)
@st.cache_data(ttl=60)
def fetch_data(table_name):
    try:
        response = supabase.table(table_name).select("*").execute()
        return response.data
    except Exception as e:
        st.error(f"{table_name} தரவைப் பெறுவதில் பிழை: {e}")
        return []

# தேவையான தரவுகளைப் பெறுதல்
students_data = fetch_data("students")
classes_data = fetch_data("classes")

# வகுப்புகளை மட்டும் அகரவரிசைப்படி பட்டியலிடுதல்
class_list = sorted([c['class_name'] for c in classes_data]) if classes_data else []

# --- 1. புதிய மாணவர் சேர்க்கும் படிவம் ---
with st.form("add_student_form", clear_on_submit=True):
    st.subheader("🆕 புதிய மாணவர் சேர்க்கை")
    c1, c2, c3, c4 = st.columns([2, 3, 2, 2])
    
    # 13 இலக்க EMIS எண் கட்டுப்பாடு
    emis = c1.text_input("EMIS எண் (13 Digits)", max_chars=13, help="சரியாக 13 இலக்க எண்களை உள்ளிடவும்").strip()
    sname = c2.text_input("மாணவர் பெயர்").upper().strip()
    gender = c3.selectbox("பாலினம்", ["Male", "Female", "Transgender"])
    s_class = c4.selectbox("வகுப்பு", ["-- தேர்வு செய்க --"] + class_list)
    
    if st.form_submit_button("💾 மாணவரைச் சேமி"):
        # முக்கியமான சரிபார்ப்புகள்
        if not emis.isdigit() or len(emis) != 13:
            st.error("❌ பிழை: EMIS எண் சரியாக 13 இலக்க எண்களாக இருக்க வேண்டும்!")
        elif sname == "" or s_class == "-- தேர்வு செய்க --":
            st.warning("⚠️ மாணவர் பெயர் மற்றும் வகுப்பைச் சரியாக உள்ளிடவும்.")
        else:
            try:
                supabase.table("students").insert({
                    "emis_no": emis,
                    "student_name": sname,
                    "gender": gender,
                    "class_name": s_class
                }).execute()
                st.success(f"மாணவர் '{sname}' வெற்றிகரமாகச் சேர்க்கப்பட்டார்!")
                st.cache_data.clear()
                st.rerun()
            except Exception as e:
                if "duplicate key" in str(e):
                    st.error(f"❌ பிழை: EMIS எண் {emis} ஏற்கனவே பதிவு செய்யப்பட்டுள்ளது!")
                else:
                    st.error(f"பதிவு செய்வதில் பிழை: {e}")

st.divider()

# --- 2. மாணவர் பட்டியல் & தேடுதல் வசதி ---
if students_data:
    df = pd.DataFrame(students_data)
    
    st.subheader("📋 மாணவர் பட்டியல்")
    
    # தேடுதல் மற்றும் வடிகட்டுதல் (Filter)
    f1, f2 = st.columns([2, 1])
    search_query = f1.text_input("பெயர் அல்லது EMIS மூலம் தேடுக:", placeholder="பெயரைத் தட்டச்சு செய்க...")
    filter_class = f2.selectbox("வகுப்பு வாரியாக வடிகட்ட:", ["All"] + class_list)
    
    # வடிகட்டும் லாஜிக் (Filtering Logic)
    filtered_df = df.copy()
    if filter_class != "All":
        filtered_df = filtered_df[filtered_df['class_name'] == filter_class]
    if search_query:
        filtered_df = filtered_df[
            filtered_df['student_name'].str.contains(search_query.upper()) | 
            filtered_df['emis_no'].contains(search_query)
        ]
        
    st.info(f"காண்பிக்கப்படும் மாணவர்கள் எண்ணிக்கை: {len(filtered_df)}")
    
    # அட்டவணையாகக் காட்டுதல்
    st.dataframe(
        filtered_df[['emis_no', 'student_name', 'gender', 'class_name']].sort_values('student_name'), 
        use_container_width=True, 
        hide_index=True
    )

    st.divider()

    # --- 3. திருத்துதல் மற்றும் நீக்குதல் ---
    st.subheader("⚙️ மாணவர் விபரங்களை மாற்றியமைக்க / நீக்க")
    
    # மாணவரைத் தேர்வு செய்தல்
    student_list = filtered_df.apply(lambda x: f"{x['emis_no']} - {x['student_name']}", axis=1).tolist()
    sel_student = st.selectbox("நிர்வகிக்க வேண்டிய மாணவரைத் தேர்வு செய்க:", ["-- தேர்வு செய்க --"] + student_list)

    if sel_student != "-- தேர்வு செய்க --":
        selected_emis = sel_student.split(" - ")[0]
        old_data = df[df['emis_no'] == selected_emis].iloc[0]
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("#### 📝 விபரங்களை மாற்ற")
            u_name = st.text_input("புதிய பெயர்:", value=old_data['student_name']).upper().strip()
            u_gender = st.selectbox("புதிய பாலினம்:", ["Male", "Female", "Transgender"], 
                                   index=["Male", "Female", "Transgender"].index(old_data['gender']))
            u_class = st.selectbox("புதிய வகுப்பு:", class_list, 
                                  index=class_list.index(old_data['class_name']) if old_data['class_name'] in class_list else 0)
            
            if st.button("🆙 இற்றைப்படுத்து (Update)"):
                try:
                    supabase.table("students").update({
                        "student_name": u_name,
                        "gender": u_gender,
                        "class_name": u_class
                    }).eq("emis_no", selected_emis).execute()
                    st.success("விபரங்கள் வெற்றிகரமாக மாற்றப்பட்டன!")
                    st.cache_data.clear()
                    st.rerun()
                except Exception as e:
                    st.error(f"மாற்றுவதில் பிழை: {e}")

        with col2:
            st.markdown("#### ❌ மாணவரை நீக்க")
            st.warning(f"எச்சரிக்கை: {old_data['student_name']} என்பவரை நீக்கப் போகிறீர்கள்.")
            confirm_del = st.checkbox("நான் இவரை நிரந்தரமாக நீக்க விரும்புகிறேன்")
            if confirm_del:
                if st.button(f"உறுதியாக நீக்கு", type="primary"):
                    try:
                        supabase.table("students").delete().eq("emis_no", selected_emis).execute()
                        st.warning("மாணவர் நீக்கப்பட்டார்!")
                        st.cache_data.clear()
                        st.rerun()
                    except Exception as e:
                        st.error(f"நீக்குவதில் பிழை: {e}")
else:
    st.info("மாணவர்கள் விபரங்கள் இன்னும் சேர்க்கப்படவில்லை.")
