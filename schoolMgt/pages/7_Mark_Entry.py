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

# ⚡ CSS - தடிமனான மற்றும் பெரிய எழுத்துக்கள்
st.markdown("""
    <style>
    .stDataFrame { font-size: 19px !important; font-weight: bold !important; }
    .stCheckbox label { font-size: 18px !important; font-weight: bold !important; color: blue; }
    </style>
    """, unsafe_allow_html=True)

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
        # டைனமிக் பாடங்கள்
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
        
        sel_display_name = c3.selectbox("3. பாடம் (குறியீடு):", ["-- தேர்வு செய்க --"] + list(subject_options.keys()))

        if sel_display_name != "-- தேர்வு செய்க --":
            sub_info = subject_options[sel_display_name]
            sub_code = sub_info['subject_code']
            eval_type = sub_info.get('eval_type', '90+10')
            parts = eval_type.split('+')
            max_t, max_p, max_i = int(parts[0]), (int(parts[1]) if len(parts) > 2 else 0), int(parts[-1])

            # ⚡ மாணவர் பட்டியல் - Session State-ல் சேமிக்கிறோம் (Update செய்ய வசதியாக)
            state_key = f"df_{exam_id}_{sel_class}_{sub_code}"
            
            if state_key not in st.session_state:
                students = supabase.table("exam_mapping").select("exam_no, student_name, emis_no").eq("exam_id", exam_id).eq("class_name", sel_class).order("exam_no").execute().data
                existing_marks = supabase.table("marks").select("*").eq("exam_id", exam_id).eq("subject_id", sub_code).execute().data
                marks_dict = {m['emis_no']: m for m in existing_marks}

                data = []
                for s in students:
                    m = marks_dict.get(s['emis_no'], {})
                    row = {
                        "Exam No": s['exam_no'], "Student Name": s['student_name'], "EMIS": s['emis_no'],
                        "Abs": m.get('is_absent', False), "Theory": m.get('theory_mark', 0),
                        "Internal": m.get('internal_mark', 0), "Practical": m.get('practical_mark', 0) if max_p > 0 else 0,
                        "Total": m.get('total_mark', 0)
                    }
                    data.append(row)
                st.session_state[state_key] = pd.DataFrame(data)

            df = st.session_state[state_key]

            # ⚙️ விரைவு உள்ளீடு (10 & 20)
            st.divider()
            f1, f2 = st.columns(2)
            if f1.checkbox(f"அனைவருக்கும் அகமதிப்பீடு {max_i} நிரப்புக", key="bulk_i"):
                df['Internal'] = max_i
                df['Total'] = df['Theory'] + df['Internal'] + df['Practical']
                st.session_state[state_key] = df
            
            if max_p > 0 and f2.checkbox(f"அனைவருக்கும் செய்முறை {max_p} நிரப்புக", key="bulk_p"):
                df['Practical'] = max_p
                df['Total'] = df['Theory'] + df['Internal'] + df['Practical']
                st.session_state[state_key] = df

            # ⚡ எக்செல் எடிட்டர்
            cols_show = ["Exam No", "Student Name", "Abs", "Theory"]
            if max_p > 0: cols_show.append("Practical")
            cols_show.extend(["Internal", "Total"])

            edited_df = st.data_editor(
                df[cols_show],
                column_config={
                    "Exam No": st.column_config.TextColumn("தேர்வு எண்", disabled=True, pinned=True),
                    "Student Name": st.column_config.TextColumn("பெயர்", disabled=True, pinned=True),
                    "Theory": st.column_config.NumberColumn(f"Theo({max_t})", min_value=0, max_value=max_t),
                    "Practical": st.column_config.NumberColumn(f"Prac({max_p})", min_value=0, max_value=max_p) if max_p > 0 else None,
                    "Internal": st.column_config.NumberColumn(f"Int({max_i})", min_value=0, max_value=max_i),
                    "Total": st.column_config.NumberColumn("மொத்தம்", disabled=True),
                },
                hide_index=True, use_container_width=True,
                key="editor_widget"
            )

            # ⚡ உடனுக்குடன் மொத்தம் அப்டேட் செய்ய:
            # எடிட்டரில் நடந்த மாற்றங்களை அசல் டேட்டாபிரேமுடன் இணைத்தல்
            edited_df['Total'] = edited_df['Theory'].fillna(0) + edited_df['Internal'].fillna(0) + edited_df.get('Practical', 0).fillna(0)
            edited_df.loc[edited_df['Abs'] == True, ['Theory', 'Practical', 'Internal', 'Total']] = 0
            
            # மாற்றங்களை சேமிக்க ஒரு பட்டன்
            if st.button("🚀 மதிப்பெண்களை உறுதி செய்து சேமி", use_container_width=True, type="primary"):
                final_list = []
                for idx, r in edited_df.iterrows():
                    final_list.append({
                        "exam_id": exam_id, "emis_no": df.iloc[idx]['EMIS'], 
                        "subject_id": sub_code, "theory_mark": int(r['Theory']), 
                        "practical_mark": int(r.get('Practical', 0)), "internal_mark": int(r['Internal']), 
                        "total_mark": int(r['Total']), "is_absent": bool(r['Abs'])
                    })
                supabase.table("marks").upsert(final_list, on_conflict="exam_id, emis_no, subject_id").execute()
                st.success("✅ வெற்றிகரமாகச் சேமிக்கப்பட்டது!")
                # சேமித்த பிறகு session state-ஐ புதுப்பிக்கலாம்
                st.session_state.pop(state_key)
                st.rerun()
