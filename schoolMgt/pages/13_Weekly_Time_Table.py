import streamlit as st
import pandas as pd
from supabase import create_client, Client

# --- 1. SUPABASE CONNECTION ---
try:
    url: str = st.secrets["SUPABASE_URL"]
    key: str = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(url, key)
except Exception as e:
    st.error("Secrets விவரங்கள் சரியாக இல்லை!")
    st.stop()

st.set_page_config(page_title="Weekly Time Table", layout="wide", page_icon="📅")

# --- ⚡ FETCH DATA ---
@st.cache_data(ttl=60)
def get_all_data():
    classes = supabase.table("classes").select("class_name").order("class_name").execute()
    allotments = supabase.table("staff_allotment").select("*").execute()
    timetable = supabase.table("weekly_timetable").select("*").execute()
    return [c['class_name'] for c in classes.data], allotments.data, timetable.data

class_list, allotment_data, existing_timetable = get_all_data()

st.title("📅 வாராந்திர கால அட்டவணை")

# --- 📋 SELECTION ---
selected_class = st.selectbox("வகுப்பைத் தேர்வு செய்க:", ["-- Select --"] + class_list)

if selected_class != "-- Select --":
    # 1. இந்த வகுப்புக்கு ஒதுக்கப்பட்ட ஆசிரியர்களை மட்டும் வடிகட்டுதல்
    my_staff = [a for a in allotment_data if a['class_name'] == selected_class]
    
    if not my_staff:
        st.warning(f"இந்த வகுப்பிற்கு ({selected_class}) இன்னும் ஆசிரியர்கள் ஒதுக்கப்படவில்லை.")
    else:
        # 2. கால அட்டவணை கட்டமைப்பு (Grid)
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
        periods = range(1, 9)
        
        st.subheader(f"🏫 {selected_class} - பாடவேளை ஒதுக்கீடு")
        
        # Grid View
        for day in days:
            st.write(f"**{day}**")
            cols = st.columns(8)
            for p in periods:
                # ஏற்கனவே இந்த நேரத்தில் இந்தப் பாடவேளை இருக்கிறதா எனப் பார்க்க
                current_entry = next((item for item in existing_timetable 
                                     if item['class_name'] == selected_class 
                                     and item['day_of_week'] == day 
                                     and item['period_number'] == p), None)
                
                with cols[p-1]:
                    btn_label = f"P{p}\nEmpty" if not current_entry else f"P{p}\n{current_entry['teacher_name'].split('(')[-1].replace(')', '')}"
                    
                    # ஒவ்வொரு பாடவேளைக்கும் ஒரு Expander (Pop-up போல)
                    with st.popover(btn_label, use_container_width=True):
                        st.write(f"Period {p} - {day}")
                        
                        # தகுதியான ஆசிரியர்கள் பட்டியல்
                        options = {f"{s['teacher_name']} ({s['subject_name']})": s for s in my_staff}
                        teacher_choice = st.selectbox("ஆசிரியர்:", ["-- Select --"] + list(options.keys()), key=f"sel_{day}_{p}")
                        
                        if st.button("Save", key=f"btn_{day}_{p}"):
                            if teacher_choice != "-- Select --":
                                staff_info = options[teacher_choice]
                                
                                # 🚦 CONFLICT CHECK: இந்த ஆசிரியர் இதே நேரத்தில் வேறு வகுப்பில் இருக்கிறாரா?
                                conflict = next((item for item in existing_timetable 
                                                if item['teacher_id'] == staff_info['teacher_id'] 
                                                and item['day_of_week'] == day 
                                                and item['period_number'] == p), None)
                                
                                if conflict:
                                    st.error(f"முரண்பாடு! இவர் ஏற்கனவே {conflict['class_name']} வகுப்பில் உள்ளார்.")
                                else:
                                    # சேமிக்கும் பகுதி
                                    data = {
                                        "class_name": selected_class,
                                        "day_of_week": day,
                                        "period_number": p,
                                        "teacher_id": staff_info['teacher_id'],
                                        "teacher_name": staff_info['teacher_name'],
                                        "subject_name": staff_info['subject_name']
                                    }
                                    supabase.table("weekly_timetable").insert(data).execute()
                                    st.cache_data.clear()
                                    st.rerun()

    # --- 📊 முழு அட்டவணைப் பார்வை (Table View) ---
    st.divider()
    st.subheader(f"📝 {selected_class} - வாராந்திர பார்வை")
    
    # தரவுகளை டேபிளாக மாற்றுதல்
    if existing_timetable:
        df_view = pd.DataFrame(existing_timetable)
        df_class = df_view[df_view['class_name'] == selected_class]
        
        if not df_class.empty:
            pivot_df = df_class.pivot(index='day_of_week', columns='period_number', values='subject_name')
            pivot_df = pivot_df.reindex(days)
            st.table(pivot_df.fillna("-"))
