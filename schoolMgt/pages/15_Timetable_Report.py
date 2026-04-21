import streamlit as st
import pandas as pd
from supabase import create_client, Client

# --- SUPABASE CONNECTION ---
try:
    url, key = st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(url, key)
except:
    st.error("Connection Error!")
    st.stop()

st.set_page_config(page_title="Timetable Reports", layout="wide")
allot = supabase.table("staff_allotment").select("*").execute().data
df = pd.DataFrame(allot)

# --- 1. ஆசிரியர் வாரியான சிறு அட்டவணைகள் ---
st.header("👨‍🏫 ஆசிரியர் வாரியான ஒதுக்கீடு")
teachers = sorted(df['teacher_name'].unique())
cols1 = st.columns(3)

for i, teacher in enumerate(teachers):
    with cols1[i % 3]:
        t_df = df[df['teacher_name'] == teacher][['class_name', 'subject_name', 'periods_per_week']]
        # Total வரிசையைச் சேர்த்தல்
        total_periods = t_df['periods_per_week'].sum()
        st.write(f"**{teacher}**")
        st.table(pd.concat([t_df.rename(columns={'class_name': 'வகுப்பு', 'subject_name': 'பாடம்', 'periods_per_week': 'மணி'}), 
                           pd.DataFrame([['-', 'Total', total_periods]], columns=['வகுப்பு', 'பாடம்', 'மணி'])]))

st.divider()

# --- 2. வகுப்பு வாரியான சிறு அட்டவணைகள் ---
st.header("🏫 வகுப்பு வாரியான ஒதுக்கீடு")
# கம்பைன் வகுப்புகளைப் பிரிக்கும் லாஜிக் (Split '&')
all_classes = []
for row in df.itertuples():
    # வகுப்புப் பெயர்களைப் பிரித்தல்
    classes = [c.strip() for c in str(row.class_name).split("&")]
    for c in classes:
        all_classes.append({'class_name': c, 'teacher_name': row.teacher_name, 'subject_name': row.subject_name, 'periods': row.periods_per_week})

df_split = pd.DataFrame(all_classes)
classes = sorted(df_split['class_name'].unique())
cols2 = st.columns(3)

for i, cls in enumerate(classes):
    with cols2[i % 3]:
        c_df = df_split[df_split['class_name'] == cls][['teacher_name', 'subject_name', 'periods']]
        total_c = c_df['periods'].sum()
        st.write(f"**வகுப்பு: {cls}**")
        st.table(pd.concat([c_df.rename(columns={'teacher_name': 'ஆசிரியர்', 'subject_name': 'பாடம்', 'periods': 'மணி'}), 
                           pd.DataFrame([['-', 'Total', total_c]], columns=['ஆசிரியர்', 'பாடம்', 'மணி'])]))
