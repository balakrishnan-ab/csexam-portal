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

st.set_page_config(page_title="Timetable Editor", layout="wide")

# CSS: அட்டவணை மற்றும் சில்லுகளுக்கான வடிவம்
st.markdown("""
    <style>
    /* Data Editor Styling */
    .stDataEditor div[data-testid="stHeader"] {
        font-size: 16px !important; font-weight: bold !important; background-color: #f0f2f6 !important;
    }
    /* Small Colored Chips */
    .staff-chip {
        display: inline-block; padding: 2px 8px; margin: 3px;
        border-radius: 12px; font-size: 11px; font-weight: bold;
        border: 1px solid #ccc; color: #333;
    }
    </style>
    """, unsafe_allow_html=True)

def get_short_sub(sub_name):
    sub_map = {"Computer Science": "CS", "Computer Applications": "CA", "Commerce": "COM", "Accountancy": "ACC", "Economics": "ECO", "Mathematics": "MAT", "Tamil": "TAM", "English": "ENG"}
    return sub_map.get(sub_name, sub_name[:3].upper())

def get_color(text):
    if not text: return "#ffffff"
    hash_obj = hashlib.md5(text.encode()).hexdigest()
    # லேசான வண்ணங்கள் (Light Colors)
    r = (int(hash_obj[:2],16)%40)+210
    g = (int(hash_obj[2:4],16)%40)+210
    b = (int(hash_obj[4:6],16)%40)+210
    return f'#{r:02x}{g:02x}{b:02x}'

# --- ⚡ FETCH DATA ---
@st.cache_data(ttl=5)
def get_data():
    allot = supabase.table("staff_allotment").select("*").execute()
    time_db = supabase.table("weekly_timetable").select("*").execute()
    classes = supabase.table("classes").select("class_name").order("class_name").execute()
    return allot.data, time_db.data, [c['class_name'] for c in classes.data]

allot_data, db_list, class_list = get_data()

# --- 🏗️ LAYOUT ---
main_col, side_col = st.columns([1.5, 0.5])

with main_col:
    selected_class = st.selectbox("வகுப்பைத் தேர்வு செய்க:", ["-- Select Class --"] + class_list)

with side_col:
    if selected_class != "-- Select Class --":
        st.markdown("##### 🏷️ ஆசிரியர் ஒதுக்கீடு")
        # அந்த வகுப்புக்கு ஒதுக்கப்பட்ட ஆசிரியர்களை மட்டும் எடுத்தல்
        class_staff = [a for a in allot_data if a['class_name'] == selected_class]
        
        if class_staff:
            for s in class_staff:
                bg = get_color(s['subject_name'])
                t_short = s['teacher_name'].split('(')[-1].replace(')', '')
                st.markdown(f"""
                    <div class="staff-chip" style="background-color: {bg};">
                        {s['subject_name']} - {t_short} ({s['periods_per_week']})
                    </div>
                """, unsafe_allow_html=True)
        else:
            st.caption("ஒதுக்கீடு இல்லை")

# --- 📝 EDITING SECTION ---
if selected_class != "-- Select Class --":
    with main_col:
        days_short = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
        days_full = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
        periods = [str(i) for i in range(1, 9)]
        day_map = dict(zip(days_short, days_full))

        # 1. ஆரம்பகால தரவுகளை DataFrame-ல் நிரப்புதல்
        df = pd.DataFrame(index=days_short, columns=periods).fillna("")
        for e in db_list:
            if e['class_name'] == selected_class:
                d_short = e['day_of_week'][:3]
                if d_short in days_short and str(e['period_number']) in periods:
                    label = f"{e['subject_name']} ({e['teacher_name'].split('(')[-1].replace(')', '')})"
                    df.at[d_short, str(e['period_number'])] = label

        # 2. Dropdown மெனுவிற்கான பட்டியல்
        my_staff_opts = sorted(list(set([f"{a['subject_name']} ({a['teacher_name'].split('(')[-1].replace(')', '')})" 
                                        for a in allot_data if a['class_name'] == selected_class])))
        my_staff_opts = [""] + my_staff_opts

        # 3. Data Editor
        edited_df = st.data_editor(
            df,
            column_config={p: st.column_config.SelectboxColumn(p, options=my_staff_opts, width="small") for p in periods},
            use_container_width=True,
            num_rows="fixed"
        )

        # 4. Save Button
        if st.button("🚀 சரிபார்த்துச் சேமி (Save)", type="primary", use_container_width=True):
            with st.spinner("சேமிக்கப்படுகிறது..."):
                supabase.table("weekly_timetable").delete().eq("class_name", selected_class).execute()
                new_data = []
                for d_short, row in edited_df.iterrows():
                    for p_num in periods:
                        val = row[p_num]
                        if val:
                            sub_n = val.split(" (")[0]
                            t_s = val.split(" (")[-1].replace(")", "")
                            staff = next((a for a in allot_data if a['class_name'] == selected_class and a['subject_name'] == sub_n and t_s in a['teacher_name']), None)
                            if staff:
                                new_data.append({
                                    "class_name": selected_class, "day_of_week": day_map[d_short], "period_number": int(p_num),
                                    "teacher_id": staff['teacher_id'], "teacher_name": staff['teacher_name'], "subject_name": staff['subject_name']
                                })
                if new_data:
                    supabase.table("weekly_timetable").insert(new_data).execute()
                st.success("சேமிக்கப்பட்டது!")
                st.cache_data.clear()
