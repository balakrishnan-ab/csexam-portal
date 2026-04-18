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

st.set_page_config(page_title="Teacher Timetable Editor", layout="wide")

# படம் 2 போன்ற நேர்த்தியான CSS
st.markdown("""
    <style>
    /* Table Headers */
    .stDataEditor div[data-testid="stHeader"] {
        font-size: 14px !important; font-weight: bold !important;
        background-color: #f8f9fa !important; color: #333 !important;
    }
    /* Info Cards on Right */
    .info-card {
        border: 1px solid #ddd; border-radius: 6px; padding: 10px;
        margin-bottom: 8px; background: white; border-left: 5px solid #4CAF50;
    }
    </style>
    """, unsafe_allow_html=True)

# --- ⚡ FETCH DATA ---
@st.cache_data(ttl=5)
def get_data():
    allot = supabase.table("staff_allotment").select("*").execute()
    time_db = supabase.table("weekly_timetable").select("*").execute()
    teachers = supabase.table("teachers").select("emis_id, short_name, full_name").order("full_name").execute()
    return allot.data, time_db.data, teachers.data

allot_data, db_list, teach_data = get_data()

# --- 🏗️ LAYOUT ---
st.title("👨‍🏫 ஆசிரியர் கால அட்டவணை மேலாண்மை")

main_col, side_col = st.columns([1.5, 0.5])

with main_col:
    # 🎯 ஆசிரியர் தேர்வு - இப்போது நடுவில்
    t_opts = {f"{t['full_name']} ({t['short_name']})": t for t in teach_data}
    sel_t_label = st.selectbox("ஆசிரியரைத் தேர்வு செய்க:", ["-- Select Teacher --"] + list(t_opts.keys()))

if sel_t_label != "-- Select Teacher --":
    sel_t = t_opts[sel_t_label]
    t_id = sel_t['emis_id']
    
    # ஆசிரியருக்கு ஒதுக்கப்பட்ட வகுப்புகள்
    t_allots = [a for a in allot_data if a['teacher_id'] == t_id]
    alloted_classes = sorted(list(set([a['class_name'] for a in t_allots])))

    # 1. 🏷️ வலதுபுறம் ஆசிரியர் செல்லும் வகுப்புகள் விவரம்
    with side_col:
        st.markdown("##### 📚 வகுப்பு விவரங்கள்")
        
        # தற்காலிகமாக எடிட்டரில் உள்ள தரவுகளைக் கணக்கிட (Live Update)
        state_key = f"tt_state_{t_id}"
        days_short = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
        days_full = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
        day_map = dict(zip(days_short, days_full))
        periods = [str(i) for i in range(1, 9)]

        # Session State-ல் தரவுகளை ஏற்றுதல்
        if state_key not in st.session_state:
            df_init = pd.DataFrame(index=days_short, columns=periods).fillna("")
            for e in db_list:
                if e['teacher_id'] == t_id:
                    d_short = e['day_of_week'][:3]
                    if d_short in days_short and str(e['period_number']) in periods:
                        df_init.at[d_short, str(e['period_number'])] = e['class_name']
            st.session_state[state_key] = df_init

        # ஒதுக்கீடு நிலை (Remaining counts)
        current_df = st.session_state[state_key]
        flat_selections = list(current_df.values.flatten())
        
        available_class_options = [""]
        for a in t_allots:
            used = flat_selections.count(a['class_name'])
            rem = a['periods_per_week'] - used
            
            if rem > 0:
                available_class_options.append(a['class_name'])
                st.markdown(f"""<div class="info-card"><b>{a['class_name']}</b><br><small>{a['subject_name']}</small><br><span style="color:green;">மீதம்: {rem}</span></div>""", unsafe_allow_html=True)
            else:
                st.markdown(f"""<div class="info-card" style="border-left-color:gray; background:#f0f0f0;"><b>{a['class_name']}</b><br><small>{a['subject_name']}</small><br><span style="color:gray;">முடிந்தது ✅</span></div>""", unsafe_allow_html=True)

    # 2. 📝 DATA EDITOR (மையத்தில்)
    with main_col:
        st.info(f"குறிப்பு: {sel_t['short_name']} செல்லும் வகுப்புகளைக் கட்டங்களில் தேர்வு செய்யவும். ஒதுக்கீடு முடிந்த வகுப்புகள் பட்டியலில் இருந்து தானாகவே மறைந்துவிடும்.")
        
        edited_df = st.data_editor(
            st.session_state[state_key],
            column_config={p: st.column_config.SelectboxColumn(p, options=available_class_options, width="small") for p in periods},
            use_container_width=True,
            num_rows="fixed",
            key=f"editor_{t_id}"
        )
        st.session_state[state_key] = edited_df

        # 3. 🚀 SAVE BUTTON
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button(f"🚀 {sel_t['short_name']} அட்டவணையைச் சேமி (Submit)", type="primary", use_container_width=True):
            with st.spinner("சேமிக்கப்படுகிறது..."):
                # ஆசிரியரின் பழைய பதிவுகளை நீக்குதல்
                supabase.table("weekly_timetable").delete().eq("teacher_id", t_id).execute()
                
                new_entries = []
                for d_short, row in edited_df.iterrows():
                    for p_num in periods:
                        cls_name = row[p_num]
                        if cls_name:
                            staff_info = next((a for a in t_allots if a['class_name'] == cls_name), None)
                            if staff_info:
                                new_entries.append({
                                    "class_name": cls_name, "day_of_week": day_map[d_short], "period_number": int(p_num),
                                    "teacher_id": t_id, "teacher_name": f"{sel_t['full_name']} ({sel_t['short_name']})",
                                    "subject_name": staff_info['subject_name']
                                })
                
                if new_entries:
                    supabase.table("weekly_timetable").insert(new_entries).execute()
                
                st.success(f"{sel_t['short_name']} அட்டவணை வெற்றிகரமாகச் சேமிக்கப்பட்டது!")
                st.cache_data.clear()

else:
    with main_col:
        st.info("தொடங்குவதற்கு மேல் உள்ள பட்டியலில் ஆசிரியரைத் தேர்வு செய்யவும்.")
