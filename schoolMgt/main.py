import streamlit as st

# 🌍 மெயினில் மட்டும் ஒருமுறை அறிவிக்கிறோம்
if "BASE_URL" not in st.session_state:
    # இங்கேயே உங்கள் URL-ஐக் கொடுத்துவிடுங்கள்
    st.session_state["BASE_URL"] = "https://script.google.com/macros/s/AKfycbxcCywCOjo9On8r3xpfyswIzkeroo6PGApMyjEaChLfsVEMwHQNfyBEXs2sqrd51zEN5w/exec"


st.set_page_config(page_title="GHSS Portal", layout="wide")
st.title("🏫 GHSS - பள்ளி மேலாண்மை போர்ட்டல்")
st.write("இடதுபுறம் உள்ள மெனுவைப் பயன்படுத்தி நிர்வாக வேலைகளைத் தொடங்கவும்.")
