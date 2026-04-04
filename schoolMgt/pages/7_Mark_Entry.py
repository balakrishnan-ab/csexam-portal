import streamlit as st
import pandas as pd
from supabase import create_client, Client

# --- Supabase இணைப்பு ---
def get_supabase_client():
    if "supabase_instance" not in st.session_state:
        st.session_state.supabase_instance = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
    return st.session_state.supabase_instance

supabase = get_supabase_client()

st.set_page_config(page_title="Mark Entry", layout="wide")
st.title("✍️ பாடவாரியான மதிப்பெண் பதிவேற்றம்")

# தரவுகளைப் பெறுதல்
exams = supabase.table("exams").select("*").eq("exam_status", "Active").execute().data
subjects = supabase.table("subjects").select("*").execute().data
classes = supabase.table("classes").select("*").execute().data

# --- 1. தெரிவு செய்தல் ---
c1, c2, c3 = st.columns(3)
sel_exam_name = c1.selectbox("தேர்வு:", [e['exam_name'] for e in exams])
sel_sub_name = c2.selectbox("பாடம்:", [s['subject_name'] for s in subjects])
sel_class = c3.selectbox("வகுப்பு:", [c['class_name'] for c in classes])

if sel_exam_name and sel_sub_name and sel_class:
    # பாடத்தின் விவரம் மற்றும் eval_type-ஐப் பெறுதல்
    sub_info = next(s for s in subjects if s['subject_name'] == sel_sub_name)
    eval_type = sub_info.get('eval_type', '90+10') # Default 90+10
    
    exam_id = next(e['id'] for e in exams if e['exam_name'] == sel_exam_name)
    sub_id = sub_info['id']

    # மாணவர் பட்டியல் (Roll No படி)
    students = supabase.table("exam_mapping").select("*").eq("exam_id", exam_id).eq("class_name", sel_class).order("exam_no").execute().data

    st.info(f"📘 இந்த பாடத்தின் மதிப்பீடு முறை (eval_type): **{eval_type}**")
    
    # eval_type-ஐப் பிரித்தல் (எ.கா: 70+20+10)
    parts = eval_type.split('+')
    max_theory = int(parts[0])
    max_prac = int(parts[1]) if len(parts) > 2 else 0 # 70+20+10 எனில் 20 Practical
    max_int = int(parts[-1]) # கடைசி எண் எப்போதும் Internal (10)

    # Quick Fill (அனைவருக்கும் முழு மதிப்பெண்)
    col_f1, col_f2 = st.columns(2)
    fill_int = col_f1.checkbox(f"அனைவருக்கும் முழு அகமதிப்பீடு ({max_int}) வழங்குக")
    fill_prac = col_f2.checkbox(f"அனைவருக்கும் முழு செய்முறை மதிப்பெண் ({max_prac}) வழங்குக") if max_prac > 0 else False

    # --- 2. மதிப்பெண் உள்ளீடு அட்டவணை ---
    mark_list = []
    
    # தலைப்புகள் (eval_type-க்கு ஏற்ப காலம்களை உருவாக்குதல்)
    col_widths = [1, 2, 0.8, 1.2] # Roll, Name, Abs, Theory
    if max_prac > 0: col_widths.append(1.2) # Practical column
    col_widths.extend([1.2, 1]) # Internal, Total
    
    head = st.columns(col_widths)
    head[0].write("**எண்**")
    head[1].write("**பெயர்**")
    head[2].write("**Abs**")
    head[3].write(f"**Theo ({max_theory})**")
    
    curr_idx = 4
    if max_prac > 0:
        head[curr_idx].write(f"**Prac ({max_prac})**")
        curr_idx += 1
    
    head[curr_idx].write(f"**Int ({max_int})**")
    head[curr_idx+1].write("**Total**")

    st.divider()

    for i, s in enumerate(students):
        row = st.columns(col_widths)
        row[0].write(s['exam_no'])
        row[1].write(s['student_name'])
        
        is_abs = row[2].checkbox("", key=f"abs_{i}", label_visibility="collapsed")
        
        if is_abs:
            t, p, intn, tot = 0, 0, 0, 0
            row[-1].error("ABS")
        else:
            # Theory
            t = row[3].number_input("", 0, max_theory, key=f"t_{i}", label_visibility="collapsed")
            
            c_idx = 4
            # Practical (இருந்தால் மட்டும்)
            p = 0
            if max_prac > 0:
                p_val = max_prac if fill_prac else 0
                p = row[c_idx].number_input("", 0, max_prac, value=p_val, key=f"p_{i}", label_visibility="collapsed")
                c_idx += 1
            
            # Internal
            i_val = max_int if fill_int else 0
            intn = row[c_idx].number_input("", 0, max_int, value=i_val, key=f"int_{i}", label_visibility="collapsed")
            
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
            supabase.table("marks").upsert(mark_list, on_conflict="exam_id, emis_no, subject_id").execute()
            st.success("மதிப்பெண்கள் வெற்றிகரமாகச் சேமிக்கப்பட்டன!")
        except Exception as e:
            st.error(f"பிழை: {e}")
