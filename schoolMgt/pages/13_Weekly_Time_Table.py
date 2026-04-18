import streamlit as st
import pandas as pd
import hashlib
from supabase import create_client, Client

# --- 1. SUPABASE CONNECTION ---
try:
    url, key = st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(url, key)
except:
    st.error("Connection Error!")
    st.stop()

st.set_page_config(page_title="Smart Timetable Editor", layout="wide")

# CSS: கச்சிதமான சில்லுகள்
st.markdown("""
    <style>
    .staff-chip {
        display: inline-block; padding: 4px 10px; margin: 4px;
        border-radius: 15px; font-size: 12px; font-weight: bold;
        border: 1px solid #999; color: #333; box-shadow: 1px 1px 3px rgba(0,0,0,0.1);
    }
    </style>
    """, unsafe_allow_html=True)

def get_color(text):
    if not text: return "#ffffff"
    hash_obj = hashlib.md5(text.encode()).hexdigest()
    return f'#{(int(hash_obj[:2],16)%40)+210:02x}{(int(hash_obj[2:4],16)%40)+210:02x}{(int(hash_obj[4:6],16)%40)+210:02x}'

# --- ⚡ FETCH DATA ---
@st.cache_data(ttl=2)
def get_data():
    allot = supabase.table("staff_allotment").select("*").execute()
    time_db = supabase.table("weekly_timetable").select("*").execute()
    classes = supabase.table("classes").select("class_name").order("class_name").execute()
    return allot.data, time_db.data, [c['class_name'] for c in classes.data]

allot_data, db_list, class_list = get_data()

# --- 🏗️ LAYOUT ---
main_col, side_col = st.columns([1.5, 0.5])

with main_col:
    selected_class = st.selectbox("வகுப்பைத் தேர்வு செய்க:", ["-- Select Class --"] + class_list)

# --- 📝 PREPARE INITIAL DATA ---
if selected_class != "-- Select Class --":
    days_short = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
    days_full = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
    periods = [str(i) for i in range(1, 9)]
    day_map = dict(zip(days_short, days_full))

    # காலி DataFrame
    df_init = pd.DataFrame(index=days_short, columns=periods).fillna("")
    
    # தரவுதளத்தில் இருந்து ஏற்கனவே உள்ளதை எடுத்தல்
    for e in db_list:
        if e['class_name'] == selected_class:
            d_short = e['day_of_week'][:3]
            if d_short in days_short and str(e['period_number']) in periods:
                label = f"{e['subject_name']} - {e['teacher_name'].split('(')[-1].replace(')', '')}"
                df_init.at[d_short, str(e['period_number'])] = label

    # --- 📝 DATA EDITOR ---
    my_staff_opts = sorted(list(set([f"{a['subject_name']} - {a['teacher_name'].split('(')[-1].replace(')', '')}" 
                                    for a in allot_data if a['class_name'] == selected_class])))
    my_staff_opts = [""] + my_staff_opts

    with main_col:
        edited_df = st.data_editor(
            df_init,
            column_config={p: st.column_config.SelectboxColumn(p, options=my_staff_opts, width="small") for p in periods},
            use_container_width=True,
            num_rows="fixed",
            key="tt_editor"
        )

    # --- 🏷️ DYNAMIC SIDE CHIPS (நேரடி கணக்கீடு) ---
    with side_col:
        st.markdown("##### 🏷️ ஆசிரியர் நிலை (Status)")
        class_staff = [a for a in allot_data if a['class_name'] == selected_class]
        
        # திரையில் (Edited DF) எத்தனை முறை ஒவ்வொரு ஆசிரியரும் இருக்கிறார் என எண்ணுதல்
        flat_list = edited_df.values.flatten()
        
        if class_staff:
            for s in class_staff:
                t_short = s['teacher_name'].split('(')[-1].replace(')', '')
                label_to_find = f"{s['subject_name']} - {t_short}"
                
                # திரையில் உள்ள எண்ணிக்கை
                current_on_screen = list(flat_list).count(label_to_find)
                rem = s['periods_per_week'] - current_on_screen
                
                bg = get_color(s['subject_name'])
                
                # எண்ணிக்கை 0 ஆனால் சிவப்பு அல்லது மங்கிய நிறத்தில் காட்டலாம்
                if rem > 0:
                    st.markdown(f"""<div class="staff-chip" style="background-color: {bg}; border-left: 5px solid green;">
                        {s['subject_name']} - {t_short} | மீதம்: {rem}</div>""", unsafe_allow_html=True)
                elif rem == 0:
                    st.markdown(f"""<div class="staff-chip" style="background-color: #e0e0e0; color: #999; border-left: 5px solid gray;">
                        {s['subject_name']} - {t_short} | முடிந்தது ✅</div>""", unsafe_allow_html=True)
                else:
                    st.markdown(f"""<div class="staff-chip" style="background-color: #ffcccc; color: red; border-left: 5px solid red;">
                        {s['subject_name']} - {t_short} | கூடுதல்: {abs(rem)} ⚠️</div>""", unsafe_allow_html=True)
        else:
            st.caption("ஒதுக்கீடு இல்லை")

    # --- 🚀 SAVE BUTTON ---
    with main_col:
        if st.button("🚀 சரிபார்த்துச் சேமி (Save)", type="primary", use_container_width=True):
            # (சேமிக்கும் அதே பழைய லாஜிக்...)
            with st.spinner("சேமிக்கப்படுகிறது..."):
                supabase.table("weekly_timetable").delete().eq("class_name", selected_class).execute()
                new_data = []
                for d_short, row in edited_df.iterrows():
                    for p_num in periods:
                        val = row[p_num]
                        if val:
                            sub_n = val.split(" - ")[0]
                            t_s = val.split(" - ")[-1]
                            staff = next((a for a in allot_data if a['class_name'] == selected_class and a['subject_name'] == sub_n and t_s in a['teacher_name']), None)
                            if staff:
                                new_data.append({
                                    "class_name": selected_class, "day_of_week": day_map[d_short], "period_number": int(p_num),
                                    "teacher_id": staff['teacher_id'], "teacher_name": staff['teacher_name'], "subject_name": staff['subject_name']
                                })
                if new_data:
                    supabase.table("weekly_timetable").insert(new_data).execute()
                st.success("வெற்றிகரமாகச் சேமிக்கப்பட்டது!")
                st.cache_data.clear()
