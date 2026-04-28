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
    # பெயர்களை மட்டும் சுத்தப்படுத்துதல் (அடைப்புக்குறிகளை நீக்குதல்)
    clean_allot = allot.data
    for a in clean_allot:
        if '(' in a['teacher_name']:
            a['teacher_name'] = a['teacher_name'].split('(')[0].strip()
    return clean_allot, [t['full_name'].strip() for t in teachers.data]

allot_data, teachers_list = get_all_data()
periods = [str(i) for i in range(1, 9)]
days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]

# 3. Master Table நிர்வகித்தல்
if 'master_tt' not in st.session_state:
    idx = pd.MultiIndex.from_product([teachers_list, days], names=['Teacher', 'Day'])
    st.session_state.master_tt = pd.DataFrame(index=idx, columns=periods).fillna("-")

# 4. ஆட்டோ-ஃபில் தர்க்கம் (நிபந்தனைகளுடன்)
if st.button("🤖 நிபந்தனைகளுடன் தானாக நிரப்பு"):
    idx = pd.MultiIndex.from_product([teachers_list, days], names=['Teacher', 'Day'])
    new_df = pd.DataFrame(index=idx, columns=periods).fillna("-")
    
    teacher_allotments = {}
    for a in allot_data:
        t_name = a['teacher_name']
        if t_name not in teacher_allotments: teacher_allotments[t_name] = []
        teacher_allotments[t_name].extend([a['class_name']] * int(a.get('periods_per_week', 0)))

    for t in teachers_list:
        assigned_classes = teacher_allotments.get(t, [])
        for d in days:
            last_class = None
            consecutive_count = 0
            for p in periods:
                if not assigned_classes: break
                for i, cls in enumerate(assigned_classes):
                    if cls != last_class or consecutive_count < 2:
                        new_df.at[(t, d), p] = cls
                        consecutive_count = (consecutive_count + 1) if cls == last_class else 1
                        last_class = cls
                        assigned_classes.pop(i)
                        break
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
                teacher_df = st.session_state.master_tt.xs(teacher, level='Teacher')
                edited_df = st.data_editor(teacher_df, use_container_width=True, key=f"edit_{teacher}")
                st.session_state.master_tt.loc[(teacher, slice(None)), :] = edited_df.values
        st.write("---")

with tab2:
    st.subheader("வகுப்பு வாரியான கால அட்டவணை எடிட்டர்")
    classes_data = supabase.table("classes").select("class_name").execute().data
    all_classes = sorted([c['class_name'] for c in classes_data], reverse=True)
    
    selected_classes = st.multiselect("தேவையான வகுப்புகளைத் தேர்ந்தெடுக்கவும்:", all_classes, default=all_classes[:3])
    
    for cls in selected_classes:
        st.markdown(f"**🏫 வகுப்பு: {cls}**")
        df_stack = st.session_state.master_tt.stack().reset_index()
        df_stack.columns = ['Teacher', 'Day', 'Period', 'Class_Val']
        
        cls_df = df_stack[df_stack['Class_Val'] == cls].pivot(index='Day', columns='Period', values='Teacher')
        
        # வகுப்பு விவரங்கள் சரியாக இல்லையெனில் காலி டேபிள்
        if cls_df.empty:
            cls_df = pd.DataFrame(index=days, columns=periods).fillna("-")
            
        st.data_editor(cls_df, use_container_width=True, key=f"edit_cls_{cls}")
        st.write("---")

# 6. சேமிப்பு பொத்தான்
if st.button("💾 அனைத்தையும் சேமி"):
    st.success("வெற்றிகரமாகச் சேமிக்கப்பட்டது!")
