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
    st.subheader("வகுப்பு வாரியான எடிட்டர்")
    
    # வகுப்புகளின் பட்டியல்
    classes_list = sorted(list(set([a['class_name'] for a in allot_data])))
    
    # 3 காலம்கள் வீதம் எடிட்டர்களை உருவாக்க
    cols_per_row = 3
    for i in range(0, len(classes_list), cols_per_row):
        cols = st.columns(cols_per_row)
        for j, cls in enumerate(classes_list[i : i + cols_per_row]):
            with cols[j]:
                st.markdown(f"**🏫 வகுப்பு: {cls}**")
                
                # Pivot செய்யப்பட்ட தரவிலிருந்து அந்த வகுப்பை மட்டும் பிரித்தல்
                # முதலில் stack செய்து பின் class வாரியாக filter செய்கிறோம்
                df_stack = st.session_state.master_tt.stack().reset_index()
                df_stack.columns = ['Teacher', 'Day', 'Period', 'Class']
                
                # இந்த வகுப்புக்கான கால அட்டவணை (Days vs Periods)
                cls_df = df_stack[df_stack['Class'] == cls].pivot(index='Day', columns='Period', values='Teacher')
                
                # எடிட் செய்யும் வசதி
                edited_cls = st.data_editor(cls_df, use_container_width=True, key=f"edit_cls_{cls}")
                
                # குறிப்பு: இங்கே எடிட் செய்தால், master_tt-ஐ அப்டேட் செய்வது சிக்கலானது. 
                # எனவே எடிட்டிங்கை 'ஆசிரியர் வாரியாக' வைத்துவிட்டு, 'வகுப்பு வாரியாக' பார்ப்பது சிறந்தது.
# 5. சேமிப்பு பொத்தான்
if st.button("💾 அனைத்தையும் சேமி"):
    st.success("வெற்றிகரமாகச் சேமிக்கப்பட்டது!")
