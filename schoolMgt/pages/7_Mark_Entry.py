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

            # ⚡ 3. தரவு சேமிப்பு (Session State) - இது ஒருமுறை மட்டுமே நடக்கும்
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

            # ⚡ 4. 10 & 20 விரைவு உள்ளீடு (Buttons)
            st.divider()
            f1, f2 = st.columns(2)
            if f1.button(f"அனைவருக்கும் Internal {max_i} நிரப்புக"):
                st.session_state[state_key]['Internal'] = max_i
                st.rerun()
            if max_p > 0 and f2.button(f"அனைவருக்கும் Practical {max_p} நிரப்புக"):
                st.session_state[state_key]['Practical'] = max_p
                st.rerun()

            # ⚡ 5. எக்செல் எடிட்டர் (Form-க்குள் வைப்பதன் மூலம் 'Lag' தவிர்க்கப்படுகிறது)
            with st.form("mark_form", clear_on_submit=False):
                df = st.session_state[state_key]
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
                    hide_index=True, use_container_width=True, key="form_editor"
                )

                submit_button = st.form_submit_button("🚀 சரிபார்த்துச் சேமி", use_container_width=True)

                if submit_button:
                    # ⚡ மொத்தம் கணக்கிடுதல்
                    edited_df['Total'] = edited_df['Theory'].fillna(0) + edited_df['Internal'].fillna(0) + edited_df.get('Practical', 0).fillna(0)
                    edited_df.loc[edited_df['Abs'] == True, ['Theory', 'Practical', 'Internal', 'Total']] = 0
                    
                    final_list = []
                    for idx, r in edited_df.iterrows():
                        final_list.append({
                            "exam_id": exam_id, "emis_no": df.iloc[idx]['EMIS'], "subject_id": sub_code,
                            "theory_mark": int(r['Theory']), "practical_mark": int(r.get('Practical', 0)),
                            "internal_mark": int(r['Internal']), "total_mark": int(r['Total']), "is_absent": bool(r['Abs'])
                        })
                    
                    supabase.table("marks").upsert(final_list, on_conflict="exam_id, emis_no, subject_id").execute()
                    st.session_state[state_key].update(edited_df) # மெமரியை அப்டேட் செய்கிறோம்
                    st.success("✅ அனைத்து மதிப்பெண்களும் சேமிக்கப்பட்டன!")
                    st.rerun()
