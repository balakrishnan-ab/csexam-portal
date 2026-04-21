import streamlit as st
import pandas as pd
from supabase import create_client

# Supabase இணைப்பு
url, key = st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

st.set_page_config(layout="wide")
st.header("🏫 வகுப்பு வாரியான ஒதுக்கீடு (தனித்தனி வகுப்புகள்)")

# 1. தரவுகளைப் பெறுதல்
allot_data = supabase.table("staff_allotment").select("*").execute().data
group_data = supabase.table("combined_groups").select("*").execute().data
class_data = supabase.table("classes").select("class_name").execute().data

df_allot = pd.DataFrame(allot_data)
df_groups = pd.DataFrame(group_data)
all_base_classes = [c['class_name'] for c in class_data]

# 2. வகுப்பு வாரியான தரவை விரிவுபடுத்துதல் (Expand Logic)
expanded_data = []

for _, row in df_allot.iterrows():
    allot_class = str(row['class_name'])
    
    # allot_class என்பது அடிப்படை வகுப்பா அல்லது குழுவா எனப் பார்க்கவும்
    if allot_class in all_base_classes:
        # நேரடியாக அடிப்படை வகுப்பு
        expanded_data.append(row.to_dict())
    else:
        # இது ஒரு குழு (Group), எனவே combined_groups அட்டவணையில் தேடவும்
        group = df_groups[df_groups['group_name'] == allot_class]
        if not group.empty:
            # அந்த குழுவில் உள்ள ஒவ்வொரு வகுப்புக்கும் ஆசிரியரைச் சேர்க்கவும்
            class_list = group.iloc[0]['class_list'] # இது ஒரு list ["11-C", "11-D"]
            for cls in class_list:
                row_dict = row.to_dict()
                row_dict['class_name'] = cls # வகுப்பை மாற்றவும்
                expanded_data.append(row_dict)

df_split = pd.DataFrame(expanded_data)

# 3. அட்டவணைகளை அடுக்குதல்
classes = sorted(df_split['class_name'].unique())
cols = st.columns(3)

for i, cls in enumerate(classes):
    with cols[i % 3]:
        c_df = df_split[df_split['class_name'] == cls][['teacher_name', 'subject_name', 'periods_per_week']]
        total_c = c_df['periods_per_week'].sum()
        
        st.write(f"**வகுப்பு: {cls}**")
        table_df = c_df.rename(columns={'teacher_name': 'ஆசிரியர்', 'subject_name': 'பாடம்', 'periods_per_week': 'மணி'})
        total_row = pd.DataFrame([['-', 'Total', total_c]], columns=['ஆசிரியர்', 'பாடம்', 'மணி'])
        st.table(pd.concat([table_df, total_row]))
