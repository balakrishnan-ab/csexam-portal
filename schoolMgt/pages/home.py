import streamlit as st

st.title("🏫 அரசு மேல்நிலைப் பள்ளி - தேவனங்குறிச்சி")
st.image("https://github.com/balakrishnan-ab/csexam-portal/edit/main/schoolMgt/school_building.jpg", caption="எங்கள் பள்ளி")

st.markdown("""
### பள்ளி பற்றிய விவரங்கள்:
* **தலைமையாசிரியர்:** [பெயர்]
* **சிறப்பம்சங்கள்:** மாணவர்களின் கல்வி மற்றும் விளையாட்டுத் திறன் மேம்பாடு.
* **நோக்கம்:** சிறந்த கல்வியை மாணவர்களுக்குக் கொண்டு சேர்ப்பது.
* **பாடபிரிவுகள்:** 
1. 502 - இயற்பியல்,வேதியில்,கனினி அறிவியல், கணிதம். ( தமிழ்/ஆங்கிலம்)
2. 503 - இயற்பியல்,வேதியில்,உயிரியல் அறிவியல், கணிதம். ( தமிழ்/ஆங்கிலம்)
3. 702 - பொருளியல், வணிகவியல், கணக்குப்பதிவியல்,கனினி பயன்பாட்டுகள் ( தமிழ்)
4. 703 - வரலாறு, வணிகவியல், கணக்குப்பதிவியல்,கனினி பயன்பாட்டுகள் (தமிழ்)
""")

# புகைப்படங்கள்
col1, col2 = st.columns(2)
with col1:
    st.image("https://github.com/balakrishnan-ab/csexam-portal/blob/main/schoolMgt/pages/photo1.jpg")
with col2:
    st.image("https://github.com/balakrishnan-ab/csexam-portal/blob/main/schoolMgt/pages/photo2.jpg")
