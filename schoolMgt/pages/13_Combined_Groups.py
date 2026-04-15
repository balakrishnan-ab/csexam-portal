import streamlit as st
from supabase import create_client, Client

# --- 1. SUPABASE CONNECTION ---
try:
    url: str = st.secrets["SUPABASE_URL"]
    key: str = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(url, key)
except Exception as e:
    st.error("Secrets விவரங்கள் சரியாக இல்லை!")
    st.stop()

st.set_page_config(page_title="Combined Groups", layout="wide")
st.title("🔗 கம்பைன் வகுப்புகள் உருவாக்கம் (Combined Groups)")

# --- ⚡ FETCH DATA ---
@st.cache_data(ttl=60)
def fetch_classes():
    res = supabase.table("classes").select("class_name").order("class_name").execute()
    return [c['class_name'] for c in res.data]

@st.cache_data(ttl=60)
def fetch_groups():
    res = supabase.table("combined_groups").select("*").execute()
    return res.data

available_classes = fetch_classes()

# --- 2. CREATE GROUP FORM ---
with st.form("group_form", clear_on_submit=True):
    st.subheader("🆕 புதிய இணைப்பை உருவாக்கு")
    g_name = st.text_input("இணைப்புக் குழுவின் பெயர்:", placeholder="எ.கா: 12-A & 12-B (PHY)")
    selected_classes = st.multiselect("இணைக்க வேண்டிய வகுப்புகளைத் தேர்வு செய்க:", available_classes)
    
    if st.form_submit_button("💾 குழுவை உருவாக்கு"):
        if g_name and len(selected_classes) > 1:
            try:
                supabase.table("combined_groups").insert({
                    "group_name": g_name,
                    "class_list": selected_classes
                }).execute()
                st.success(f"'{g_name}' குழு வெற்றிகரமாக உருவாக்கப்பட்டது!")
                st.cache_data.clear()
                st.rerun()
            except Exception as e:
                st.error(f"பிழை: {e}")
        else:
            st.warning("குறைந்தது இரண்டு வகுப்புகளைத் தேர்ந்தெடுக்கவும்.")

st.divider()

# --- 3. DISPLAY GROUPS ---
groups_data = fetch_groups()
if groups_data:
    st.subheader("📋 தற்போதைய இணைப்புக் குழுக்கள்")
    for g in groups_data:
        with st.expander(f"📌 {g['group_name']}"):
            st.write(f"உள்ளடங்கிய வகுப்புகள்: {', '.join(g['class_list'])}")
            if st.button(f"Delete {g['group_name']}", key=g['id']):
                supabase.table("combined_groups").delete().eq("id", g['id']).execute()
                st.cache_data.clear()
                st.rerun()
else:
    st.info("இன்னும் இணைப்புக் குழுக்கள் உருவாக்கப்படவில்லை.")
