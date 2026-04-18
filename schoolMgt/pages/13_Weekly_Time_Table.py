import streamlit as st
import pandas as pd
import hashlib
from supabase import create_client, Client

# --- 1. SUPABASE CONNECTION ---
try:
    url, key = st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(url, key)
except:
    st.error("Connection Error!")
    st.stop()

st.set_page_config(page_title="Timetable Master", layout="wide")

# CSS: அட்டவணை மற்றும் சிறிய வண்ணச் சில்லுகளுக்கான வடிவம்
st.markdown("""
    <style>
    /* Data Editor Headers */
    .stDataEditor div[data-testid="stHeader"] {
        font-size: 20px !important; font-weight: bold !important;
        background-color: #f0f2f6 !important; color: #1f2937 !important;
    }
    /* Small Colorful Chips Styling */
    .teacher-chip {
        padding: 4px 8px; border-radius: 12px; font-size: 11px;
        font-weight: bold; color: #333; margin-bottom: 6px;
        border: 1px solid rgba(0,0,0,0.1); display: inline-block;
        width: 100%; text-align: center; box-shadow: 1px 1px 3px rgba(0,0,0,0.05);
    }
    .chip-label { font-size: 10px; color: #555; display: block; }
    </style>
    """, unsafe_allow_html=True)

# --- ⚡ FETCH DATA ---
@st.cache_data(ttl=5)
def get_data():
    allot = supabase.table("staff_allotment").select("*").execute()
    time_db = supabase.table("weekly_timetable").select("*").execute()
    classes = supabase.table("classes").select("class_name").order("class_name").execute()
    return allot.data, time_db.data, [c['class_name'] for c in classes.data]

allot_data, db_list, class_list = get_data()

def get_short_sub(sub_name):
    sub_map = {"Computer Science": "CS", "Computer Applications": "CA", "Commerce": "COM", "Accountancy": "ACC", "Economics": "ECO", "Mathematics": "MAT", "Tamil": "TAM", "English": "ENG"}
    return sub_map.get(sub_name, sub_name[:3].upper())

def get_color(text):
    if not text: return "#ffffff"
    hash_obj = hashlib.md5(text.encode()).hexdigest()
    # லேசான வண்ணங்கள் (Pastel Colors)
    return f'#{(int(hash_obj[:2],16)%30)+220:02x}{(int(hash_obj[2:4],16)%30)+220:02x}{(int(hash_obj[4:6],16)%30)+220:02x}'

st.title("📅 வாராந்திர கால அட்டவணை")

# --- 🏗️ LAYOUT ---
main_col, side_col = st.columns([1.4, 0.6])

with main_col:
    selected_class = st.selectbox("வகுப்பைத் தேர்வு செய்க:", ["-- Select Class --"] + class_list)

    if selected_class != "-- Select Class --":
        # 1. தரவுகளைத் தயார் செய்தல்
        days_short = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
        day_map = {"Mon": "Monday", "Tue": "Tuesday", "Wed": "Wednesday", "Thu": "Thursday", "Fri": "Friday", "Sat": "Saturday"}
        periods = [str(i) for i in range(1, 9)]
        
        df = pd.DataFrame(index=days_short, columns=periods).fillna("")
        
        for e in db_list:
            if e['class_name'] == selected_class:
                d_short = e['day_of_week'][:3]
                if d_short in days_short and str(e['period_number']) in periods:
                    label = f"{e['subject_name']} ({e['teacher_name'].split('(')[-1].replace(')', '')})"
                    df.at[d_short, str(e['period_number'])] = label

        # 2. Dropdown Options
        my_staff = sorted(list(set([f"{a['subject_name']} ({a['teacher_name'].split('(')[-1].replace(')', '')})" 
                                   for a in allot_data if a['class_name'] == selected_class])))
        my_staff = [""] + my_staff

        # 3. Data Editor (படம் 1 பாணி)
        edited_df = st.data_editor(
            df,
            column_config={p: st.column_config.SelectboxColumn(p, options=my_staff, width="small") for p in periods},
            use_container_width=True, num_rows="fixed"
        )

        # 4. Save Button
        if st.button("🚀 சரிபார்த்துச் சேமி (Submit)", type="primary", use_container_width=True):
            with st.spinner("சேமிக்கப்படுகிறது..."):
                supabase.table("weekly_timetable").delete().eq("class_name", selected_class).execute()
                new_data = []
                for d_short, row in edited_df.iterrows():
                    for p_num in periods:
                        val = row[p_num]
                        if val:
                            sub_name = val.split(" (")[0]
                            t_short = val.split(" (")[-1].replace(")", "")
                            staff = next((a for a in allot_data if a['class_name'] == selected_class 
                                         and a['subject_name'] == sub_name and t_short in a['teacher_name']), None)
                            if staff:
                                new_data.append({"class_name": selected_class, "day_of_week": day_map[d_short], "period_number": int(p_num), "teacher_id": staff['teacher_id'], "teacher_name": staff['teacher_name'], "subject_name": staff['subject_name']})
                if new_data: supabase.table("weekly_timetable").insert(new_data).execute()
                st.success("வெற்றிகரமாகச் சேமிக்கப்பட்டது!")
                st.cache_data.clear()

with side_col:
    if selected_class != "-- Select Class --":
        st.markdown(f"##### 🏷️ {selected_class} - ஆசிரியர் சில்லுகள்")
        # இந்த வகுப்புக்குரிய ஆசிரியர்களை மட்டும் எடுத்தல்
        class_allots = [a for a in allot_data if a['class_name'] == selected_class]
        
        if class_allots:
            for a in class_allots:
                bg_color = get_color(a['subject_name'])
                t_short = a['teacher_name'].split('(')[-1].replace(')', '')
                
                # சிறிய வண்ணச் சில்லு உருவாக்கம்
                st.markdown(f"""
                    <div class="teacher-chip" style="background-color: {bg_color};">
                        {a['subject_name']} - {t_short}
                        <span class="chip-label">ஒதுக்கீடு: {a['periods_per_week']} பீரியட்கள்</span>
                    </div>
                """, unsafe_allow_html=True)
        else:
            st.caption("இந்த வகுப்புக்கு ஆசிரியர்கள் இன்னும் ஒதுக்கப்படவில்லை.")
    else:
        st.info("வகுப்பைத் தேர்வு செய்தால் சில்லுகள் இங்கே தோன்றும்.")
