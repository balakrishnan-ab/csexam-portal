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
@st.cache_data(ttl=10) # தரவுகள் உடனுக்குடன் மாற 10 விநாடிகள்
def get_all_data():
    classes = supabase.table("classes").select("class_name").order("class_name").execute()
    allotments = supabase.table("staff_allotment").select("*").execute()
    timetable = supabase.table("weekly_timetable").select("*").execute()
    combined = supabase.table("combined_groups").select("*").execute()
    return [c['class_name'] for c in classes.data], allotments.data, timetable.data, combined.data

class_list, allotment_data, existing_timetable, combined_groups = get_all_data()

st.title("📅 வாராந்திர கால அட்டவணை")

# --- 📋 SELECTION ---
selected_class = st.selectbox("வகுப்பைத் தேர்வு செய்க:", ["-- Select --"] + class_list)

if selected_class != "-- Select --":
    # 🔍 இந்த வகுப்பு எந்தெந்த GC குரூப்பில் உள்ளது என்பதைக் கண்டறிதல்
    relevant_groups = [g['group_name'] for g in combined_groups if selected_class in g['class_list']]
    
    # 🔍 நேரடி ஒதுக்கீடு + GC குரூப் ஒதுக்கீடு இரண்டையும் சேர்த்தல்
    my_staff = [a for a in allotment_data if a['class_name'] == selected_class or a['class_name'] in relevant_groups]
    
    if not my_staff:
        st.warning(f"இந்த வகுப்பிற்கு ({selected_class}) இன்னும் ஆசிரியர்கள் ஒதுக்கப்படவில்லை. Staff Allotment பக்கம் சென்று வகுப்பு அல்லது GC குரூப்பிற்கு ஆசிரியர்களை ஒதுக்கவும்.")
    else:
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
        periods = range(1, 9)
        
        st.subheader(f"🏫 {selected_class} - பாடவேளை அமைப்பு")
        
        # 🎨 GRID VIEW
        for day in days:
            with st.container():
                st.write(f"### {day}")
                cols = st.columns(8)
                for p in periods:
                    # ஏற்கனவே இந்த நேரத்தில் இந்தப் பாடவேளை இருக்கிறதா?
                    entries = [item for item in existing_timetable 
                               if item['class_name'] == selected_class 
                               and item['day_of_week'] == day 
                               and item['period_number'] == p]
                    
                    with cols[p-1]:
                        # பட்டன் லேபிள் (ஒன்றுக்கும் மேற்பட்ட ஆசிரியர் இருந்தால் 'Multi' எனக் காட்டும்)
                        if not entries:
                            btn_label = f"P{p}\nEmpty"
                        elif len(entries) == 1:
                            btn_label = f"P{p}\n{entries[0]['teacher_name'].split('(')[-1].replace(')', '')}"
                        else:
                            btn_label = f"P{p}\n(Multi)"
                        
                        with st.popover(btn_label, use_container_width=True):
                            st.write(f"**Period {p} - {day}**")
                            
                            # பல ஆசிரியர்களைத் தேர்வு செய்யும் வசதி (Multi-select for GC)
                            staff_options = {f"{s['teacher_name']} ({s['subject_name']})": s for s in my_staff}
                            
                            selected_options = st.multiselect(
                                "ஆசிரியர்களைத் தேர்வு செய்க:", 
                                list(staff_options.keys()),
                                default=[f"{e['teacher_name']} ({e['subject_name']})" for e in entries],
                                key=f"ms_{day}_{p}"
                            )
                            
                            if st.button("Update Slot", key=f"btn_{day}_{p}"):
                                # 1. பழைய பதிவுகளை நீக்குதல்
                                supabase.table("weekly_timetable").delete().eq("class_name", selected_class).eq("day_of_week", day).eq("period_number", p).execute()
                                
                                # 2. புதிய ஆசிரியர்களைச் சேர்த்தல்
                                for opt in selected_options:
                                    staff_info = staff_options[opt]
                                    
                                    # 🚦 CONFLICT CHECK: ஆசிரியர் வேறு வகுப்பில் இருக்கிறாரா?
                                    conflict = next((item for item in existing_timetable 
                                                    if item['teacher_id'] == staff_info['teacher_id'] 
                                                    and item['day_of_week'] == day 
                                                    and item['period_number'] == p
                                                    and item['class_name'] != selected_class), None)
                                    
                                    if conflict:
                                        st.error(f"{staff_info['teacher_name']} ஏற்கனவே {conflict['class_name']} வகுப்பில் உள்ளார்!")
                                    else:
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

    # --- 📊 வாராந்திர அட்டவணை அட்டவணை வடிவில் ---
    st.divider()
    st.subheader(f"📝 {selected_class} - கால அட்டவணைப் பார்வை")
    
    if existing_timetable:
        df_view = pd.DataFrame(existing_timetable)
        df_class = df_view[df_view['class_name'] == selected_class]
        
        if not df_class.empty:
            # பல ஆசிரியர்கள் இருந்தால் பெயர்களை இணைத்துக் காட்டுதல்
            pivot_df = df_class.groupby(['day_of_week', 'period_number'])['teacher_name'].apply(lambda x: ', '.join([n.split('(')[-1].replace(')', '') for n in x])).unstack()
            pivot_df = pivot_df.reindex(days)
            st.table(pivot_df.fillna("-"))
