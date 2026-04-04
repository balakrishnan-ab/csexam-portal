import streamlit as st
import pandas as pd
from supabase import create_client

# --- Supabase இணைப்பு ---
def get_supabase_client():
    if "supabase_instance" not in st.session_state:
        st.session_state.supabase_instance = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
    return st.session_state.supabase_instance

supabase = get_supabase_client()

st.set_page_config(page_title="Mark Entry", layout="wide")
st.title("📊 மதிப்பெண் பதிவேற்றம் (Freeze Panes)")

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

    # மாணவர் பட்டியல்
    students = supabase.table("exam_mapping").select("exam_no, student_name, emis_no").eq("exam_id", exam_id).eq("class_name", sel_cls).order("exam_no").execute().data

    parts = eval_type.split('+')
    max_t, max_p, max_i = int(parts[0]), (int(parts[1]) if len(parts) > 2 else 0), int(parts[-1])

    # ⚡ 2. எக்செல் போன்ற அட்டவணை உருவாக்கம்
    df = pd.DataFrame(students)
    df['Abs'] = False
    df['Theory'] = 0
    if max_p > 0: df['Practical'] = 0
    df['Internal'] = 0
    df['Total'] = 0

    st.subheader("📝 மதிப்பெண் உள்ளீடு")
    
    # ⚡ 3. எக்செல் எடிட்டர் (Data Editor)
    # இதில் 'pin' வசதி தானாகவே இருக்கும் அல்லது column_config மூலம் கட்டுப்படுத்தலாம்
    edited_df = st.data_editor(
        df,
        column_config={
            "exam_no": st.column_config.TextColumn("தேர்வு எண்", disabled=True, pinned=True, width="small"),
            "student_name": st.column_config.TextColumn("மாணவர் பெயர்", disabled=True, pinned=True, width="medium"),
            "emis_no": None, # EMIS எண்ணை மறைக்க
            "Abs": st.column_config.CheckboxColumn("Abs", default=False),
            "Theory": st.column_config.NumberColumn(f"Theo({max_t})", min_value=0, max_value=max_t),
            "Practical": st.column_config.NumberColumn(f"Prac({max_p})", min_value=0, max_value=max_p) if max_p > 0 else None,
            "Internal": st.column_config.NumberColumn(f"Int({max_i})", min_value=0, max_value=max_i),
            "Total": st.column_config.NumberColumn("மொத்தம்", disabled=True),
        },
        hide_index=True,
        use_container_width=True,
    )

    # ⚡ 4. கணக்கீடு
    edited_df['Total'] = edited_df['Theory'] + edited_df.get('Practical', 0) + edited_df['Internal']
    edited_df.loc[edited_df['Abs'] == True, ['Theory', 'Practical', 'Internal', 'Total']] = 0

    # ⚡ 5. சேமித்தல்
    if st.button("🚀 தரவுகளைச் சேமி", use_container_width=True, type="primary"):
        mark_list = []
        for _, row in edited_df.iterrows():
            mark_list.append({
                "exam_id": exam_id,
                "emis_no": row['emis_no'],
                "subject_id": sub_code,
                "theory_mark": int(row['Theory']),
                "practical_mark": int(row.get('Practical', 0)),
                "internal_mark": int(row['Internal']),
                "total_mark": int(row['Total']),
                "is_absent": bool(row['Abs'])
            })
        
        try:
            supabase.table("marks").upsert(mark_list, on_conflict="exam_id, emis_no, subject_id").execute()
            st.success("வெற்றிகரமாகச் சேமிக்கப்பட்டது!")
            st.balloons()
        except Exception as e:
            st.error(f"பிழை: {e}")
