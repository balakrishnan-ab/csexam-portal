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

st.set_page_config(page_title="Elegant Timetable Editor", layout="wide")

# படம் 2 போன்ற நேர்த்தியான தோற்றத்திற்கான CSS
st.markdown("""
    <style>
    /* Headers Styling */
    .stDataEditor div[data-testid="stHeader"] {
        font-size: 14px !important; font-weight: bold !important;
        background-color: #f8f9fa !important; color: #333 !important;
    }
    /* Side Info Box */
    .status-card {
        border: 1px solid #ddd; border-radius: 5px; padding: 8px;
        margin-bottom: 5px; background: white; border-left: 5px solid #007bff;
    }
    </style>
    """, unsafe_allow_html=True)

# --- ⚡ FETCH DATA ---
@st.cache_data(ttl=5)
def get_data():
    allot = supabase.table("staff_allotment").select("*").execute()
    time_db = supabase.table("weekly_timetable").select("*").execute()
    teachers = supabase.table("teachers").select("emis_id, short_name, full_name").execute()
    classes = supabase.table("classes").select("class_name").order("class_name").execute()
    return allot.data, time_db.data, teachers.data, [c['class_name'] for c in classes.data]

allot_data, db_list, teach_data, class_list = get_data()

# --- 🏗️ LAYOUT ---
st.title("🏫 வாராந்திர கால அட்டவணை (Elegant Mode)")

main_col, side_col = st.columns([1.5, 0.5])

with side_col:
    st.markdown("##### 👨‍🏫 ஆசிரியர் தேர்வு")
    t_opts = {f"{t['full_name']} ({t['short_name']})": t for t in teach_data}
    sel_t_label = st.selectbox("ஆசிரியரைத் தேர்வு செய்க:", ["-- Select --"] + list(t_opts.keys()), label_visibility="collapsed")

if sel_t_label != "-- Select --":
    sel_t = t_opts[sel_t_label]
    t_id = sel_t['emis_id']
    t_allots = [a for a in allot_data if a['teacher_id'] == t_id]
    
    with main_col:
        # 1. வகுப்புத் தேர்வு
        class_opts = sorted(list(set([a['class_name'] for a in t_allots])))
        selected_class = st.selectbox("வகுப்பைத் தேர்வு செய்க:", ["-- Select Class --"] + class_opts)

        if selected_class != "-- Select Class --":
            days_short = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
            days_full = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
            day_map = dict(zip(days_short, days_full))
            periods = [str(i) for i in range(1, 9)]

            # 2. ஆரம்ப கால தரவு (Session State-ல் சேமிப்பதால் வேகம் அதிகரிக்கும்)
            state_key = f"tt_{selected_class}_{t_id}"
            if state_key not in st.session_state:
                df_init = pd.DataFrame(index=days_short, columns=periods).fillna("")
                for e in db_list:
                    if e['class_name'] == selected_class:
                        d_short = e['day_of_week'][:3]
                        if d_short in days_short and str(e['period_number']) in periods:
                            label = f"{e['subject_name']} - {e['teacher_name'].split('(')[-1].replace(')', '')}"
                            df_init.at[d_short, str(e['period_number'])] = label
                st.session_state[state_key] = df_init

            # 3. 🏷️ DYNAMIC STATUS & FILTER (வலதுபுறம்)
            with side_col:
                st.markdown("##### 🏷️ ஒதுக்கீடு நிலை")
                current_df = st.session_state[state_key]
                flat_list = list(current_df.values.flatten())
                
                # இந்த ஆசிரியருக்கான ஆப்ஷன்
                t_short = sel_t['short_name']
                staff_info = next((a for a in t_allots if a['class_name'] == selected_class), None)
                
                available_options = [""]
                if staff_info:
                    label = f"{staff_info['subject_name']} - {t_short}"
                    used = flat_list.count(label)
                    rem = staff_info['periods_per_week'] - used
                    
                    if rem > 0:
                        available_options.append(label)
                        st.markdown(f"<div class='status-card'><b>{selected_class}</b><br>{label}<br><span style='color:blue;'>மீதம்: {rem}</span></div>", unsafe_allow_html=True)
                    else:
                        st.markdown(f"<div class='status-card' style='border-left-color:gray; background:#eee;'><b>{selected_class}</b><br>{label}<br><span style='color:green;'>முடிந்தது ✅</span></div>", unsafe_allow_html=True)

            # 4. 📝 DATA EDITOR (படம் 2-ன் நேர்த்தியான அமைப்பு)
            with main_col:
                edited_df = st.data_editor(
                    st.session_state[state_key],
                    column_config={p: st.column_config.SelectboxColumn(p, options=available_options, width="small") for p in periods},
                    use_container_width=True,
                    num_rows="fixed",
                    key=f"editor_{state_key}"
                )
                st.session_state[state_key] = edited_df

                # 5. 🚀 SAVE BUTTON (படம் 2 போன்ற பெரிய சிவப்பு பட்டன்)
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button(f"🚀 {sel_t['short_name']} அட்டவணையைச் சேமி (Save)", type="primary", use_container_width=True):
                    with st.spinner("சேமிக்கப்படுகிறது..."):
                        # இந்த ஆசிரியரின் தரவுகளை மட்டும் நீக்கிவிட்டு மீண்டும் சேமித்தல்
                        supabase.table("weekly_timetable").delete().eq("teacher_id", t_id).eq("class_name", selected_class).execute()
                        new_data = []
                        for d_short, row in edited_df.iterrows():
                            for p_num in periods:
                                val = row[p_num]
                                if val == label: # இந்த ஆசிரியரின் பாடம் மட்டும்
                                    new_data.append({
                                        "class_name": selected_class, "day_of_week": day_map[d_short], "period_number": int(p_num),
                                        "teacher_id": t_id, "teacher_name": f"{sel_t['full_name']} ({sel_t['short_name']})",
                                        "subject_name": staff_info['subject_name']
                                    })
                        if new_data:
                            supabase.table("weekly_timetable").insert(new_data).execute()
                        st.success("வெற்றிகரமாகச் சேமிக்கப்பட்டது!")
                        st.cache_data.clear()

else:
    with main_col:
        st.info("தொடங்குவதற்கு ஆசிரியரைத் தேர்வு செய்யவும்.")
