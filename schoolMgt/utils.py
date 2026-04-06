import streamlit as st

def add_school_header():
    # உங்கள் பள்ளியின் விவரங்கள்
    school_name = "அரசு மேல்நிலைப் பள்ளி, தேவனாங்குறிச்சி" 
    address = "திருச்செங்கோடு வட்டம், நாமக்கல் - 638209."
    
    st.markdown(f"""
        <style>
        .school-header-container {{
            background-color: #1e3a8a; 
            padding: clamp(10px, 3vw, 20px); 
            border-radius: 10px; 
            text-align: center; 
            margin-bottom: 20px;
            width: 100%;
        }}
        .school-title {{
            color: white; 
            margin: 0; 
            font-size: clamp(18px, 4.5vw, 32px); /* மொபைலில் 18px, பெரிய திரையில் 32px வரை */
            line-height: 1.2;
            font-weight: bold;
        }}
        .school-address {{
            color: #d1d5db; 
            margin: 5px 0 0 0; 
            font-size: clamp(12px, 2.5vw, 18px); /* முகவரி மொபைலில் 12px, கணினியில் 18px வரை */
        }}
        </style>
        
        <div class="school-header-container">
            <h1 class="school-title">{school_name}</h1>
            <p class="school-address">{address}</p>
        </div>
    """, unsafe_allow_html=True)
