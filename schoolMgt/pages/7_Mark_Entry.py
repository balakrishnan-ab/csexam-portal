import streamlit as st
from supabase import create_client

# --- Supabase இணைப்பு ---
def get_supabase_client():
    if "supabase_instance" not in st.session_state:
        st.session_state.supabase_instance = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
    return st.session_state.supabase_instance

supabase = get_supabase_client()

st.set_page_config(page_title="Mark Entry", layout="wide")
st.title("✍️ மதிப்பெண் பதிவேற்றம்")

# ⚡ தரவுகளைப் பெறுதல்
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

    parts = eval_type.split('+')
    max_t, max_p, max_i = int(parts[0]), (int(parts[1]) if len(parts) > 2 else 0), int(parts[-1])
    min_theory = 25 if max_t == 90 else 15

    # ⚡ 'on_change' மூலம் மதிப்பெண்களை உடனே பெட்டியில் ஏற்றும் முறை
    def update_all():
        for i in range(len(students)):
            if st.session_state.m_int: st.session_state[f"int_{i}"] = str(max_i)
            if max_p > 0 and st.session_state.get('m_prac'): st.session_state[f"p_{i}"] = str(max_p)

    st.subheader("⚙️ விரைவு உள்ளீடு")
    cf1, cf2 = st.columns(2)
    cf1.checkbox(f"அனைவருக்கும் முழு அகமதிப்பீடு ({max_i})", key="m_int", on_change=update_all)
    if max_p > 0:
        cf2.checkbox(f"அனைவருக்கும் முழு செய்முறை ({max_p})", key="m_prac", on_change=update_all)

    st.divider()
    
    # ⚡ தலைப்புகள் (நெருக்கமான விகிதம்)
    col_r = [1, 2.5, 0.5, 1, 1, 1, 1] if max_p > 0 else [1, 3, 0.5, 1.2, 0.1, 1.2, 1]
    h = st.columns(col_r)
    h[0].caption("எண்"); h[1].caption("பெயர்"); h[2].caption("Abs")
    h[3].caption(f"Theo({max_t})")
    if max_p > 0: h[4].caption(f"Prac({max_p})")
    h[5].caption(f"Int({max_i})")
    h[6].caption("Total")

    mark_list = []

    for idx, s in enumerate(students):
        # ⚡ text_input பயன்படுத்துவதால் எண்களை வேகமாக மாற்றலாம், பெட்டியும் சிறியதாக இருக்கும்
        t_str = st.session_state.get(f"t_{idx}", "0")
        p_str = st.session_state.get(f"p_{idx}", "0")
        i_str = st.session_state.get(f"int_{idx}", "0")
        
        # எண்களாக மாற்றுதல்
        t_v = int(t_str) if t_str.isdigit() else 0
        p_v = int(p_str) if p_str.isdigit() else 0
        i_v = int(i_str) if i_str.isdigit() else 0
        total = t_v + p_v + i_v
        
        is_fail = (t_v < min_theory) or (total < 35)
        name_style = "color:red; font-weight:bold;" if is_fail else "color:black;"

        r = st.columns(col_r)
        r[0].write(f"**{str(s['exam_no'])[-4:]}**") # கடைசி 4 எண்கள் மட்டும்
        r[1].markdown(f"<span style='font-size:13px; {name_style}'>{s['student_name']}</span>", unsafe_allow_html=True)
        is_abs = r[2].checkbox("", key=f"abs_{idx}", label_visibility="collapsed")

        if is_abs:
            t_v, p_v, i_v, total = 0, 0, 0, 0
            r[6].error("ABS")
        else:
            # ⚡ number_input-க்கு பதில் text_input (பெட்டி அளவு சிறியதாக இருக்கும்)
            t_v = r[3].text_input("", value=t_str, key=f"t_{idx}", label_visibility="collapsed")
            if max_p > 0:
                p_v = r[4].text_input("", value=p_str, key=f"p_{idx}", label_visibility="collapsed")
            i_v = r[5].text_input("", value=i_str, key=f"int_{idx}", label_visibility="collapsed")
            
            # மொத்த மதிப்பெண் வண்ணம்
            bg = "#ffcccc" if total < 35 else "#ccffcc"
            r[6].markdown(f"<div style='background-color:{bg}; text-align:center; border-radius:4px; line-height:2;'><b>{total}</b></div>", unsafe_allow_html=True)

        mark_list.append({
            "exam_id": exam_id, "emis_no": s['emis_no'], "subject_id": sub_code,
            "theory_mark": int(t_v) if str(t_v).isdigit() else 0,
            "practical_mark": int(p_v) if str(p_v).isdigit() else 0,
            "internal_mark": int(i_v) if str(i_v).isdigit() else 0,
            "total_mark": total, "is_absent": is_abs
        })

    st.divider()
    if st.button("🚀 மதிப்பெண்களைச் சேமி", use_container_width=True, type="primary"):
        supabase.table("marks").upsert(mark_list, on_conflict="exam_id, emis_no, subject_id").execute()
        st.success("வெற்றிகரமாகச் சேமிக்கப்பட்டது!")
