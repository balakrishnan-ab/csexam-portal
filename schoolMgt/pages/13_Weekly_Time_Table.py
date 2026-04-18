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

st.set_page_config(page_title="Dynamic Strict Editor", layout="wide")

# CSS: சில்லுகள்
st.markdown("""
    <style>
    .staff-chip {
        display: inline-block; padding: 4px 10px; margin: 4px;
        border-radius: 15px; font-size: 11px; font-weight: bold;
        border: 1px solid #999;
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

if selected_class != "-- Select Class --":
    days_short = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
    days_full = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
    periods = [str(i) for i in range(1, 9)]
    day_map = dict(zip(days_short, days_full))

    # 1. ஆரம்ப கால தரவுத் தயாரிப்பு
    if f"df_{selected_class}" not in st.session_state:
        df_init = pd.DataFrame(index=days_short, columns=periods).fillna("")
        for e in db_list:
            if e['class_name'] == selected_class:
                d_short = e['day_of_week'][:3]
                if d_short in days_short and str(e['period_number']) in periods:
                    df_init.at[d_short, str(e['period_number'])] = f"{e['subject_name']} - {e['teacher_name'].split('(')[-1].replace(')', '')}"
        st.session_state[f"df_{selected_class}"] = df_init

    # 2. 🏷️ DYNAMIC FILTER LOGIC (வலதுபுறம்)
    with side_col:
        st.markdown("##### 🏷️ ஆசிரியர் நிலை")
        class_staff = [a for a in allot_data if a['class_name'] == selected_class]
        current_df = st.session_state[f"df_{selected_class}"]
        flat_list = list(current_df.values.flatten())
        
        available_options = [""]
        
        for s in class_staff:
            t_short = s['teacher_name'].split('(')[-1].replace(')', '')
            label = f"{s['subject_name']} - {t_short}"
            
            used = flat_list.count(label)
            rem = s['periods_per_week'] - used
            
            if rem > 0:
                # 🎯 மீதம் இருந்தால் மட்டுமே பட்டியலில் சேரும்
                available_options.append(label)
                bg = get_color(s['subject_name'])
                st.markdown(f'<div class="staff-chip" style="background:{bg}; border-left:5px solid blue;">{label} | மீதம்: {rem}</div>', unsafe_allow_html=True)
            else:
                # 🚫 எண்ணிக்கை முடிந்தால் மங்கலாகக் காட்டி, பட்டியலில் இருந்து நீக்கப்படும்
                st.markdown(f'<div class="staff-chip" style="background:#eee; color:#aaa; border-left:5px solid gray;">{label} | முடிந்தது ✅</div>', unsafe_allow_html=True)

    # 3. 📝 DYNAMIC DATA EDITOR
    with main_col:
        st.info("குறிப்பு: ஒரு ஆசிரியரின் பாடவேளை எண்ணிக்கை முடிந்துவிட்டால், அவர் பெயர் பட்டியலில் இருந்து தானாகவே மறைந்துவிடும்.")
        
        # எடிட்டரில் பாடவேளைகளைத் தேர்வு செய்தல்
        edited_df = st.data_editor(
            st.session_state[f"df_{selected_class}"],
            column_config={p: st.column_config.SelectboxColumn(p, options=available_options, width="small") for p in periods},
            use_container_width=True,
            num_rows="fixed",
            key=f"editor_{selected_class}"
        )
        
        # மாற்றங்களை உடனுக்குடன் சேமிக்க (Sync Session State)
        st.session_state[f"df_{selected_class}"] = edited_df

    # 4. 🚀 SAVE TO DATABASE
    with main_col:
        if st.button("🚀 சரிபார்த்துச் சேமி (Save)", type="primary", use_container_width=True):
            with st.spinner("சேமிக்கப்படுகிறது..."):
                supabase.table("weekly_timetable").delete().eq("class_name", selected_class).execute()
                new_data = []
                for d_short, row in edited_df.iterrows():
                    for p_num in periods:
                        val = row[p_num]
                        if val:
                            sub_n, t_s = val.split(" - ")
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
