import streamlit as st

def add_school_header():
    school_name = "அரசு மேல்நிலைப் பள்ளி, தேவனாங்குறிச்சி" 
    address = "திருச்செங்கோடு வட்டம், நாமக்கல் - 638209."
    
    st.markdown(f"""
        <style>
        .school-header-container {{
            background-color: #1e3a8a; 
            padding: clamp(15px, 4vw, 30px); 
            border-radius: 12px; 
            text-align: center; 
            margin-bottom: 25px;
            box-shadow: 0 6px 15px rgba(0,0,0,0.2);
            width: 100%;
        }}
        .school-title {{
            color: #FFFFFF !important; 
            margin: 0; 
            font-size: clamp(20px, 5.5vw, 38px) !important; 
            font-weight: 800 !important;
            line-height: 1.3;
            text-shadow: 2px 2px 8px rgba(0,0,0,0.5) !important;
            display: block;
        }}
        .school-address {{
            color: #E2E8F0 !important; 
            margin: 10px 0 0 0; 
            font-size: clamp(13px, 2.5vw, 18px) !important;
            font-weight: 500;
            letter-spacing: 0.5px;
            text-shadow: 1px 1px 3px rgba(0,0,0,0.4) !important;
        }}
        </style>
        
        <div class="school-header-container">
            <span class="school-title">{school_name}</span>
            <span class="school-address">{address}</span>
        </div>
    """, unsafe_allow_html=True)

def apply_global_styles():
    st.markdown("""
        <style>
        /* எழுத்துக்களைத் தெளிவாக்க */
        * {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif !important;
            font-size: 16px !important;
        }
        /* மெனு மற்றும் உரைகளை அடர் நிறமாக்க */
        .stMarkdown, .stText, p, label, div {
            color: #333333 !important;
        }
        /* எண்களைப் பெரிதாக்க (metric values) */
        .stMetricValue {
            font-size: 24px !important;
            font-weight: 800 !important;
        }
        /* பட்டன்களின் எழுத்து அளவு */
        button {
            font-size: 16px !important;
        }
        </style>
    """, unsafe_allow_html=True)
