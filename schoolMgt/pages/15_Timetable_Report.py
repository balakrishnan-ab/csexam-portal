import streamlit as st
import pandas as pd
from supabase import create_client

# Supabase இணைப்பு
url, key = st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

st.title("📋 ஒதுக்கீடு சிறு அட்டவணை அறிக்கை")

# தரவை பெறுதல்
allot = supabase.table("staff_allotment").select("*").execute().data
df = pd.DataFrame(allot)

# 1. ஆசிரியர் வாரியான சிறு அட்டவணைகள்
st.subheader("👨‍🏫 ஆசிரியர் வாரியான ஒதுக்கீடு")
teachers = df['teacher_name'].unique()
cols1 = st.columns(3) # ஒரு வரிசையில் 3 அட்டவணைகள்

for i, teacher in enumerate(teachers):
    with cols1[i % 3]:
        t_df = df[df['teacher_name'] == teacher][['class_name', 'subject_name', 'periods_per_week']]
        st.write(f"**{teacher}**")
        st.table(t_df.rename(columns={'class_name': 'வகுப்பு', 'subject_name': 'பாடம்', 'periods_per_week': 'மணி'}))

st.divider()

# 2. வகுப்பு வாரியான சிறு அட்டவணைகள்
st.subheader("🏫 வகுப்பு வாரியான ஒதுக்கீடு")
classes = sorted(df['class_name'].unique())
cols2 = st.columns(3)

for i, cls in enumerate(classes):
    with cols2[i % 3]:
        c_df = df[df['class_name'] == cls][['teacher_name', 'subject_name', 'periods_per_week']]
        st.write(f"**வகுப்பு: {cls}**")
        st.table(c_df.rename(columns={'teacher_name': 'ஆசிரியர்', 'subject_name': 'பாடம்', 'periods_per_week': 'மணி'}))
