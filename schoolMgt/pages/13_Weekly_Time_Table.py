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

st.set_page_config(page_title="Strict Timetable Editor", layout="wide")

# CSS: கச்சிதமான சில்லுகள் மற்றும் எச்சரிக்கை வண்ணம்
st.markdown("""
    <style>
    .staff-chip {
        display: inline-block; padding: 4px 10px; margin: 4px;
        border-radius: 15px; font-size: 12px; font-weight: bold;
        border: 1px solid #999; color: #333;
    }
    .stDataEditor [data-testid="stHeader"] { font-size: 14px !important; font-weight: bold; }
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
    # திரையில் உள்ள எண்ணிக்கையைப் பொறுத்து ஆப்ஷன்களைக் குறைத்தல்
    class_staff = [a for a in allot_data if a['class_name'] == selected_class]
    
    with main_col:
        # தற்காலிகமாக எடிட்டரைக் காட்டுதல்
        edited_df = st.data_editor(
            df_init,
            column_config={p: st.column_config.SelectboxColumn(p, width="small") for p in periods},
            use_container_width=True,
            num_rows="fixed",
            key="tt_editor"
        )

    # --- 🏷️ DYNAMIC SIDE CHIPS & VALIDATION ---
    with side_col:
        st.markdown("##### 🏷️ ஆசிரியர் நிலை (Status)")
        flat_list = list(edited_df.values.flatten())
        
        valid_submission = True
        
        for s in class_staff:
            t_short = s['teacher_name'].split('(')[-1].replace(')', '')
            label = f"{s['subject_name']} - {t_short}"
            
            current_count = flat_list.count(label)
            rem = s['periods_per_week'] - current_count
            bg = get_color(s['subject_name'])
            
            if rem > 0:
                st.markdown(f'<div class="staff-chip" style="background:{bg}; border-left:5px solid blue;">{label} | மீதம்: {rem}</div>', unsafe_allow_html=True)
            elif rem == 0:
                st.markdown(f'<div class="staff-chip" style="background:#e0e0e0; color:#888; border-left:5px solid gray;">{label} | முடிந்தது ✅</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="staff-chip" style="background:#ffcccc; color:red; border-left:5px solid red;">{label} | கூடுதல்: {abs(rem)} ⚠️</div>', unsafe_allow_html=True)
                valid_submission = False # கூடுதல் இருந்தால் சேமிக்க முடியாது

        # --- 🧪 PRACTICAL CHECK (Double Periods) ---
        st.markdown("##### 🧪 செய்முறை வகுப்பு ஆய்வு")
        for day in days_short:
            day_row = edited_df.loc[day].values
            for i in range(len(day_row)-1):
                # அடுத்தடுத்த கட்டங்களில் ஒரே பாடம் இருந்தால் அது Double Period
                if day_row[i] != "" and day_row[i] == day_row[i+1]:
                    st.caption(f"✅ {day}: {i+1}-{i+2} தொடர் பாடவேளை")

    # --- 🚀 SAVE BUTTON ---
    with main_col:
        if st.button("🚀 சரிபார்த்துச் சேமி (Save)", type="primary", use_container_width=True):
            if not valid_submission:
                st.error("பிழை: சில ஆசிரியர்களுக்கு அனுமதிக்கப்பட்ட எண்ணிக்கையை விட அதிகமாக பாடவேளைகள் உள்ளன. அவற்றைச் சரிசெய்து பின் சேமிக்கவும்.")
            else:
                with st.spinner("சேமிக்கப்படுகிறது..."):
                    # Delete and Bulk Insert
                    supabase.table("weekly_timetable").delete().eq("class_name", selected_class).execute()
                    new_data = []
                    for d_short, row in edited_df.iterrows():
                        for p_idx, p_num in enumerate(periods):
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
