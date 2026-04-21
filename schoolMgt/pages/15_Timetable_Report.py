import streamlit as st
import pandas as pd
from supabase import create_client

# Supabase இணைப்பு
url, key = st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

st.set_page_config(page_title="Timetable Reports", layout="wide")
allot = supabase.table("staff_allotment").select("*").execute().data
df = pd.DataFrame(allot)

st.header("🏫 வகுப்பு வாரியான ஒதுக்கீடு (தனித்தனி வகுப்புகள்)")

# கம்பைன் வகுப்புகளைப் பிரித்து, தனித்தனி வகுப்புகளாக மாற்றும் லாஜிக்
def split_class_names(row):
    # வகுப்புகளைப் பிரித்தல் (உதாரணம்: '11-C & 11-D' -> ['11-C', '11-D'])
    # '&' அல்லது கமா இருந்தால் பிரிக்கவும்
    names = str(row['class_name']).replace('&', ',').split(',')
    return [name.strip() for name in names]

# புதிய விரிவான அட்டவணை தயாரிப்பு
expanded_data = []
for _, row in df.iterrows():
    splitted_classes = split_class_names(row)
    for cls in splitted_classes:
        # கம்பைன் வகுப்புப் பெயர்களைத் தவிர்த்து, உண்மையான வகுப்புப் பெயர்களை மட்டும் எடுத்தல்
        if len(cls) > 0 and 'ARTS' not in cls and 'SCI' not in cls: # உங்களுக்குத் தேவையில்லாத பெயர்களை இங்கே தவிர்க்கலாம்
            expanded_data.append({
                'class_name': cls,
                'teacher_name': row['teacher_name'],
                'subject_name': row['subject_name'],
                'periods': row['periods_per_week']
            })

df_split = pd.DataFrame(expanded_data)
classes = sorted(df_split['class_name'].unique())

# அட்டவணைகளை அடுக்குதல்
cols = st.columns(3)
for i, cls in enumerate(classes):
    with cols[i % 3]:
        c_df = df_split[df_split['class_name'] == cls][['teacher_name', 'subject_name', 'periods']]
        total_c = c_df['periods'].sum()
        
        st.write(f"**வகுப்பு: {cls}**")
        # அட்டவணை
        table_df = c_df.rename(columns={'teacher_name': 'ஆசிரியர்', 'subject_name': 'பாடம்', 'periods': 'மணி'})
        # Total வரிசை இணைத்தல்
        total_row = pd.DataFrame([['-', 'Total', total_c]], columns=['ஆசிரியர்', 'பாடம்', 'மணி'])
        st.table(pd.concat([table_df, total_row]))
