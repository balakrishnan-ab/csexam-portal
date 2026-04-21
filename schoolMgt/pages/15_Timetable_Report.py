import streamlit as st
import pandas as pd
from supabase import create_client

# Supabase இணைப்பு
url, key = st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

st.header("👨‍🏫 ஆசிரியர் வாரியான விரிவான ஒதுக்கீடு")

# தரவுகளைப் பெறுதல்
allot_data = supabase.table("staff_allotment").select("*").execute().data
group_data = supabase.table("combined_groups").select("*").execute().data
class_data = supabase.table("classes").select("class_name").execute().data

df_allot = pd.DataFrame(allot_data)
df_groups = pd.DataFrame(group_data)
all_base_classes = [c['class_name'] for c in class_data]

# தரவை ஆசிரியர்களுக்கு ஏற்ப விரிவுபடுத்துதல் (Expand Logic)
teacher_expanded = []
for _, row in df_allot.iterrows():
    allot_class = str(row['class_name'])
    
    # அடிப்படை வகுப்பா அல்லது குழுவா எனப் பிரித்தல்
    if allot_class in all_base_classes:
        teacher_expanded.append(row.to_dict())
    else:
        # குழுவாக இருந்தால், அந்த குழுவில் உள்ள ஒவ்வொரு வகுப்பையும் பிரித்தல்
        group = df_groups[df_groups['group_name'] == allot_class]
        if not group.empty:
            class_list = group.iloc[0]['class_list']
            for cls in class_list:
                row_dict = row.to_dict()
                row_dict['class_name'] = cls
                teacher_expanded.append(row_dict)

df_teacher_split = pd.DataFrame(teacher_expanded)
teachers = sorted(df_teacher_split['teacher_name'].unique())

# அட்டவணைகளை அடுக்குதல்
cols = st.columns(3)
for i, teacher in enumerate(teachers):
    with cols[i % 3]:
        t_df = df_teacher_split[df_teacher_split['teacher_name'] == teacher][['class_name', 'subject_name', 'periods_per_week']]
        total_t = t_df['periods_per_week'].sum()
        
        st.write(f"**{teacher}**")
        table_df = t_df.rename(columns={'class_name': 'வகுப்பு', 'subject_name': 'பாடம்', 'periods_per_week': 'மணி'})
        total_row = pd.DataFrame([['-', 'Total', total_t]], columns=['வகுப்பு', 'பாடம்', 'மணி'])
        st.table(pd.concat([table_df, total_row]))
