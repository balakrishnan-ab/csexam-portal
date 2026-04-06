import streamlit as st

def add_school_header():
    # இங்கே உங்கள் பள்ளியின் பெயரை மாற்றிக்கொள்ளுங்கள்
    school_name = "அரசு மேல்நிலைப் பள்ளி,தேவனாங்குறிச்சி " 
    address = "திருச்செங்கோடு வட்டம், நாமக்கல் - 638209."
    
    st.markdown(f"""
        <div style="background-color:#1e3a8a; padding:20px; border-radius:10px; text-align:center; margin-bottom:20px;">
            <h1 style="color:white; margin:0; font-size:28px;">{school_name}</h1>
            <p style="color:#d1d5db; margin:5px 0 0 0; font-size:16px;">{address}</p>
        </div>
    """, unsafe_allow_html=True)
