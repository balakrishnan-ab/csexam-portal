import streamlit as st
import pandas as pd
from supabase import create_client, Client

# --- Supabase இணைப்பு ---
def get_supabase_client():
    if "supabase_instance" not in st.session_state:
        try:
            st.session_state.supabase_instance = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
        except: return None
    return st.session_state.supabase_instance

supabase = get_supabase_client()

st.set_page_config(page_title="Mark Entry", layout="wide")
st.title("✍️ பாடவாரியான மதிப்பெண் பதிவேற்றம்")

if not supabase:
    st.error("Supabase இணைப்பு தோல்வி!")
    st.stop()

# ⚡ தரவுகளைப் பெறுதல்
exams = supabase.table("exams").select("*").eq("exam_status", "Active").execute().data
subjects = supabase.table("subjects").select("*").execute().data
classes = supabase.table("classes").select("*").execute().data

# --- 1. தெரிவு செய்தல் ---
c1, c2, c3 = st.columns(3)
sel_exam_name = c1.selectbox("தேர்வு:", [e['exam_name'] for e in exams]) if exams else None
sel_sub_name = c2.selectbox("பாடம்:", [s['subject_name'] for s in subjects]) if subjects else None
sel_class = c3.selectbox("வகுப்பு:", [c['class_name'] for c in classes]) if classes else None

if sel_exam_name and sel_sub_name and sel_class:
    # 🔍 திருத்தப்பட்ட பகுதி: 'id'-க்கு பதில் 'subject_code'-ஐப் பயன்படுத்துகிறோம்
    sub_info = next(s for s in subjects if s['subject_name'] == sel_sub_name)
    eval_type = sub_info.get('eval_type', '90+10')
    
    # இங்குதான் பிழை வந்தது, அதை இப்போது 'subject_code' என மாற்றியுள்ளோம்
    sub_id = sub_info.get('subject_code') 
    
    exam_id = next(e['id'] for e in exams if e['exam_name'] == sel_exam_name)

    # அந்தத் தேர்விற்கான மாணவர் பட்டியல் (தேர்வு எண் வரிசையில்)
    students = supabase.table("exam_mapping").select("*").eq("exam_id", exam_id).eq("class_name", sel_class).order("exam_no").execute().data

    if not students:
        st.warning(f"⚠️ {sel_class} வகுப்பிற்குத் தேர்வு எண்கள் இன்னும் உருவாக்கப்படவில்லை.")
        st.stop()

    # eval_type-ஐப் பிரித்தல்
    parts = eval_type.split('+')
    max_theory = int(parts[0])
    max_prac = int(parts[1]) if len(parts) > 2 else 0
    max_int = int(parts[-1])

    st.info(f"📘 மதிப்பீடு முறை: **{eval_type}** | பாடம் குறியீடு: **{sub_id}**")
    
    cf1, cf2 = st.columns(2)
    fill_int = cf1.checkbox(f"அனைவருக்கும் முழு அகமதிப்பீடு ({max_int})")
    fill_prac = cf2.checkbox(f"அனைவருக்கும் முழு செய்முறை ({max_prac})") if max_prac > 0 else False

    # --- 2. மதிப்பெண் உள்ளீடு ---
    mark_list = []
    col_w = [0.8, 2, 0.7, 1.2]
    if max_prac > 0: col_w.append(1.2)
    col_w.extend([1.2, 1])

    head = st.columns(col_w)
    head[0].write("**எண்**"); head[1].write("**பெயர்**"); head[2].write("**Abs**")
    head[3].write("**Theory**")
    cp = 4
    if max_prac > 0: head[cp].write("**Prac**"); cp += 1
    head[cp].write("**Int**"); head[cp+1].write("**Total**")

    for i, s in enumerate(students):
        row = st.columns(col_w)
        row[0].write(s['exam_no'])
        row[1].write(s['student_name'])
        is_abs = row[2].checkbox("", key=f"abs_{i}")
        
        if is_abs:
            t, p, intn, tot = 0, 0, 0, 0
            row[-1].error("ABS")
        else:
            t = row[3].number_input("", 0, max_theory, key=f"t_{i}", label_visibility="collapsed")
            curr = 4
            p = 0
            if max_prac > 0:
                p = row[curr].number_input("", 0, max_prac, value=(max_prac if fill_prac else 0), key=f"p_{i}", label_visibility="collapsed")
                curr += 1
            intn = row[curr].number_input("", 0, max_int, value=(max_int if fill_int else 0), key=f"int_{i}", label_visibility="collapsed")
            tot = t + p + intn
            row[-1].success(f"**{tot}**")

        mark_list.append({
            "exam_id": exam_id, 
            "emis_no": s['emis_no'], 
            "subject_id": sub_id, # 'id'-க்கு பதிலாக subject_code சேமிக்கப்படும்
            "theory_mark": t, 
            "practical_mark": p, 
            "internal_mark": intn, 
            "total_mark": tot, 
            "is_absent": is_abs
        })

    if st.button("💾 மதிப்பெண்களைச் சேமி", use_container_width=True, type="primary"):
        # subject_id என்ற Column-ஐ அடிப்படையாகக் கொண்டு மதிப்பெண்கள் புதுப்பிக்கப்படும்
        supabase.table("marks").upsert(mark_list, on_conflict="exam_id, emis_no, subject_id").execute()
        st.success("வெற்றிகரமாகச் சேமிக்கப்பட்டது!")
