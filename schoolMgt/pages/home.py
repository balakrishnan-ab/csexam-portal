import streamlit as st

st.title("🏫 அரசு மேல்நிலைப் பள்ளி - தேவனங்குறிச்சி")
st.image("https://github.com/balakrishnan-ab/csexam-portal/edit/main/schoolMgt/school_building.jpg", caption="எங்கள் பள்ளி")

st.markdown("""
### பள்ளி பற்றிய விவரங்கள்:
* **தலைமையாசிரியர்:** [பெயர்]
* **சிறப்பம்சங்கள்:** மாணவர்களின் கல்வி மற்றும் விளையாட்டுத் திறன் மேம்பாடு.
* **நோக்கம்:** சிறந்த கல்வியை மாணவர்களுக்குக் கொண்டு சேர்ப்பது.
""")

# புகைப்படங்கள்
col1, col2 = st.columns(2)
with col1:
    st.image("https://github.com/balakrishnan-ab/csexam-portal/blob/main/schoolMgt/pages/photo1.jpg")
with col2:
    st.image("https://github.com/balakrishnan-ab/csexam-portal/blob/main/schoolMgt/pages/photo2.jpg")
