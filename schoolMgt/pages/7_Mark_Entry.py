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
    max_i = int(parts[-1])

    # ⚡ 20, 10 தானாக விழ செக் பாக்ஸ்
    col_f1, col_f2 = st.columns(2)
    fill_i = col_f1.checkbox(f"அனைவருக்கும் முழு அகமதிப்பீடு ({max_i})", key="m_int")
    fill_p = False
    if max_p > 0:
        fill_p = col_f2.checkbox(f"அனைவருக்கும் முழு செய்முறை ({max_p})", key="m_prac")

    mark_list = []
    
    # அட்டவணை அமைப்பு
    cols_width = [0.8, 2, 0.6, 1.2]
    if max_p > 0: cols_width.append(1.2)
    cols_width.extend([1.2, 1])

    for idx, s in enumerate(students):
        row = st.columns(cols_width)
        row[0].write(s['exam_no'])
        row[1].write(s['student_name'])
        is_abs = row[2].checkbox("", key=f"abs_{idx}")

        if is_abs:
            t, p, i_v, tot = 0, 0, 0, 0
            row[-1].error("ABS")
        else:
            # ⚡ Theory - Enter அழுத்தினால் அடுத்த பெட்டிக்குச் செல்ல 'on_change' தேவையில்லை, 
            # ஆனால் Streamlit-ல் Tab பொத்தான் அழுத்தினால் தான் அடுத்த பெட்டிக்குச் செல்லும்.
            t = row[3].number_input("T", 0, max_t, key=f"t_{idx}", label_visibility="collapsed")
            
            p_idx = 4
            p = 0
            if max_p > 0:
                # ⚡ டிக் அடித்திருந்தால் max_p, இல்லையென்றால் பெட்டியில் உள்ள மதிப்பு
                p_val = max_p if fill_p else 0
                p = row[p_idx].number_input("P", 0, max_p, value=p_val, key=f"p_{idx}", label_visibility="collapsed")
                p_idx += 1
            
            # ⚡ டிக் அடித்திருந்தால் max_i, இல்லையென்றால் பெட்டியில் உள்ள மதிப்பு
            i_val = max_i if fill_i else 0
            intn = row[p_idx].number_input("I", 0, max_i, value=i_val, key=f"i_{idx}", label_visibility="collapsed")
            
            tot = t + p + intn
            row[-1].success(f"**{tot}**")

        mark_list.append({
            "exam_id": exam_id, "emis_no": s['emis_no'], "subject_id": sub_code,
            "theory_mark": t, "practical_mark": p, "internal_mark": intn, "total_mark": tot, "is_absent": is_abs
        })

    st.divider()
    if st.button("💾 மதிப்பெண்களைச் சேமி", use_container_width=True, type="primary"):
        supabase.table("marks").upsert(mark_list, on_conflict="exam_id, emis_no, subject_id").execute()
        st.success("வெற்றிகரமாகச் சேமிக்கப்பட்டது!")
