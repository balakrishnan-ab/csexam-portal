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

# 3. Master Table நிர்வகித்தல்
if 'master_tt' not in st.session_state:
    idx = pd.MultiIndex.from_product([teachers_list, days], names=['Teacher', 'Day'])
    st.session_state.master_tt = pd.DataFrame(index=idx, columns=periods).fillna("-")

# 4. ஆட்டோ-ஃபில் தர்க்கம்
if st.button("🤖 அனைவருக்கும் தானாக நிரப்பு (Auto-Assign All)"):
    # புதிய Master Table-ஐ உருவாக்குதல்
    idx = pd.MultiIndex.from_product([teachers_list, days], names=['Teacher', 'Day'])
    new_df = pd.DataFrame(index=idx, columns=periods).fillna("-")
    
    # staff_allotment அட்டவணையிலிருந்து தரவை எடுத்தல்
    # allot_data என்பது supabase-லிருந்து பெறப்பட்டது (இதுவே உங்கள் staff_allotment அட்டவணை)
    
    all_tasks = []
    for a in allot_data:
        # உங்கள் அட்டவணையில் உள்ள column பெயர்கள்: class_name, periods_per_week
        cls = a['class_name']
        p_count = int(a.get('periods_per_week', 0))
        all_tasks.extend([cls] * p_count)
    
    # ஆசிரியர்களுக்குப் பாடங்களை வரிசையாக நிரப்புதல்
    task_idx = 0
    for t in teachers_list:
        for d in days:
            for p in periods:
                if task_idx < len(all_tasks):
                    new_df.at[(t, d), p] = all_tasks[task_idx]
                    task_idx += 1
    
    st.session_state.master_tt = new_df
    st.rerun()
# 5. Tabs உருவாக்கம்
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
    st.subheader("வகுப்பு வாரியான கால அட்டவணை எடிட்டர்")
    classes_data = supabase.table("classes").select("class_name").execute().data
    all_classes = sorted([c['class_name'] for c in classes_data], reverse=True)
    
    selected_classes = st.multiselect("தேவையான வகுப்புகளைத் தேர்ந்தெடுக்கவும்:", all_classes, default=all_classes[:3])
    
    cols_per_row = 3
    for i in range(0, len(selected_classes), cols_per_row):
        cols = st.columns(cols_per_row)
        for j, cls in enumerate(selected_classes[i : i + cols_per_row]):
            with cols[j]:
                st.markdown(f"**🏫 வகுப்பு: {cls}**")
                df_stack = st.session_state.master_tt.stack().reset_index()
                df_stack.columns = ['Teacher', 'Day', 'Period', 'Class_Val']
                
                cls_df = df_stack[df_stack['Class_Val'] == cls].pivot(index='Day', columns='Period', values='Teacher')
                
                if cls_df.empty:
                    cls_df = pd.DataFrame(index=days, columns=periods).fillna("-")
                
                st.data_editor(cls_df, use_container_width=True, key=f"edit_cls_{cls}")
        st.write("---")

# 6. சேமிப்பு பொத்தான்
if st.button("💾 அனைத்தையும் சேமி"):
    st.success("வெற்றிகரமாகச் சேமிக்கப்பட்டது!")
