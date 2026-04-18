import streamlit as st
import pandas as pd
from supabase import create_client, Client

# --- 1. SUPABASE CONNECTION ---
try:
    url, key = st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(url, key)
except:
    st.error("Connection Error!")
    st.stop()

st.set_page_config(page_title="Weekly Timetable Editor", layout="wide")

# Mark Entry போன்ற பாணியில் தலைப்பு
st.markdown("## 📅 வாராந்திர கால அட்டவணை மேலாண்மை")

# --- ⚡ FETCH DATA ---
@st.cache_data(ttl=5)
def get_basic_data():
    classes = supabase.table("classes").select("class_name").order("class_name").execute()
    allotments = supabase.table("staff_allotment").select("*").execute()
    existing_tt = supabase.table("weekly_timetable").select("*").execute()
    return [c['class_name'] for c in classes.data], allotments.data, existing_tt.data

class_list, allot_data, db_timetable = get_basic_data()

# --- 🏗️ SELECTION ---
selected_class = st.selectbox("வகுப்பைத் தேர்வு செய்க:", ["-- Select Class --"] + class_list)

if selected_class != "-- Select Class --":
    # 1. இந்த வகுப்புக்கு ஏற்கனவே உள்ள தரவுகளைத் தயார் செய்தல்
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
    periods = [str(i) for i in range(1, 9)]
    
    # காலி அட்டவணை (DataFrame) உருவாக்குதல்
    df_template = pd.DataFrame(index=days, columns=periods).fillna("")
    
    # தரவுதளத்தில் உள்ள தகவல்களை DataFrame-க்குள் நிரப்புதல்
    for entry in db_timetable:
        if entry['class_name'] == selected_class:
            if entry['day_of_week'] in days and str(entry['period_number']) in periods:
                label = f"{entry['subject_name']} ({entry['teacher_name'].split('(')[-1].replace(')', '')})"
                df_template.at[entry['day_of_week'], str(entry['period_number'])] = label

    # 2. ஆசிரியர்கள் மற்றும் பாடங்கள் பட்டியல் (Dropdown-க்காக)
    my_staff = [f"{a['subject_name']} ({a['teacher_name'].split('(')[-1].replace(')', '')})" 
                for a in allot_data if a['class_name'] == selected_class]
    my_staff = sorted(list(set(my_staff))) # டூப்ளிகேட்களை நீக்க
    my_staff = [""] + my_staff # காலியாக விட ஒரு ஆப்ஷன்

    st.info("கீழே உள்ள அட்டவணையில் தேவையான பாடவேளையைத் தேர்வு செய்து மாற்றங்களைச் செய்யவும்.")

    # 3. 📝 DATA EDITOR (படம் 1-ல் உள்ளது போன்ற அமைப்பு)
    edited_df = st.data_editor(
        df_template,
        column_config={
            p: st.column_config.SelectboxColumn(
                f"P{p}",
                help=f"Period {p} பாடத்தை தேர்வு செய்க",
                options=my_staff,
                width="medium"
            ) for p in periods
        },
        use_container_width=True,
        num_rows="fixed"
    )

    # 4. 🚀 SAVE BUTTON (சரிபார்த்துச் சேமி)
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🚀 சரிபார்த்துச் சேமி (Submit)", type="primary", use_container_width=True):
        with st.spinner("சேமிக்கப்படுகிறது..."):
            # பழைய பதிவுகளை நீக்குதல்
            supabase.table("weekly_timetable").delete().eq("class_name", selected_class).execute()
            
            new_entries = []
            for day in days:
                for p_num in range(1, 9):
                    val = edited_df.at[day, str(p_num)]
                    if val:
                        # "Tamil (MR)" என்பதில் இருந்து Tamil மற்றும் MR-ஐப் பிரித்தல்
                        sub_part = val.split(" (")[0]
                        teacher_short = val.split(" (")[-1].replace(")", "")
                        
                        # அசல் ஆசிரியர் தகவலைக் கண்டறிதல்
                        staff_info = next((a for a in allot_data if a['class_name'] == selected_class 
                                          and a['subject_name'] == sub_part 
                                          and teacher_short in a['teacher_name']), None)
                        
                        if staff_info:
                            new_entries.append({
                                "class_name": selected_class,
                                "day_of_week": day,
                                "period_number": p_num,
                                "teacher_id": staff_info['teacher_id'],
                                "teacher_name": staff_info['teacher_name'],
                                "subject_name": staff_info['subject_name']
                            })
            
            if new_entries:
                supabase.table("weekly_timetable").insert(new_entries).execute()
            
            st.success(f"{selected_class} கால அட்டவணை வெற்றிகரமாகச் சேமிக்கப்பட்டது!")
            st.cache_data.clear()

else:
    st.warning("கால அட்டவணையைத் திருத்த வகுப்பைத் தேர்வு செய்யவும்.")
