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

# --- 2. FETCH DATA ---
@st.cache_data(ttl=10)
def get_data():
    allot = supabase.table("staff_allotment").select("*").execute()
    time_db = supabase.table("weekly_timetable").select("*").execute()
    teachers = supabase.table("teachers").select("emis_id, short_name, full_name").order("full_name").execute()
    return allot.data, time_db.data, teachers.data

allot_data, db_list, teach_data = get_data()

# --- 3. UI SETUP ---
st.title("👨‍🏫 ஆசிரியர் கால அட்டவணை மேலாண்மை")
if 'draft_tt' not in st.session_state: st.session_state.draft_tt = {}

t_opts = {f"{t['full_name']} ({t['short_name']})": t for t in teach_data}
sel_t_label = st.selectbox("ஆசிரியரைத் தேர்வு செய்க:", ["-- Select Teacher --"] + list(t_opts.keys()))

if sel_t_label != "-- Select Teacher --":
    sel_t = t_opts[sel_t_label]
    t_id = sel_t['emis_id']
    t_allots = [a for a in allot_data if a['teacher_id'] == t_id]
    
    # Session State-க்கு தரவை மாற்றல்
    if st.session_state.get('active_t_id') != t_id:
        st.session_state.draft_tt = {}
        st.session_state.active_t_id = t_id
        for e in db_list:
            if e['teacher_id'] == t_id:
                st.session_state.draft_tt[(e['day_of_week'], e['period_number'])] = e['class_name']

    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
    periods = [str(i) for i in range(1, 9)]

    main_col, side_col = st.columns([0.7, 0.3])

    # --- 4. DATA EDITOR ---
    with main_col:
        df_grid = pd.DataFrame(index=[d[:3] for d in days], columns=periods).fillna("")
        for (d, p), cls in st.session_state.draft_tt.items():
            df_grid.at[d[:3], str(p)] = cls

        # செலக்ட் பாக்ஸ் ஆப்ஷன்ஸ்
        all_class_names = [a['class_name'] for a in t_allots]
        existing = [str(x) for x in st.session_state.draft_tt.values() if x]
        final_options = sorted(list(set([""] + all_class_names + existing)))

        edited_df = st.data_editor(
            df_grid,
            column_config={p: st.column_config.SelectboxColumn(p, options=final_options, width="small") for p in periods},
            use_container_width=True, num_rows="fixed"
        )
        
        for d_short, row in edited_df.iterrows():
            day = next(d for d in days if d.startswith(d_short))
            for p in periods: st.session_state.draft_tt[(day, int(p))] = row[p]

        # SAVE BUTTON
        if st.button("🚀 அட்டவணையைச் சேமி"):
            supabase.table("weekly_timetable").delete().eq("teacher_id", t_id).execute()
            new_entries = []
            for (d, p), cls in st.session_state.draft_tt.items():
                if cls and str(cls).strip() != "" and not pd.isna(cls):
                    staff = next((a for a in t_allots if a['class_name'] == cls), None)
                    if staff:
                        new_entries.append({
                            "class_name": str(cls), "day_of_week": str(d), "period_number": int(p),
                            "teacher_id": int(t_id), "teacher_name": str(sel_t['full_name']),
                            "subject_name": str(staff['subject_name'])
                        })
            if new_entries: supabase.table("weekly_timetable").insert(new_entries).execute()
            st.success("சேமிக்கப்பட்டது!")
            st.rerun()

    # --- 5. ஒதுக்கீடு விவரம் ---
    with side_col:
        st.markdown("##### 🏷️ ஒதுக்கீடு விவரம் (FN/AN)")
        for a in t_allots:
            cls = a['class_name']
            flat_vals = list(st.session_state.draft_tt.values())
            rem = a['periods_per_week'] - flat_vals.count(cls)
            fn = sum(1 for (d, p), c in st.session_state.draft_tt.items() if c == cls and int(p) <= 4)
            an = sum(1 for (d, p), c in st.session_state.draft_tt.items() if c == cls and int(p) > 4)
            st.markdown(f"**{cls}** | மீதம்: {rem}<br><small>FN:{fn} | AN:{an}</small>", unsafe_allow_html=True)

    # --- 6. வகுப்பு வாரியான அட்டவணை ---
    st.divider()
    st.markdown("### 🏫 வகுப்பு வாரியான கால அட்டவணை")
    unique_classes = sorted(list(set([a['class_name'] for a in allot_data])))
    db_list_new = supabase.table("weekly_timetable").select("*").execute().data

    def style_table(df):
        return df.style.set_table_styles([
            {'selector': 'th.row_heading', 'props': [('background-color', '#f0f2f6')]},
            {'selector': 'th.col_heading', 'props': [('background-color', '#1f77b4'), ('color', 'white')]}
        ])

    for i in range(0, len(unique_classes), 3):
        cols = st.columns(3)
        for j, cls in enumerate(unique_classes[i:i+3]):
            with cols[j]:
                st.markdown(f"**வகுப்பு: {cls}**")
                df_cls = pd.DataFrame(index=[d[:3] for d in days], columns=periods).fillna("-")
                for entry in db_list_new:
                    if cls in [c.strip() for c in str(entry['class_name']).split("&")]:
                        short_t = entry['teacher_name'].split('(')[-1].replace(')', '')[:2]
                        df_cls.at[entry['day_of_week'][:3], str(entry['period_number'])] = f"{entry['subject_name'][:3]}-{short_t}"
                st.write(style_table(df_cls).to_html(), unsafe_allow_html=True)
