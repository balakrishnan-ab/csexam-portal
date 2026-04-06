import streamlit as st

def add_school_header():
    school_name = "அரசு மேல்நிலைப் பள்ளி, தேவனாங்குறிச்சி" 
    address = "திருச்செங்கோடு வட்டம், நாமக்கல் - 638209."
    
    st.markdown(f"""
        <style>
        .school-header-container {{
            background-color: #1e3a8a; 
            padding: clamp(15px, 4vw, 30px); /* பேடிங் சற்று அதிகரிப்பு */
            border-radius: 12px; 
            text-align: center; 
            margin-bottom: 25px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1); /* லேசான நிழல் - அழகுக்காக */
        }}
        .school-title {{
            color: white !important; 
            margin: 0; 
            /* குறைந்தபட்சம் 22px, திரையின் அகலத்தில் 5%, அதிகபட்சம் 40px */
            font-size: clamp(22px, 5vw, 40px) !important; 
            font-weight: 800;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3); /* எழுத்துக்கள் பளிச்சென்று தெரிய */
        }}
        .school-address {{
            color: #d1d5db !important; 
            margin: 8px 0 0 0; 
            font-size: clamp(14px, 2.5vw, 20px) !important;
            letter-spacing: 0.5px;
        }}
        </style>
        
        <div class="school-header-container">
            <h1 class="school-title">{school_name}</h1>
            <p class="school-address">{address}</p>
        </div>
    """, unsafe_allow_html=True)
        
        <div class="school-header-container">
            <h1 class="school-title">{school_name}</h1>
            <p class="school-address">{address}</p>
        </div>
    """, unsafe_allow_html=True)
