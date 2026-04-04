import streamlit as st
from supabase import create_client

# --- Supabase இணைப்பு ---
def get_supabase_client():
    if "supabase_instance" not in st.session_state:
        st.session_state.supabase_instance = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
    return st.session_state.supabase_instance

supabase = get_supabase_client()

st.set_page_config(page_title="Mark Entry", layout="wide")
st.title("✍️ மதிப்பெண் பதிவேற்றம் & கண்காணிப்பு")

# தரவுகளைப் பெறுதல்
exams = supabase.table("exams").select("*").eq("exam_status", "Active").execute().data
subjects = supabase.table("subjects").select("*").execute().data
classes = supabase.table("classes").select("*").execute().data

# --- 1. தெரிவு செய்தல் ---
c1, c2, c3 = st.columns(3)
sel_exam = c1.selectbox("தேர்வு:", [e['exam_name'] for e in exams]) if exams else None
sel_sub = c2.selectbox("பாடம்:", [s['subject_name'] for s in subjects]) if subjects else None
sel_cls = c3.selectbox("வகுப்பு:", [c['class_name'] for c in classes]) if classes else None

if sel_exam and sel_sub and sel_cls:
    sub_info = next(s for s in subjects if s['subject_name'] == sel_sub)
    eval_type = sub_info.get('eval_type', '90+10')
    sub_code = sub_info.get('subject_code')
    exam_id = next(e['id'] for e in exams if e['exam_name'] == sel_exam)

    students = supabase.table("exam_mapping").select("*").eq("exam_id", exam_id).eq("class_name", sel_cls).order("exam_no").execute().data

    # மதிப்பீடு பிரித்தல்
    parts = eval_type.split('+')
    max_t = int(parts[0])
    max_p = int(parts[1]) if len(parts) > 2 else 0
    max_i = int(parts[-1]) # இங்கே 'max_i' எனப் பெயர் வைத்துள்ளோம்

    # ⚡ தேர்ச்சி மதிப்பெண் நிபந்தனை
    min_theory = 25 if max_t == 90 else 15
    min_total = 35

    # விரைவு உள்ளீடு தர்க்கம்
    def update_all():
        for i in range(len(students)):
            # அகமதிப்பீடு அப்டேட்
            if st.session_state.m_int:
                st.session_state[f"int_{i}"] = max_i
            else:
                st.session_state[f"int_{i}"] = 0
            
            # செய்முறை அப்டேட் (இருந்தால் மட்டும்)
            if max_p > 0:
                if st.session_state.get('m_prac'):
                    st.session_state[f"p_{i}"] = max_p
                else:
                    st.session_state[f"p_{i}"] = 0

    st.subheader("⚙️ விரைவு உள்ளீடு")
    cf1, cf2 = st.columns(2)
    
    # ⚡ திருத்தம்: max_int என்பதற்கு பதில் max_i என மாற்றப்பட்டுள்ளது
    fill_i = cf1.checkbox(f"அனைவருக்கும் முழு அகமதிப்பீடு ({max_i})", key="m_int", on_change=update_all)
    
    fill_p = False
    if max_p > 0:
        fill_p = cf2.checkbox(f"அனைவருக்கும் முழு செய்முறை ({max_p})", key="m_prac", on_change=update_all)

    mark_list = []
    st.divider()
    
    # தலைப்புகள்
    cols_h = st.columns([1, 2.5, 0.6, 1.2, 1.2, 1.2, 1])
    cols_h[0].write("**எண்**"); cols_h[1].write("**பெயர்**"); cols_h[2].write("**Abs**")
    cols_h[3].write(f"**Theo({max_t})**"); cols_h[4].write(f"**Prac({max_p})**"); cols_h[5].write(f"**Int({max_i})**"); cols_h[6].write("**Total**")

    for idx, s in enumerate(students):
        # தற்போதைய மதிப்புகளை எடுத்தல்
        t_val = st.session_state.get(f"t_{idx}", 0)
        p_val = st.session_state.get(f"p_{idx}", 0)
        i_val = st.session_state.get(f"int_{idx}", 0)
        total = t_val + p_val + i_val
        
        # ⚡ தோல்வி நிபந்தனை: பெயர் சிவப்பாக மாறும்
        is_fail = (t_val < min_theory) or (total < min_total)
        display_name = s['student_name']
        if is_fail:
            display_name = f":red[**{s['student_name']} (Fail)**]"

        r = st.columns([1, 2.5, 0.6, 1.2, 1.2, 1.2, 1])
        r[0].write(s['exam_no'])
        r[1].markdown(display_name)
        is_abs = r[2].checkbox("", key=f"abs_{idx}")

        if is_abs:
            t, p, intn, tot = 0, 0, 0, 0
            r[-1].error("ABS")
        else:
            t = r[3].number_input("T", 0, max_t, key=f"t_{idx}", label_visibility="collapsed")
            
            p = 0
            if max_p > 0:
                p = r[4].number_input("P", 0, max_p, key=f"p_{idx}", label_visibility="collapsed")
            
            intn = r[5].number_input("I", 0, max_i, key=f"int_{idx}", label_visibility="collapsed")
            
            tot = t + p + intn
            if tot < 35: r[-1].error(f"**{tot}**")
            else: r[-1].success(f"**{tot}**")

        mark_list.append({
            "exam_id": exam_id, "emis_no": s['emis_no'], "subject_id": sub_code,
            "theory_mark": t, "practical_mark": p, "internal_mark": intn, "total_mark": tot, "is_absent": is_abs
        })

    if st.button("🚀 மதிப்பெண்களைச் சேமி", use_container_width=True, type="primary"):
        try:
            supabase.table("marks").upsert(mark_list, on_conflict="exam_id, emis_no, subject_id").execute()
            st.success("வெற்றிகரமாகச் சேமிக்கப்பட்டது!")
            st.balloons()
        except Exception as e:
            st.error(f"பிழை: {e}")
