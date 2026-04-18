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

# CSS: அட்டவணையைத் தெளிவாகவும் பெரிய எழுத்துக்களுடனும் காட்ட
st.markdown("""
    <style>
    /* Headers Styling */
    .stDataEditor div[data-testid="stHeader"] {
        font-size: 18px !important;
        font-weight: bold !important;
        background-color: #f0f2f6 !important;
    }
    /* Cell Text Styling */
    .stDataEditor div[role="gridcell"] {
        font-size: 14px !important;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("📅 வாராந்திர கால அட்டவணை மேலாண்மை")

# --- ⚡ FETCH DATA ---
@st.cache_data(ttl=5)
def get_data():
    allot = supabase.table("staff_allotment").select("*").execute()
    time_db = supabase.table("weekly_timetable").select("*").execute()
    teach = supabase.table("teachers").select("emis_id, short_name, full_name").execute()
    classes = supabase.table("classes").select("class_name").order("class_name").execute()
    return allot.data, time_db.data, teach.data, [c['class_name'] for c in classes.data]

allot_data, db_list, teach_data, class_list = get_data()

# --- 🏗️ LAYOUT ---
main_col, side_col = st.columns([1.5, 0.5])

with side_col:
    st.subheader("👨‍🏫 ஆசிரியர் தேர்வு")
    t_opts = {f"{t['full_name']} ({t['short_name']})": t for t in teach_data}
    sel_t_label = st.selectbox("ஆசிரியரைத் தேர்வு செய்க:", ["-- Select --"] + list(t_opts.keys()))
    
    selected_class = "-- Select Class --"
    if sel_t_label != "-- Select --":
        t_id = t_opts[sel_t_label]['emis_id']
        # அந்த ஆசிரியருக்கு ஒதுக்கப்பட்ட வகுப்புகள் மட்டும்
        t_allots = [a for a in allot_data if a['teacher_id'] == t_id]
        
        if t_allots:
            st.write("ஒதுக்கப்பட்ட வகுப்புகள்:")
            for a in t_allots:
                if st.button(f"திறக்க: {a['class_name']}", key=f"btn_{a['id']}", use_container_width=True):
                    st.session_state['view_class'] = a['class_name']
                    st.rerun()
        else:
            st.warning("இந்த ஆசிரியருக்கு வகுப்புகள் ஒதுக்கப்படவில்லை.")

with main_col:
    # 1. வகுப்புத் தேர்வு (ஆசிரியர் பட்டன் மூலமாகவும் மாறலாம்)
    view_class = st.session_state.get('view_class', "-- Select Class --")
    selected_class = st.selectbox("வகுப்பு:", ["-- Select Class --"] + class_list, 
                                  index=class_list.index(view_class)+1 if view_class in class_list else 0)

    if selected_class != "-- Select Class --":
        st.write(f"### 🏫 {selected_class} - கால அட்டவணைத் திருத்தம்")
        
        # 2. தரவுகளைத் தயார் செய்தல் (Mon-Sat & 1-8)
        days_full = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
        days_short = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
        periods = [str(i) for i in range(1, 9)]
        
        # கிரிட் மேப்பிங்
        day_map = dict(zip(days_short, days_full))
        
        # ஆரம்பகால DataFrame
        df = pd.DataFrame(index=days_short, columns=periods).fillna("")
        
        for e in db_list:
            if e['class_name'] == selected_class:
                d_short = e['day_of_week'][:3]
                if d_short in days_short and str(e['period_number']) in periods:
                    label = f"{e['subject_name']} ({e['teacher_name'].split('(')[-1].replace(')', '')})"
                    df.at[d_short, str(e['period_number'])] = label

        # 3. ஆசிரியர்கள் பட்டியல் (Dropdown Options)
        my_staff = sorted(list(set([f"{a['subject_name']} ({a['teacher_name'].split('(')[-1].replace(')', '')})" 
                                   for a in allot_data if a['class_name'] == selected_class])))
        my_staff = [""] + my_staff

        # 4. 📝 DATA EDITOR (படம் 1 போன்ற அமைப்பு)
        edited_df = st.data_editor(
            df,
            column_config={
                p: st.column_config.SelectboxColumn(
                    p, # 'p' என்பது 1, 2, 3...
                    options=my_staff,
                    width="small"
                ) for p in periods
            },
            use_container_width=True,
            num_rows="fixed"
        )

        # 5. 🚀 SUBMIT
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🚀 சரிபார்த்துச் சேமி (Submit)", type="primary", use_container_width=True):
            with st.spinner("சேமிக்கப்படுகிறது..."):
                # பழைய தரவை நீக்குதல்
                supabase.table("weekly_timetable").delete().eq("class_name", selected_class).execute()
                
                new_data = []
                for d_short, row in edited_df.iterrows():
                    for p_num in periods:
                        val = row[p_num]
                        if val:
                            sub_name = val.split(" (")[0]
                            t_short = val.split(" (")[-1].replace(")", "")
                            
                            staff = next((a for a in allot_data if a['class_name'] == selected_class 
                                         and a['subject_name'] == sub_name 
                                         and t_short in a['teacher_name']), None)
                            
                            if staff:
                                new_data.append({
                                    "class_name": selected_class,
                                    "day_of_week": day_map[d_short],
                                    "period_number": int(p_num),
                                    "teacher_id": staff['teacher_id'],
                                    "teacher_name": staff['teacher_name'],
                                    "subject_name": staff['subject_name']
                                })
                
                if new_data:
                    supabase.table("weekly_timetable").insert(new_data).execute()
                
                st.success("வெற்றிகரமாகச் சேமிக்கப்பட்டது!")
                st.cache_data.clear()
