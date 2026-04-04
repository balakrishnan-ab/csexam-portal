import streamlit as st
from supabase import create_client

# --- Supabase இணைப்பு ---
def get_supabase_client():
    if "supabase_instance" not in st.session_state:
        st.session_state.supabase_instance = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
    return st.session_state.supabase_instance

supabase = get_supabase_client()

st.set_page_config(page_title="Mark Entry", layout="wide")
st.title("✍️ மதிப்பெண் பதிவேற்றம் (Final Fix)")

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

    # மதிப்பீடு பிரித்தல் (எ.கா: 70+20+10)
    parts = eval_type.split('+')
    max_t, max_p, max_i = int(parts[0]), (int(parts[1]) if len(parts) > 2 else 0), int(parts[-1])

    # ⚡ 20, 10 தானாக விழும் "மேஜிக்" பட்டன்கள்
    st.subheader("⚙️ விரைவு உள்ளீடு")
    col_f1, col_f2 = st.columns(2)
    
    # இதோ அந்த ரகசியம்: 'on_change' பயன்படுத்தினால் மட்டுமே திரையில் மதிப்புகள் உடனே மாறும்
    def update_all():
        for i in range(len(students)):
            if st.session_state.m_int: st.session_state[f"int_{i}"] = max_i
            else: st.session_state[f"int_{i}"] = 0
            
            if max_p > 0:
                if st.session_state.m_prac: st.session_state[f"p_{i}"] = max_p
                else: st.session_state[f"p_{i}"] = 0

    fill_i = col_f1.checkbox(f"அனைவருக்கும் முழு அகமதிப்பீடு ({max_i})", key="m_int", on_change=update_all)
    fill_p = col_f2.checkbox(f"அனைவருக்கும் முழு செய்முறை ({max_p})", key="m_prac", on_change=update_all) if max_p > 0 else False

    # --- 2. அட்டவணை ---
    mark_list = []
    st.divider()
    
    for idx, s in enumerate(students):
        r = st.columns([1, 2, 0.6, 1.2, 1.2, 1.2, 1])
        r[0].write(s['exam_no'])
        r[1].write(s['student_name'])
        is_abs = r[2].checkbox("", key=f"abs_{idx}")

        if is_abs:
            t, p, i_v, tot = 0, 0, 0, 0
            r[-1].error("ABS")
        else:
            # ⚡ Theory
            t = r[3].number_input("T", 0, max_t, key=f"t_{idx}", label_visibility="collapsed")
            
            # ⚡ Practical
            p = 0
            if max_p > 0:
                p = r[4].number_input("P", 0, max_p, key=f"p_{idx}", label_visibility="collapsed")
            
            # ⚡ Internal
            i_v = r[5].number_input("I", 0, max_i, key=f"int_{idx}", label_visibility="collapsed")
            
            tot = t + p + i_v
            r[-1].success(f"**{tot}**")

        mark_list.append({
            "exam_id": exam_id, "emis_no": s['emis_no'], "subject_id": sub_code,
            "theory_mark": t, "practical_mark": p, "internal_mark": i_v, "total_mark": tot, "is_absent": is_abs
        })

    # 💾 சேமித்தல்
    if st.button("🚀 மதிப்பெண்களை உறுதி செய்து சேமி", use_container_width=True, type="primary"):
        supabase.table("marks").upsert(mark_list, on_conflict="exam_id, emis_no, subject_id").execute()
        st.success("வெற்றிகரமாகச் சேமிக்கப்பட்டது!")
        st.balloons()
