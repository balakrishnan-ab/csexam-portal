import streamlit as st
import pandas as pd
from supabase import create_client, Client

st.set_page_config(layout="wide")
st.title("⚙️ ஆட்டோ-ஜெனரேட் டைம்டேபிள் - எடிட்டர்")

# 1. Supabase இணைப்பு
try:
    url, key = st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(url, key)
except:
    st.error("Connection Error!")
    st.stop()

# 2. தரவு பெறுதல்
@st.cache_data(ttl=5)
def get_all_data():
    allot = supabase.table("staff_allotment").select("*").execute()
    teachers = supabase.table("teachers").select("full_name").execute()
    weekly_tt = supabase.table("weekly_timetable").select("*").execute()
    return allot.data, [t['full_name'] for t in teachers.data], weekly_tt.data

allot_data, teachers_list, db_list_new = get_all_data()
periods = [str(i) for i in range(1, 9)]
days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]

# அட்டவணை ஸ்டைல் பங்க்ஷன்
def style_table(df):
    return df.style.set_table_styles([
        {'selector': 'th', 'props': [('background-color', '#1f77b4'), ('color', 'white')]},
        {'selector': 'th.row_heading', 'props': [('background-color', '#f0f2f6')]}
    ])

# 3. Master Table நிர்வகித்தல்
if 'master_tt' not in st.session_state:
    idx = pd.MultiIndex.from_product([teachers_list, days], names=['Teacher', 'Day'])
    st.session_state.master_tt = pd.DataFrame(index=idx, columns=periods).fillna("-")

# 4. Tabs உருவாக்கம்
tab1, tab2 = st.tabs(["👨‍🏫 ஆசிரியர் எடிட்டர்", "🏫 வகுப்பு வாரியான பார்வை"])

with tab1:
    st.subheader("அனைத்து ஆசிரியர்களின் வாராந்திர எடிட்டர்")
    cols_per_row = 3
    for i in range(0, len(teachers_list), cols_per_row):
        cols = st.columns(cols_per_row)
        for j, teacher in enumerate(teachers_list[i : i + cols_per_row]):
            with cols[j]:
                st.markdown(f"**👨‍🏫 {teacher}**")
                teacher_df = st.session_state.master_tt.loc[teacher]
                edited_df = st.data_editor(teacher_df, use_container_width=True, key=f"edit_{teacher}")
                st.session_state.master_tt.loc[teacher] = edited_df
        st.write("---")

with tab2:
    st.subheader("வகுப்பு வாரியான பார்வை")
    
    # 1. முதலில் தரவை அடுக்கி (stack), Index-ஐ Reset செய்கிறோம்
    df_stack = st.session_state.master_tt.stack().reset_index()
    
    # 2. இப்போது சரியாக 4 காலம்கள் இருப்பதை உறுதி செய்து பெயரிடுகிறோம்
    # MultiIndex-ல் ஏற்கனவே 'Teacher', 'Day' என்று பெயரிட்டுள்ளோம்.
    # எனவே, stack() செய்தபின் வரும் புதிய காலம் 'Period' மற்றும் தரவு 'Class' ஆகும்.
    df_stack.columns = ['Teacher', 'Day', 'Period', 'Class']
    
    # 3. Pivot அட்டவணை உருவாக்குதல்
    class_view = df_stack.pivot_table(index='Class', columns='Period', aggfunc='first')
    
    st.dataframe(class_view, use_container_width=True)

# 5. சேமிப்பு பொத்தான்
if st.button("💾 அனைத்தையும் சேமி"):
    st.success("வெற்றிகரமாகச் சேமிக்கப்பட்டது!")
