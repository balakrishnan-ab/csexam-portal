import streamlit as st
import pandas as pd
from supabase import create_client, Client

# --- SUPABASE CONNECTION ---
try:
    url, key = st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(url, key)
except:
    st.error("Connection Error!")
    st.stop()

st.set_page_config(page_title="Teacher Timetable", layout="wide")

# CSS: நேர்த்தியான தோற்றம்
st.markdown("""
    <style>
    .info-line { font-size: 13px; padding: 5px; border-bottom: 1px solid #eee; }
    div[data-testid="stColumn"] { padding: 0px !important; }
    </style>
    """, unsafe_allow_html=True)

# --- FETCH DATA ---
@st.cache_data(ttl=2)
def get_data():
    allot = supabase.table("staff_allotment").select("*").execute()
    time_db = supabase.table("weekly_timetable").select("*").execute()
    teachers = supabase.table("teachers").select("emis_id, short_name, full_name").order("full_name").execute()
    return allot.data, time_db.data, teachers.data

allot_data, db_list, teach_data = get_data()

st.title("👨‍🏫 ஆசிரியர் கால அட்டவணை மேலாண்மை")
main_col, side_col = st.columns([1.6, 0.4])

with main_col:
    t_opts = {f"{t['full_name']} ({t['short_name']})": t for t in teach_data}
    sel_t_label = st.selectbox("ஆசிரியரைத் தேர்வு செய்க:", ["-- Select Teacher --"] + list(t_opts.keys()), label_visibility="collapsed")

if sel_t_label != "-- Select Teacher --":
    sel_t = t_opts[sel_t_label]
    t_id = sel_t['emis_id']
    t_allots = [a for a in allot_data if a['teacher_id'] == t_id]

    state_key = f"tt_state_{t_id}"
    days_short = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
    days_full = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
    day_map = dict(zip(days_short, days_full))
    periods = [str(i) for i in range(1, 9)]

    if state_key not in st.session_state:
        df_init = pd.DataFrame(index=days_short, columns=periods).fillna("")
        for e in db_list:
            if e['teacher_id'] == t_id:
                d_short = e['day_of_week'][:3]
                if d_short in days_short and str(e['period_number']) in periods:
                    df_init.at[d_short, str(e['period_number'])] = e['class_name']
        st.session_state[state_key] = df_init

    # 1. 🏷️ வலதுபுறம் FN/AN விவரங்களுடன் கூடிய ஒதுக்கீடு
    with side_col:
        st.markdown("##### 📚 ஒதுக்கீடு விவரம்")
        current_df = st.session_state[state_key]
        
        # FN/AN பிரித்தல் (பீரியட் 1-4 காலை, 5-8 மாலை)
        for a in t_allots:
            cls = a['class_name']
            total_used = 0
            fn_used = 0
            an_used = 0
            
            for d in days_short:
                for p in periods:
                    if current_df.at[d, p] == cls:
                        total_used += 1
                        if int(p) <= 4: fn_used += 1
                        else: an_used += 1
            
            rem = a['periods_per_week'] - total_used
            # மீதம் 0 வந்தால் பட்டியில் காட்டாது
            status_text = f"மீதம்: {rem}" if rem > 0 else "முடிந்தது ✅"
            color = "blue" if rem > 0 else "gray"
            
            st.markdown(f'<div class="info-line"><b>{cls}</b> | {a["subject_name"]} | <span style="color:{color};">{status_text}</span><br><small style="color:green;">FN:{fn_used} | AN:{an_used}</small></div>', unsafe_allow_html=True)

    # 2. 📝 DATA EDITOR
    with main_col:
        # ஒதுக்கீடு மீதமுள்ள வகுப்புகளை மட்டும் பட்டியலிடுதல்
        available_list = [""]
        for a in t_allots:
            used = list(current_df.values.flatten()).count(a['class_name'])
            if a['periods_per_week'] - used > 0:
                available_list.append(a['class_name'])
        
        # ஏற்கனவே உள்ள பெயர்கள் மறையாமல் இருக்க பழைய பெயர்களைச் சேர்த்தல்
        flat_all = list(current_df.values.flatten())
        existing = sorted(list(set([str(x) for x in flat_all if x and x != ""])))
        final_dropdown = sorted(list(set(available_list + existing)))

        edited_df = st.data_editor(
            st.session_state[state_key],
            column_config={p: st.column_config.SelectboxColumn(p, options=final_dropdown, width="small") for p in periods},
            use_container_width=True, key=f"editor_{t_id}"
        )
        st.session_state[state_key] = edited_df

        # 3. SAVE
        if st.button("🚀 அட்டவணையைச் சேமி", type="primary", use_container_width=True):
            supabase.table("weekly_timetable").delete().eq("teacher_id", t_id).execute()
            new_entries = []
            for d, row in edited_df.iterrows():
                for p in periods:
                    cls = row[p]
                    if cls and cls != "":
                        staff = next((a for a in t_allots if a['class_name'] == cls), None)
                        if staff:
                            new_entries.append({"class_name": cls, "day_of_week": day_map[d], "period_number": int(p),
                                              "teacher_id": t_id, "teacher_name": sel_t['full_name'], "subject_name": staff['subject_name']})
            if new_entries: supabase.table("weekly_timetable").insert(new_entries).execute()
            st.success("சேமிக்கப்பட்டது!")
            st.rerun()
