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

# ⚡ எழுத்துக்களைப் பெரிதாக்கவும் தடிமனாக்கவும் CSS
st.markdown("""
    <style>
    .stDataFrame div[data-testid="stTable"] { font-size: 20px !important; font-weight: bold !important; }
    .stSelectbox label { font-size: 18px !important; font-weight: bold !important; }
    button[data-testid="stBaseButton-primary"] { font-size: 20px !important; font-weight: bold !important; }
    </style>
    """, unsafe_allow_html=True)

st.title("📊 மதிப்பெண் பதிவேற்றம் (வகுப்பு வாரியான பாடங்கள்)")

# --- 1. அடிப்படைத் தரவுகள் ---
exams = supabase.table("exams").select("*").eq("exam_status", "Active").execute().data
all_subjects = supabase.table("subjects").select("*").execute().data
all_classes = supabase.table("classes").select("*").execute().data

# --- 2. டைனமிக் பில்டர் (வகுப்பு -> பாடம்) ---
c1, c2, c3 = st.columns(3)

# A. தேர்வுத் தெரிவு
sel_exam_name = c1.selectbox("1. தேர்வைத் தேர்ந்தெடுக்கவும்:", ["-- தேர்வு செய்க --"] + [e['exam_name'] for e in exams])

if sel_exam_name != "-- தேர்வு செய்க --":
    exam_id = next(e['id'] for e in exams if e['exam_name'] == sel_exam_name)
    
    # B. வகுப்புத் தெரிவு
    class_list = sorted(list(set([c['class_name'] for c in all_classes])))
    sel_class = c2.selectbox("2. வகுப்பைத் தேர்ந்தெடுக்கவும்:", ["-- தேர்வு செய்க --"] + class_list)

    if sel_class != "-- தேர்வு செய்க --":
        # ⚡ 3. வகுப்பு வாரியாகப் பாடங்களை வடிகட்டுதல் (Dynamic Logic)
        # உங்கள் பாடப் பட்டியலில் 'Biology' இருந்தால் அது A பிரிவுக்கும், 'Computer Science' இருந்தால் அது B பிரிவுக்கும் வருமாறு அமைக்கலாம்
        
        filtered_subs = []
        if "11-A" in sel_class or "12-A" in sel_class:
            # A பிரிவிற்கான பாடங்கள் (உதாரணம்)
            science_group = ["Tamil", "English", "Physics", "Chemistry", "Biology", "Mathematics"]
            filtered_subs = [s['subject_name'] for s in all_subjects if s['subject_name'] in science_group]
        elif "11-B" in sel_class or "12-B" in sel_class:
            # B பிரிவிற்கான பாடங்கள் (உதாரணம்)
            cs_group = ["Tamil", "English", "Physics", "Chemistry", "Computer Science", "Mathematics"]
            filtered_subs = [s['subject_name'] for s in all_subjects if s['subject_name'] in cs_group]
        else:
            # மற்ற வகுப்புகளுக்கு எல்லா பாடங்களும்
            filtered_subs = [s['subject_name'] for s in all_subjects]

        # C. வடிகட்டப்பட்ட பாடத் தெரிவு
        sel_sub_name = c3.selectbox("3. பாடத்தைத் தேர்ந்தெடுக்கவும்:", ["-- தேர்வு செய்க --"] + filtered_subs)

        if sel_sub_name != "-- தேர்வு செய்க --":
            sub_info = next(s for s in all_subjects if s['subject_name'] == sel_sub_name)
            sub_code = sub_info.get('subject_code')
            eval_type = sub_info.get('eval_type', '90+10')
            parts = eval_type.split('+')
            max_t, max_p, max_i = int(parts[0]), (int(parts[1]) if len(parts) > 2 else 0), int(parts[-1])

            # --- 4. தரவு சேகரிப்பு & ஏற்கனவே உள்ள மதிப்பெண்கள் ---
            students = supabase.table("exam_mapping").select("exam_no, student_name, emis_no").eq("exam_id", exam_id).eq("class_name", sel_class).order("exam_no").execute().data
            existing_marks = supabase.table("marks").select("*").eq("exam_id", exam_id).eq("subject_id", sub_code).execute().data
            marks_dict = {m['emis_no']: m for m in existing_marks}

            # அட்டவணைத் தரவு
            table_data = []
            for s in students:
                m = marks_dict.get(s['emis_no'], {})
                row = {
                    "Exam No": s['exam_no'],
                    "Student Name": s['student_name'],
                    "EMIS": s['emis_no'],
                    "Abs": m.get('is_absent', False),
                    "Theory": m.get('theory_mark', 0),
                    "Internal": m.get('internal_mark', 0),
                }
                if max_p > 0: row["Practical"] = m.get('practical_mark', 0)
                row["Total"] = m.get('total_mark', 0)
                table_data.append(row)

            df = pd.DataFrame(table_data)

            # --- 5. விரைவு உள்ளீடு (Checkboxes) ---
            st.divider()
            f1, f2 = st.columns(2)
            if f1.checkbox(f"அனைவருக்கும் அகமதிப்பீடு {max_i} நிரப்புக"):
                df['Internal'] = max_i
            if max_p > 0 and f2.checkbox(f"அனைவருக்கும் செய்முறை {max_p} நிரப்புக"):
                df['Practical'] = max_p

            # --- 6. எக்செல் எடிட்டர் (Freeze Panes) ---
            st.write(f"### 📝 {sel_class} - {sel_sub_name} பட்டியல்")
            
            edited_df = st.data_editor(
                df,
                column_config={
                    "Exam No": st.column_config.TextColumn("தேர்வு எண்", disabled=True, pinned=True),
                    "Student Name": st.column_config.TextColumn("மாணவர் பெயர்", disabled=True, pinned=True),
                    "EMIS": None,
                    "Abs": st.column_config.CheckboxColumn("Abs"),
                    "Theory": st.column_config.NumberColumn(f"Theo({max_t})"),
                    "Practical": st.column_config.NumberColumn(f"Prac({max_p})") if max_p > 0 else None,
                    "Internal": st.column_config.NumberColumn(f"Int({max_i})"),
                    "Total": st.column_config.NumberColumn("மொத்தம்", disabled=True),
                },
                hide_index=True,
                use_container_width=True,
                key=f"editor_{exam_id}_{sel_class}_{sub_code}"
            )

            # கணக்கீடு
            edited_df['Total'] = edited_df['Theory'] + edited_df.get('Practical', 0) + edited_df['Internal']
            edited_df.loc[edited_df['Abs'] == True, ['Theory', 'Practical', 'Internal', 'Total']] = 0

            # --- 7. சேமித்தல் ---
            if st.button("🚀 மதிப்பெண்களைச் சேமி / திருத்து", use_container_width=True, type="primary"):
                final_marks = []
                for _, r in edited_df.iterrows():
                    final_marks.append({
                        "exam_id": exam_id, "emis_no": r['EMIS'], "subject_id": sub_code,
                        "theory_mark": int(r['Theory']), "practical_mark": int(r.get('Practical', 0)),
                        "internal_mark": int(r['Internal']), "total_mark": int(r['Total']), "is_absent": bool(r['Abs'])
                    })
                supabase.table("marks").upsert(final_marks, on_conflict="exam_id, emis_no, subject_id").execute()
                st.success("✅ தரவுகள் வெற்றிகரமாகப் புதுப்பிக்கப்பட்டன!")
