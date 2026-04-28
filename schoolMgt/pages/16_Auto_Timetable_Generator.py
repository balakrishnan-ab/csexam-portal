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
    return allot.data, [t['full_name'] for t in teachers.data]

allot_data, teachers_list = get_all_data()
days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
periods = [str(i) for i in range(1, 9)]

# 3. ஆட்டோ-ஃபில் தர்க்கம்
if st.button("🤖 அனைவருக்கும் தானாக நிரப்பு (Auto-Assign All)"):
    new_df = pd.DataFrame(index=teachers_list, columns=periods).fillna("-")
    all_tasks = []
    for a in allot_data:
        all_tasks.extend([a['class_name']] * int(a.get('periods_per_week', 0)))
    
    idx = 0
    for teacher in teachers_list:
        for p in periods:
            if idx < len(all_tasks):
                new_df.at[teacher, p] = all_tasks[idx]
                idx += 1
    st.session_state.master_tt = new_df
    st.rerun()

# 4. Master Table நிர்வகித்தல்
if 'master_tt' not in st.session_state:
    st.session_state.master_tt = pd.DataFrame(index=teachers_list, columns=periods).fillna("-")

# 5. Tabs உருவாக்கம்
tab1, tab2 = st.tabs(["👨‍🏫 ஆசிரியர் வாரியாக", "🏫 வகுப்பு வாரியாக"])

with tab1:

    st.subheader("ஆசிரியர்களுக்கான வாராந்திர அட்டவணை (8 பாடவேளைகள்)")
    
    # 8 பாடவேளைகளை உறுதி செய்ய (1 to 8)
    periods_8 = [str(i) for i in range(1, 9)]
    
    for teacher in teachers_list:
        st.markdown(f"#### 👨‍🏫 ஆசிரியர்: {teacher}")
        
        # அந்த ஆசிரியரின் தரவை மட்டும் பிரித்தல்
        teacher_df = st.session_state.master_tt.loc[[teacher]]
        
        # 8 வேளைகள் இல்லை என்றால் அதைச் சேர்க்கவும் (எடிட்டரின் வசதிக்காக)
        for p in periods_8:
            if p not in teacher_df.columns:
                teacher_df[p] = "-"
        
        # அட்டவணை தோற்றம் (Styling)
        # காலங்களை மட்டும் பிரித்து காட்டுகிறோம்
        st.dataframe(teacher_df[periods_8], use_container_width=True)
        st.write("---")ி
with tab2:
    st.subheader("வகுப்பு வாரியான பார்வை")
    # மாஸ்டர் டேபிளை வகுப்பு வாரியாக மாற்றுதல் (Pivot Logic)
    df_stack = st.session_state.master_tt.stack().reset_index()
    df_stack.columns = ['Teacher', 'Period', 'Class']
    class_view = df_stack.pivot_table(index='Class', columns='Period', aggfunc='first')
    st.dataframe(class_view, use_container_width=True)

# 6. சேமிப்பு பொத்தான்
if st.button("💾 அனைத்தையும் சேமி"):
    st.success("வெற்றிகரமாகச் சேமிக்கப்பட்டது!")
    # இங்கே உங்கள் Supabase .upsert() தர்க்கத்தை சேர்க்கவும்
