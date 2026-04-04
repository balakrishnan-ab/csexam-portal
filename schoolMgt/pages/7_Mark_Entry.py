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

# ⚡ CSS - எழுத்துக்களைப் பெரிதாக்க
st.markdown("<style>.stDataFrame { font-size: 19px !important; font-weight: bold !important; }</style>", unsafe_allow_html=True)

st.title("📊 மதிப்பெண் பதிவேற்றம் & திருத்தம்")

# --- 1. தரவுகள் ---
exams = supabase.table("exams").select("*").eq("exam_status", "Active").execute().data
all_classes = supabase.table("classes").select("*").execute().data
all_groups = supabase.table("groups").select("*").execute().data
all_subjects = supabase.table("subjects").select("*").execute().data

# --- 2. தேர்வுப் பெட்டிகள் ---
c1, c2, c3 = st.columns(3)
sel_exam_name = c1.selectbox("1. தேர்வு:", ["-- தேர்வு செய்க --"] + [e['exam_name'] for e in exams])

if sel_exam_name != "-- தேர்வு செய்க --":
    exam_id = next(e['id'] for e in exams if e['exam_name'] == sel_exam_name)
    class_names = [c.get('class_n') or c.get('class_name') for c in all_classes if (c.get('class_n') or c.get('class_name'))]
    sel_class = c2.selectbox("2. வகுப்பு:", ["-- தேர்வு செய்க --"] + sorted(class_names))

    if sel_class != "-- தேர்வு செய்க --":
        class_info = next((c for c in all_classes if (c.get('class_n') == sel_class or c.get('class_name') == sel_class)), None)
        subject_options = {} 
        if class_info:
            group_info = next((g for g in all_groups if g['group_name'] == class_info.get('group_name')), None)
            if group_info and group_info.get('subjects'):
                group_subs = [s.strip() for s in group_info['subjects'].split(',')]
                for sub_name in group_subs:
                    match = next((s for s in all_subjects if s['subject_name'] == sub_name), None)
                    if match:
                        display_name = f"{sub_name} ({match['subject_code']})"
                        subject_options[display_name] = match
        
        sel_display_name = c3.selectbox("3. பாடம்:", ["-- தேர்வு செய்க --"] + list(subject_options.keys()))

        if sel_display_name != "-- தேர்வு செய்க --":
            sub_info = subject_options[sel_display_name]
            sub_code = sub_info['subject_code']
            eval_type = sub_info.get('eval_type', '90+10')
            parts = eval_type.split('+')
            max_t, max_p, max_i = int(parts[0]), (int(parts[1]) if len(parts) > 2 else 0), int(parts[-1])

            # ⚡ 3. Session State - தரவுகள் அழியாமல் இருக்க
            state_key = f"df_{exam_id}_{sel_class}_{sub_code}"
            if state_key not in st.session_state:
                students = supabase.table("exam_mapping").select("exam_no, student_name, emis_no").eq("exam_id", exam_id).eq("class_name", sel_class).order("exam_no").execute().data
                existing_marks = supabase.table("marks").select("*").eq("exam_id", exam_id).eq("subject_id", sub_code).execute().data
                marks_dict = {m['emis_no']: m for m in existing_marks}
                
                rows = []
                for s in students:
                    m = marks_dict.get(s['emis_no'], {})
                    rows.append({
                        "Exam No": s['exam_no'], "Student Name": s['student_name'], "EMIS": s['emis_no'],
                        "Abs": m.get('is_absent', False), "Theory": m.get('theory_mark', 0),
                        "Internal": m.get('internal_mark', 0), 
                        "Practical": m.get('practical_mark', 0) if max_p > 0 else 0, "Total": m.get('total_mark', 0)
                    })
                st.session_state[state_key] = pd.DataFrame(rows)

            # ⚡ 4. எக்செல் எடிட்டர் (Form-க்குள் இருப்பதால் தட்டச்சு செய்யும்போது தடங்கல் இருக்காது)
            with st.form("mark_entry_form"):
                st.subheader(f"📝 {sel_class} - {sel_display_name}")
                df = st.session_state[state_key]
                
                # காண்பிக்கப்பட வேண்டிய வரிசை
                cols = ["Exam No", "Student Name", "Abs", "Theory"]
                if max_p > 0: cols.append("Practical")
                cols.extend(["Internal", "Total"])

                edited_df = st.data_editor(
                    df[cols],
                    column_config={
                        "Exam No": st.column_config.TextColumn("தேர்வு எண்", disabled=True, pinned=True),
                        "Student Name": st.column_config.TextColumn("பெயர்", disabled=True, pinned=True),
                        "Theory": st.column_config.NumberColumn(f"Theo({max_t})"),
                        "Practical": st.column_config.NumberColumn(f"Prac({max_p})") if max_p > 0 else None,
                        "Internal": st.column_config.NumberColumn(f"Int({max_i})"),
                        "Total": st.column_config.NumberColumn("மொத்தம்", disabled=True),
                    },
                    hide_index=True, use_container_width=True, key="my_editor"
                )

                submit = st.form_submit_button("🚀 சரிபார்த்துச் சேமி", use_container_width=True)

                if submit:
                    # ⚡ பிழையில்லாமல் மொத்தம் கணக்கிடுதல்
                    t_marks = pd.to_numeric(edited_df['Theory'], errors='coerce').fillna(0)
                    i_marks = pd.to_numeric(edited_df['Internal'], errors='coerce').fillna(0)
                    
                    # Practical இருந்தால் மட்டும் கணக்கில் கொள்ளவும்
                    if "Practical" in edited_df.columns:
                        p_marks = pd.to_numeric(edited_df['Practical'], errors='coerce').fillna(0)
                    else:
                        p_marks = 0
                    
                    edited_df['Total'] = t_marks + i_marks + p_marks
                    # Abs டிக் செய்திருந்தால் மொத்தம் 0
                    edited_df.loc[edited_df['Abs'] == True, ['Theory', 'Practical', 'Internal', 'Total']] = 0

                    # டேட்டாபேஸில் சேமித்தல்
                    final_list = []
                    for idx, r in edited_df.iterrows():
                        final_list.append({
                            "exam_id": exam_id, "emis_no": df.iloc[idx]['EMIS'], "subject_id": sub_code,
                            "theory_mark": int(r['Theory']), 
                            "practical_mark": int(r.get('Practical', 0)) if max_p > 0 else 0,
                            "internal_mark": int(r['Internal']), "total_mark": int(r['Total']), "is_absent": bool(r['Abs'])
                        })
                    
                    supabase.table("marks").upsert(final_list, on_conflict="exam_id, emis_no, subject_id").execute()
                    # மெமரியை (Session State) அப்டேட் செய்கிறோம்
                    st.session_state[state_key].update(edited_df)
                    st.success("✅ வெற்றிகரமாகச் சேமிக்கப்பட்டது!")
                    st.rerun()
