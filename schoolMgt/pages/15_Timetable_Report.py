import streamlit as st
import pandas as pd
from supabase import create_client

# Supabase இணைப்பு
url, key = st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

st.set_page_config(layout="wide")
st.title("📊 ஆசிரியர் மற்றும் வகுப்பு ஒதுக்கீடு அறிக்கைகள்")

allot_data = supabase.table("staff_allotment").select("*").execute().data
group_data = supabase.table("combined_groups").select("*").execute().data
df_allot = pd.DataFrame(allot_data)
df_groups = pd.DataFrame(group_data)

# Tabs உருவாக்குதல்
tab1, tab2 = st.tabs(["👨‍🏫 ஆசிரியர் ஒதுக்கீடு", "🏫 வகுப்பு வாரியான ஒதுக்கீடு"])

# 1. ஆசிரியர் வாரியான ஒதுக்கீடு (அப்படியே காட்டுதல்)
with tab1:
    st.header("ஆசிரியர் வாரியான பணிச்சுமை")
    teachers = sorted(df_allot['teacher_name'].unique())
    cols = st.columns(3)
    for i, teacher in enumerate(teachers):
        with cols[i % 3]:
            # ஆசிரியர் வாரியாக அப்படியே காட்டுதல் (பிரிப்பு தேவையில்லை)
            t_df = df_allot[df_allot['teacher_name'] == teacher][['class_name', 'subject_name', 'periods_per_week']]
            total_t = t_df['periods_per_week'].sum()
            
            st.write(f"**{teacher}**")
            table_df = t_df.rename(columns={'class_name': 'வகுப்பு', 'subject_name': 'பாடம்', 'periods_per_week': 'மணி'})
            total_row = pd.DataFrame([['-', 'Total', total_t]], columns=['வகுப்பு', 'பாடம்', 'மணி'])
            st.table(pd.concat([table_df, total_row]))

# --- வகுப்பு வாரியான ஒதுக்கீடு (திருத்தப்பட்ட விரிவான லாஜிக்) ---
    st.header("வகுப்பு வாரியான ஒதுக்கீடு (விரிவானது)")
    expanded_data = []
    
    for _, row in df_allot.iterrows():
        allot_class = str(row['class_name']).strip()
        
        # 'combined_groups' அட்டவணையில் அந்த வகுப்புப் பெயர் உள்ளதா எனச் சரிபார்க்கவும்
        group = df_groups[df_groups['group_name'] == allot_class]
        
        if not group.empty:
            # குழுவாக இருந்தால், அந்த குழுவில் உள்ள துல்லியமான வகுப்புப் பெயர்களை எடுக்கவும்
            # இங்குதான் A1, B1 எனப் பிரிந்து வரும்
            class_list = group.iloc[0]['class_list'] 
            for cls in class_list:
                expanded_data.append({
                    'class_name': str(cls).strip(), # துல்லியமான பெயர்
                    'teacher_name': row['teacher_name'], 
                    'subject_name': row['subject_name'], 
                    'periods': row['periods_per_week']
                })
        else:
            # நேரடியாக அடிப்படை வகுப்பு (A1, B1 போன்றவை இங்கு வரும்)
            expanded_data.append({
                'class_name': allot_class, 
                'teacher_name': row['teacher_name'], 
                'subject_name': row['subject_name'], 
                'periods': row['periods_per_week']
            })

    df_split = pd.DataFrame(expanded_data)
    
    # வகுப்புகளை அகரவரிசைப்படி வரிசைப்படுத்துதல்
    classes = sorted(df_split['class_name'].unique())
    
    cols = st.columns(3)
    for i, cls in enumerate(classes):
        with cols[i % 3]:
            # அந்த வகுப்புக்கு உரிய தரவை மட்டும் எடுத்தல்
            c_df = df_split[df_split['class_name'] == cls]
            total_c = c_df['periods'].sum()
            
            st.write(f"**வகுப்பு: {cls}**")
            table_df = c_df[['teacher_name', 'subject_name', 'periods']].rename(columns={'teacher_name': 'ஆசிரியர்', 'subject_name': 'பாடம்', 'periods': 'மணி'})
            
            # Total வரிசை
            total_row = pd.DataFrame([['-', 'Total', total_c]], columns=['ஆசிரியர்', 'பாடம்', 'மணி'])
            st.table(pd.concat([table_df, total_row]))
