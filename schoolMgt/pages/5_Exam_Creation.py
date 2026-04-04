import streamlit as st
import pandas as pd
from supabase import create_client, Client

# 1. Supabase இணைப்பு
try:
    url: str = st.secrets["SUPABASE_URL"]
    key: str = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(url, key)
except Exception as e:
    st.error("Secrets-ல் Supabase விவரங்கள் சரியாக இல்லை! தயவுசெய்து சரிபார்க்கவும்.")
    st.stop()

st.set_page_config(page_title="Exam Management", layout="wide")
st.title("🏆 தேர்வு உருவாக்கம் (Exam Creation)")

# ⚡ தரவுகளைப் பெறுதல் (Caching)
@st.cache_data(ttl=60)
def fetch_exams():
    try:
        # ID அடிப்படையில் இறங்கு வரிசையில் (Newest first) தரவுகளை எடுத்தல்
        response = supabase.table("exams").select("*").order("id", desc=True).execute()
        return response.data
    except Exception as e:
        return []

# --- 1. புதிய தேர்வை உருவாக்குதல் ---
with st.form("create_exam_form", clear_on_submit=True):
    st.subheader("🆕 புதிய தேர்வைச் சேர்த்தல்")
    
    col1, col2 = st.columns(2)
    with col1:
        e_name = st.text_input("தேர்வின் பெயர்", placeholder="எ.கா: Quarterly Exam 2026")
    with col2:
        a_year = st.selectbox("கல்வி ஆண்டு", ["2025-26", "2026-27", "2027-28"])
    
    # எந்தெந்த வகுப்புகளுக்கு இந்தத் தேர்வு பொருந்தும்?
    st.markdown("**இந்தத் தேர்வு எந்த வகுப்புகளுக்குப் பொருந்தும்?**")
    all_classes = ["6", "7", "8", "9", "10", "11", "12"]
    selected_classes = st.multiselect("வகுப்புகளைத் தேர்வு செய்க:", all_classes, default=all_classes)
    
    if st.form_submit_button("💾 தேர்வை உருவாக்கு"):
        if e_name and selected_classes:
            try:
                # வகுப்புகளை ஒரு கமாவால் பிரிக்கப்பட்ட வரியாக (String) மாற்றுதல்
                classes_str = ", ".join(selected_classes)
                
                supabase.table("exams").insert({
                    "exam_name": e_name,
                    "academic_year": a_year,
                    "applicable_classes": classes_str,
                    "exam_status": "Active"
                }).execute()
                
                st.success(f"'{e_name}' வெற்றிகரமாக உருவாக்கப்பட்டது!")
                st.cache_data.clear() # Cache-ஐ அழித்து புதிய தரவைக் காட்ட
                st.rerun()
            except Exception as e:
                st.error(f"பதிவு செய்வதில் பிழை: {e}")
        else:
            st.warning("தேர்வின் பெயர் மற்றும் குறைந்தது ஒரு வகுப்பையாவது தேர்ந்தெடுக்கவும்.")

st.divider()

# --- 2. உருவாக்கப்பட்ட தேர்வுகளின் பட்டியல் ---
exams_data = fetch_exams()

if exams_data:
    st.subheader("📋 உருவாக்கப்பட்ட தேர்வுகள்")
    df_exams = pd.DataFrame(exams_data)
    
    # அட்டவணையில் காட்ட வேண்டிய காலம்கள்
    # 'id' என்பது Primary Key, இது வரிசைப்படுத்த உதவும்
    display_df = df_exams[['id', 'exam_name', 'academic_year', 'applicable_classes', 'exam_status']]
    display_df.columns = ['ID', 'தேர்வின் பெயர்', 'கல்வி ஆண்டு', 'வகுப்புகள்', 'நிலை (Status)']
    
    st.dataframe(display_df, use_container_width=True, hide_index=True)

    st.divider()

    # --- 3. தேர்வு மேலாண்மை (Status Update / Delete) ---
    st.subheader("⚙️ தேர்வு மேலாண்மை (Edit/Delete)")
    
    # ID மற்றும் பெயரை இணைத்துத் தேர்வுப் பட்டியலை உருவாக்குதல்
    exam_options = {f"{e['id']} - {e['exam_name']}": e['id'] for e in exams_data}
    selected_label = st.selectbox("நிர்வகிக்க வேண்டிய தேர்வைத் தேர்வு செய்க:", 
                                  ["-- தேர்வு செய்க --"] + list(exam_options.keys()))
    
    if selected_label != "-- தேர்வு செய்க --":
        selected_id = exam_options[selected_label]
        
        col_m1, col_m2 = st.columns(2)
        
        with col_m1:
            st.info("🔄 நிலையை மாற்ற (Status)")
            # தற்போதைய நிலையைப் பெறுதல்
            current_status = df_exams[df_exams['id'] == selected_id]['exam_status'].values[0]
            new_status = st.radio("புதிய நிலை:", ["Active", "Completed"], 
                                 index=0 if current_status == "Active" else 1)
            
            if st.button("🆙 நிலையை இப்போதே மாற்று"):
                supabase.table("exams").update({"exam_status": new_status}).eq("id", selected_id).execute()
                st.success(f"தேர்வு நிலை '{new_status}' என மாற்றப்பட்டது!")
                st.cache_data.clear()
                st.rerun()
                
        with col_m2:
            st.warning("⚠️ ஆபத்தான பகுதி (Delete)")
            st.write("இந்தத் தேர்வை நீக்கினால், இதனுடன் தொடர்புடைய அனைத்து மதிப்பெண்களும் நீக்கப்படும்!")
            if st.button(f"❌ {selected_label}-ஐ நீக்கு", type="primary"):
                # ID-ஐ வைத்து நீக்குவதுதான் மிகவும் பாதுகாப்பானது
                supabase.table("exams").delete().eq("id", selected_id).execute()
                st.error("தேர்வு நீக்கப்பட்டது!")
                st.cache_data.clear()
                st.rerun()
else:
    st.info("இன்னும் தேர்வுகள் எதுவும் உருவாக்கப்படவில்லை. மேலே உள்ள படிவத்தைப் பயன்படுத்தி ஒரு தேர்வை உருவாக்கவும்.")5_Exam_Creation.py
