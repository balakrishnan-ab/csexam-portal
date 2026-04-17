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
@st.cache_data(ttl=5)
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
    # 🔍 GC குரூப் ஒதுக்கீடுகளைக் கண்டறிதல்
    relevant_groups = [g['group_name'] for g in combined_groups if selected_class in g['class_list']]
    my_staff = [a for a in allotment_data if a['class_name'] == selected_class or a['class_name'] in relevant_groups]
    
    if not my_staff:
        st.warning(f"இந்த வகுப்பிற்கு ({selected_class}) இன்னும் ஆசிரியர்கள் ஒதுக்கப்படவில்லை.")
    else:
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
        periods = range(1, 9)
        
        st.subheader(f"🏫 {selected_class} - பாடவேளை அமைப்பு")
        
        for day in days:
            st.write(f"### {day}")
            cols = st.columns(8)
            for p in periods:
                # ஏற்கனவே உள்ள பதிவுகள்
                entries = [item for item in existing_timetable 
                           if item['class_name'] == selected_class 
                           and item['day_of_week'] == day 
                           and item['period_number'] == p]
                
                with cols[p-1]:
                    if not entries:
                        btn_label = f"P{p}\nEmpty"
                    else:
                        names = ", ".join([e['teacher_name'].split('(')[-1].replace(')', '') for e in entries])
                        btn_label = f"P{p}\n{names}"
                    
                    with st.popover(btn_label, use_container_width=True):
                        st.write(f"**Period {p} - {day}**")
                        
                        staff_options = {f"{s['teacher_name']} ({s['subject_name']})": s for s in my_staff}
                        default_vals = [f"{e['teacher_name']} ({e['subject_name']})" for e in entries if f"{e['teacher_name']} ({e['subject_name']})" in staff_options]
                        
                        selected_options = st.multiselect(
                            "ஆசிரியர்களைத் தேர்வு செய்க:", 
                            list(staff_options.keys()),
                            default=default_vals,
                            key=f"ms_{day}_{p}"
                        )
                        
                        if st.button("Update Slot", key=f"btn_{day}_{p}"):
                            try:
                                # 1. பழைய பதிவை நீக்குதல்
                                supabase.table("weekly_timetable").delete().eq("class_name", selected_class).eq("day_of_week", day).eq("period_number", p).execute()
                                
                                # 2. புதிய ஆசிரியர்களைச் சேர்த்தல்
                                for opt in selected_options:
                                    s = staff_options[opt]
                                    
                                    # 🚦 CONFLICT CHECK
                                    conflict = next((item for item in existing_timetable 
                                                    if item['teacher_id'] == s['teacher_id'] 
                                                    and item['day_of_week'] == day 
                                                    and item['period_number'] == p
                                                    and item['class_name'] != selected_class), None)
                                    
                                    if conflict:
                                        st.error(f"{s['teacher_name']} ஏற்கனவே {conflict['class_name']}-ல் உள்ளார்!")
                                    else:
                                        insert_data = {
                                            "class_name": selected_class,
                                            "day_of_week": day,
                                            "period_number": p,
                                            "teacher_id": str(s['teacher_id']), # String-ஆக மாற்றுதல்
                                            "teacher_name": s['teacher_name'],
                                            "subject_name": s['subject_name']
                                        }
                                        supabase.table("weekly_timetable").insert(insert_data).execute()
                                
                                st.cache_data.clear()
                                st.rerun()
                            except Exception as e:
                                st.error(f"சேமிப்பதில் பிழை: {e}")

    # --- 📊 TABLE VIEW ---
    st.divider()
    st.subheader(f"📝 {selected_class} - கால அட்டவணைப் பார்வை")
    if existing_timetable:
        df_view = pd.DataFrame(existing_timetable)
        df_class = df_view[df_view['class_name'] == selected_class]
        if not df_class.empty:
            pivot_df = df_class.groupby(['day_of_week', 'period_number'])['teacher_name'].apply(lambda x: ', '.join([n.split('(')[-1].replace(')', '') for n in x])).unstack()
            pivot_df = pivot_df.reindex(days)
            st.table(pivot_df.fillna("-"))
