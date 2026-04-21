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

@st.cache_data(ttl=10)
def get_data():
    allot = supabase.table("staff_allotment").select("*").execute()
    time_db = supabase.table("weekly_timetable").select("*").execute()
    teachers = supabase.table("teachers").select("emis_id, short_name, full_name").order("full_name").execute()
    return allot.data, time_db.data, teachers.data

allot_data, db_list, teach_data = get_data()

st.title("👨‍🏫 ஆசிரியர் கால அட்டவணை மேலாண்மை")
if 'draft_tt' not in st.session_state: st.session_state.draft_tt = {}

t_opts = {f"{t['full_name']} ({t['short_name']})": t for t in teach_data}
sel_t_label = st.selectbox("ஆசிரியரைத் தேர்வு செய்க:", ["-- Select Teacher --"] + list(t_opts.keys()))

if sel_t_label != "-- Select Teacher --":
    sel_t = t_opts[sel_t_label]
    t_id = sel_t['emis_id']
    t_allots = [a for a in allot_data if a['teacher_id'] == t_id]
    
    if st.session_state.get('active_t_id') != t_id:
        st.session_state.draft_tt = {}
        st.session_state.active_t_id = t_id
        for e in db_list:
            if e['teacher_id'] == t_id:
                st.session_state.draft_tt[(e['day_of_week'], e['period_number'])] = e['class_name']

    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
    periods = [str(i) for i in range(1, 9)]

    # --- 4. DATA EDITOR (Strict Limit Enforcement) ---
    main_col, side_col = st.columns([0.7, 0.3])
    with main_col:
        df_grid = pd.DataFrame(index=[d[:3] for d in days], columns=periods).fillna("")
        for (d, p), cls in st.session_state.draft_tt.items():
            df_grid.at[d[:3], str(p)] = cls

        flat_tt = list(st.session_state.draft_tt.values())
        
        # மீதம் உள்ள வகுப்புகளை மட்டும் பட்டியலில் காட்டுதல்
        allowed_options = []
        for a in t_allots:
            rem = a['periods_per_week'] - flat_tt.count(a['class_name'])
            if rem > 0 or flat_tt.count(a['class_name']) > 0:
                allowed_options.append(a['class_name'])

        final_options = sorted(list(set([""] + allowed_options)))

        edited_df = st.data_editor(
            df_grid, 
            column_config={p: st.column_config.SelectboxColumn(p, options=final_options, width="small") for p in periods}, 
            use_container_width=True, num_rows="fixed"
        )
        
        for d_short, row in edited_df.iterrows():
            day = next(d for d in days if d.startswith(d_short))
            for p in periods: st.session_state.draft_tt[(day, int(p))] = row[p]

        if st.button("🚀 அட்டவணையைச் சேமி"):
            supabase.table("weekly_timetable").delete().eq("teacher_id", t_id).execute()
            new_entries = [{"class_name": cls, "day_of_week": d, "period_number": p, "teacher_id": t_id, 
                           "teacher_name": sel_t['full_name'], "subject_name": next((a['subject_name'] for a in t_allots if a['class_name'] == cls), "")}
                          for (d, p), cls in st.session_state.draft_tt.items() if cls and cls != "" and not pd.isna(cls)]
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
            st.markdown(f"**{cls}** | மீதம்: {rem} ==> FN:{fn} | AN:{an}", unsafe_allow_html=True)

    # --- 6. வகுப்பு வாரியான கால அட்டவணை ---
    st.divider()
    st.markdown("### 🏫 வகுப்பு வாரியான கால அட்டவணை")
    unique_classes = sorted(list(set([a['class_name'] for a in allot_data])))
    db_list_new = supabase.table("weekly_timetable").select("*").execute().data

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
                
                # அட்டவணை வண்ணம்
                styled_df = df_cls.style.set_table_styles([
                    {'selector': 'th', 'props': [('background-color', '#1f77b4'), ('color', 'white')]},
                    {'selector': 'th.row_heading', 'props': [('background-color', '#f0f2f6'), ('color', 'black')]}
                ])
                st.write(styled_df.to_html(), unsafe_allow_html=True)
