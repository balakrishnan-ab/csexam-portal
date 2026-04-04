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
    # பாட விவரம் மற்றும் மதிப்பீடு முறை (eval_type)
    sub_info = next(s for s in subjects if s['subject_name'] == sel_sub_name)
    eval_type = sub_info.get('eval_type', '90+10')
    sub_id = sub_info.get('subject_code') # உங்கள் டேபிளில் உள்ளபடி
    exam_id = next(e['id'] for e in exams if e['exam_name'] == sel_exam_name)

    # மாணவர் பட்டியல் (தேர்வு எண் வரிசையில்)
    students = supabase.table("exam_mapping").select("*").eq("exam_id", exam_id).eq("class_name", sel_class).order("exam_no").execute().data

    if not students:
        st.warning(f"⚠️ {sel_class} வகுப்பிற்குத் தேர்வு எண்கள் இன்னும் உருவாக்கப்படவில்லை.")
        st.stop()

    # eval_type-ஐப் பிரித்தல் (எ.கா: 70+20+10)
    parts = eval_type.split('+')
    max_theory = int(parts[0])
    max_prac = int(parts[1]) if len(parts) > 2 else 0
    max_int = int(parts[-1])

    st.info(f"📘 மதிப்பீடு முறை: **{eval_type}** | பாடம் குறியீடு: **{sub_id}**")
    
    # ⚡ விரைவு உள்ளீடு (டிக் பாக்ஸ் வசதி)
    cf1, cf2 = st.columns(2)
    fill_int = cf1.checkbox(f"அனைவருக்கும் முழு அகமதிப்பீடு ({max_int}) வழங்குக", key="chk_int")
    fill_prac = False
    if max_prac > 0:
        fill_prac = cf2.checkbox(f"அனைவருக்கும் முழு செய்முறை ({max_prac}) வழங்குக", key="chk_prac")

    # --- 2. மதிப்பெண் அட்டவணை ---
    mark_list = []
    
    # நெடுவரிசை அகலங்கள்
    col_w = [0.8, 2, 0.6, 1.2]
    if max_prac > 0: col_w.append(1.2)
    col_w.extend([1.2, 1])

    head = st.columns(col_w)
    head[0].write("**எண்**"); head[1].write("**பெயர்**"); head[2].write("**Abs**")
    head[3].write(f"**Theo({max_theory})**")
    
    curr_h = 4
    if max_prac > 0: 
        head[curr_h].write(f"**Prac({max_prac})**")
        curr_h += 1
    head[curr_h].write(f"**Int({max_int})**")
    head[curr_h+1].write("**Total**")

    st.divider()

    for i, s in enumerate(students):
        row = st.columns(col_w)
        row[0].write(s['exam_no'])
        row[1].write(s['student_name'])
        
        is_abs = row[2].checkbox("", key=f"abs_{i}")
        
        if is_abs:
            t, p, intn, tot = 0, 0, 0, 0
            row[-1].error("ABS")
        else:
            # 1. Theory
            t = row[3].number_input("", 0, max_theory, key=f"t_{i}", label_visibility="collapsed")
            
            curr_r = 4
            p = 0
            # 2. Practical (டிக் வசதியுடன்)
            if max_prac > 0:
                p_val = max_prac if fill_prac else 0
                p = row[curr_r].number_input("", 0, max_prac, value=p_val, key=f"p_{i}", label_visibility="collapsed")
                curr_r += 1
            
            # 3. Internal (டிக் வசதியுடன்)
            i_val = max_int if fill_int else 0
            intn = row[curr_r].number_input("", 0, max_int, value=i_val, key=f"int_{i}", label_visibility="collapsed")
            
            # 4. Total calculation
            tot = t + p + intn
            row[-1].success(f"**{tot}**")

        mark_list.append({
            "exam_id": exam_id, 
            "emis_no": s['emis_no'], 
            "subject_id": sub_id,
            "theory_mark": t, 
            "practical_mark": p, 
            "internal_mark": intn, 
            "total_mark": tot, 
            "is_absent": is_abs
        })

    st.divider()
    
    # --- 3. சேமித்தல் ---
    if st.button("💾 மதிப்பெண்களைச் சேமி", use_container_width=True, type="primary"):
        try:
            with st.spinner("சேமிக்கப்படுகிறது..."):
                supabase.table("marks").upsert(mark_list, on_conflict="exam_id, emis_no, subject_id").execute()
                st.success("வெற்றிகரமாகச் சேமிக்கப்பட்டது!")
                st.balloons()
        except Exception as e:
            st.error(f"பிழை: {e}")
