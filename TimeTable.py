import streamlit as st
import pandas as pd

# பக்க வடிவமைப்பு
st.set_page_config(page_title="GHSS Exam Portal", layout="wide")
st.title("📅 பள்ளித் தேர்வு கால அட்டவணை போர்ட்டல் - 2026")

# --- 1. ஆசிரியர்கள் மற்றும் பாடங்களின் தரவுத்தளம் (Mapping) ---
# நீங்கள் கொடுத்த PDF தரவுகளின் அடிப்படையில் உருவாக்கப்பட்டது
TEACHER_MAP = {
    "A. Balakrishnan (AB)": "AB",
    "K. Vanitha (KV)": "KV",
    "R. Vasanthi (RV)": "RV",
    "T. Sudha (TS)": "TS",
    "A. Sathya (AS)": "AS",
    "M. Angamuthu (MA)": "MA",
    "M. Revathi (MR)": "MR"
}

# --- 2. மாதிரி அட்டவணை தரவுத்தொகுப்பு (PDF-ல் இருந்து பிரிக்கப்பட்ட வடிவம்) ---
# (பயனர் எளிதாகத் தேட, உங்கள் PDF-ல் உள்ள முக்கியத் தரவுகள் இங்கே உள்ளீடு செய்யப்பட்டுள்ளன)
@st.cache_data
def load_timetable_data():
    # முற்பகல்/பிற்பகல் மற்றும் பீரியட் வாரியான முழு விவரங்கள்
    records = [
        # 12-A வகுப்பு விவரங்கள் (மூலம்: class.pdf)
        {"Day": "Mo", "Class": "12-A", "Period": "1", "Subject": "English", "Staff": "MA"},
        {"Day": "Mo", "Class": "12-A", "Period": "2", "Subject": "Maths", "Staff": "AL"},
        {"Day": "Mo", "Class": "12-A", "Period": "3", "Subject": "Chemistry", "Staff": "RV"},
        {"Day": "Mo", "Class": "12-A", "Period": "4", "Subject": "Physics", "Staff": "KV"},
        {"Day": "Mo", "Class": "12-A", "Period": "5", "Subject": "Computer Science", "Staff": "AB"},
        {"Day": "Mo", "Class": "12-A", "Period": "6", "Subject": "Tamil", "Staff": "MR"},
        
        # 12-C வகுப்பு விவரங்கள் (மூலம்: class.pdf)
        {"Day": "Mo", "Class": "12-C", "Period": "1", "Subject": "Accountancy", "Staff": "SVL"},
        {"Day": "Mo", "Class": "12-C", "Period": "2", "Subject": "Computer Applications", "Staff": "AB"},
        {"Day": "Mo", "Class": "12-C", "Period": "3", "Subject": "Economics", "Staff": "TS"},
        {"Day": "Mo", "Class": "12-C", "Period": "4", "Subject": "Commerce", "Staff": "SVL"},
        
        # செவ்வாய்க்கிழமை விவரங்கள்
        {"Day": "Tu", "Class": "12-A", "Period": "2", "Subject": "Computer Science", "Staff": "AB"},
        {"Day": "Tu", "Class": "12-C", "Period": "3", "Subject": "Computer Applications", "Staff": "AB"},
        {"Day": "We", "Class": "11-A", "Period": "2", "Subject": "Computer Science", "Staff": "AB"},
        {"Day": "Th", "Class": "12-A", "Period": "3", "Subject": "Computer Science", "Staff": "AB"},
        {"Day": "Fr", "Class": "12-A", "Period": "4", "Subject": "Computer Science", "Staff": "AB"},
    ]
    return pd.DataFrame(records)

df_master = load_timetable_data()

# --- 3. பயனர் இடைமுகம் (Tabs) ---
tab1, tab2 = st.tabs(["👨‍🏫 ஆசிரியர் வாரியான தேடல்", "📚 வகுப்பு வாரியான தேடல்"])

# --- TAB 1: ஆசிரியர் தேடல் ---
with tab1:
    st.header("ஆசிரியர்களின் தேர்வுப் பணி விவரங்கள்")
    
    selected_teacher_name = st.selectbox(
        "ஆசிரியர் பெயரைத் தேர்ந்தெடுக்கவும்:", 
        ["தேர்ந்தெடுக்கவும்..."] + list(TEACHER_MAP.keys())
    )
    
    if selected_teacher_name != "தேர்ந்தெடுக்கவும்...":
        teacher_code = TEACHER_MAP[selected_teacher_name]
        
        # மாஸ்டர் டேட்டாவில் இருந்து குறிப்பிட்ட ஆசிரியரின் தரவை மட்டும் பிரித்தல்
        df_filtered = df_master[df_master["Staff"] == teacher_code].copy()
        
        if not df_filtered.empty:
            st.success(f"📊 {selected_teacher_name} அவர்களின் கால அட்டவணை:")
            
            # காட்சிப்படுத்துதலை எளிமையாக்க தமிழ் தலைப்புகள்
            df_display = df_filtered.rename(columns={
                "Day": "கிழமை (Day)",
                "Class": "வகுப்பு (Class)",
                "Period": "பாடவேளை (Period)",
                "Subject": "பாடம் (Subject)"
            })

            # இங்கு "Corporate/School Day" என்பதற்குப் பதிலாக "கிழமை (Day)" என்று மாற்றப்பட்டுள்ளது
            st.dataframe(df_display[["கிழமை (Day)", "வகுப்பு (Class)", "பாடவேளை (Period)", "பாடம் (Subject)"]], use_container_width=True)
        else:
            st.warning("குறிப்பிட்ட ஆசிரியருக்கான தேர்வுப் பணி விவரங்கள் தற்போதைய அட்டவணையில் இல்லை.")

# --- TAB 2: வகுப்பு வாரியான தேடல் ---
with tab2:
    st.header("வகுப்பு வாரியான கால அட்டவணை")
    
    classes_list = ["தேர்ந்தெடுக்கவும்...", "12-A", "12-A1", "12-B", "12-C", "12-D", "11-A", "11-C"]
    selected_class = st.selectbox("வகுப்பைத் தேர்ந்தெடுக்கவும்:", classes_list)
    
    if selected_class != "தேர்ந்தெடுக்கவும்...":
        df_class_filtered = df_master[df_master["Class"] == selected_class].copy()
        
        if not df_class_filtered.empty:
            st.success(f"📝 வகுப்பு {selected_class} - இன் கால அட்டவணை விவரங்கள்")
            
            # ஆசிரியர்களின் குறியீட்டிற்குப் பதிலாக முழுப் பெயரை மாற்றுதல்
            reverse_teacher_map = {v: k.split(" (")[0] for k, v in TEACHER_MAP.items()}
            df_class_filtered["Teacher Name"] = df_class_filtered["Staff"].map(reverse_teacher_map).fillna(df_class_filtered["Staff"])
            
            df_class_display = df_class_filtered.rename(columns={
                "Day": "கிழமை (Day)",
                "Period": "பாடவேளை (Period)",
                "Subject": "பாடம் (Subject)",
                "Teacher Name": "ஆசிரியர் (Teacher)"
            })
            
            st.dataframe(df_class_display[["கிழமை (Day)", "பாடவேளை (Period)", "பாடம் (Subject)", "ஆசிரியர் (Teacher)"]], use_container_width=True)
        else:
            st.info("இந்த வகுப்பிற்கான அட்டவணைத் தரவுகள் இன்னும் உள்ளீடு செய்யப்படவில்லை.")

st.markdown("---")
st.caption("🛠️ GHSS கணினி அறிவியல் துறை போர்ட்டல் - 2026")
