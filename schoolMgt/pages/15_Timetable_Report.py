import streamlit as st
import pandas as pd

# 1. மாதிரி தரவு (உங்களுக்குத் தகுந்தபடி இதை மாற்றிக் கொள்ளவும்)
teachers_data = {
    "Revathi (MR)-Tamil": {"11-Sci(TM)": 4, "12-Sci(TM)": 4, "11-Sci(EM)": 4, "12-Sci(EM)": 4, "11-Arts(TM)": 4, "12-Arts(TM)": 4},
    "M. Angamuthu (MA)-English": {"11-Sci(TM)": 4, "12-Sci(TM)": 4, "11-Sci(EM)": 4, "12-Sci(EM)": 4, "11-Arts(TM)": 4, "12-Arts(TM)": 4}
}

# 2. ஆசிரியர்களுக்கான சிறு அட்டவணைகள்
st.subheader("ஆசிரியர் ஒதுக்கீடு")
cols = st.columns(3) # 3 அட்டவணைகளை ஒரு வரிசையில் காட்ட

for i, (teacher, subjects) in enumerate(teachers_data.items()):
    with cols[i % 3]:
        df = pd.DataFrame(list(subjects.items()), columns=[teacher, "Periods"])
        # 'total' வரிசையைச் சேர்க்க
        total_row = pd.DataFrame({"Periods": [sum(subjects.values())]}, index=["Total"])
        df = pd.concat([pd.DataFrame(list(subjects.items()), columns=["Subject", "Periods"]), total_row.reset_index().rename(columns={"index": "Subject"})])
        
        st.write(f"**{teacher}**")
        st.table(df)

# 3. வகுப்புகளுக்கான சிறு அட்டவணைகள் (அதேபோல்)
st.divider()
st.subheader("வகுப்பு ஒதுக்கீடு")
class_data = {
    "11-A": {"TM-MR": 4, "Eng-MA": 4, "Phy-KV": 7, "Che-RV": 7, "Math-AL": 7, "CS-AB": 7, "GC-AS": 1, "MRL-TS": 1, "PET-CR": 2}
}

for cls, details in class_data.items():
    df_cls = pd.DataFrame(list(details.items()), columns=["Subject", "Periods"])
    st.write(f"**வகுப்பு: {cls}**")
    st.table(df_cls)
