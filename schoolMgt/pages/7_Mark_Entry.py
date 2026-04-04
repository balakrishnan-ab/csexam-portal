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

# ⚡ எழுத்துக்களைப் பெரிதாக்க மற்றும் தடிமனாக்க CSS
st.markdown("""
    <style>
    .stDataFrame div[data-testid="stTable"] { font-size: 18px !important; font-weight: bold !important; }
    div[data-testid="column"] { font-size: 18px !important; font-weight: bold !important; }
    input { font-size: 18px !important; font-weight: bold !important; }
    </style>
    """, unsafe_allow_html=True)

st.title("📊 மதிப்பெண் பதிவேற்றம் & திருத்தம்")

# --- 1. தரவுகளைப் பெறுதல் ---
exams = supabase.table("exams").select("*").eq("exam_status", "Active").execute().data
all_subjects = supabase.table("subjects").select("*").execute().data
all_classes = supabase.table("classes").select("*").execute().data

# --- 2. டைனமிக் பில்டர் ---
c1, c2, c3 = st.columns(3)

sel_exam_name = c1.selectbox("1. தேர்வு:", ["-- தேர்வு செய்க --"] + [e['exam_name'] for e in exams])

if sel_exam_name != "-- தேர்வு செய்க --":
    exam_id = next(e['id'] for e in exams if e['exam_name'] == sel_exam_name)
    
    # வகுப்புகள்
    class_list = sorted(list(set([c['class_name'] for c in all_classes])))
    sel_class = c2.selectbox("2. வகுப்பு:", ["-- தேர்வு செய்க --"] + class_list)

    if sel_class != "-- தேர்வு செய்க --":
        # ⚡ திருத்தம்: அந்த வகுப்புக்குரிய பாடங்களை மட்டும் வடிகட்டுதல்
        # (உங்கள் database-ல் subjects table-ல் class_name இருந்தால் இதை பயன்படுத்தலாம்)
        # தற்போது எல்லா பாடங்களையும் காட்டி, தேர்வு செய்த பின் அதன் மதிப்பெண்களைக் கையாள்கிறோம்
        sub_list = [s['subject_name'] for s in all_subjects]
        sel_sub_name = c3.selectbox("3. பாடம்:", ["-- தேர்வு செய்க --"] + sub_list)

        if sel_sub_name != "-- தேர்வு செய்க --":
            sub_info = next(s for s in all_subjects if s['subject_name'] == sel_sub_name)
            sub_code = sub_info.get('subject_code')
            eval_type = sub_info.get('eval_type', '90+10')
            parts = eval_type.split('+')
            max_t, max_p, max_i = int(parts[0]), (int(parts[1]) if len(parts) > 2 else 0), int(parts[-1])

            # --- 3. தரவுப் பதிவேற்றம் ---
            students = supabase.table("exam_mapping").select("exam_no, student_name, emis_no").eq("exam_id", exam_id).eq("class_name", sel_class).order("exam_no").execute().data
            existing_marks = supabase.table("marks").select("*").eq("exam_id", exam_id).eq("subject_id", sub_code).execute().data
            marks_dict = {m['emis_no']: m for m in existing_marks}

            data = []
            for s in students:
                m = marks_dict.get(s['emis_no'], {})
                row = {
                    "Exam No": s['exam_no'],
                    "Student Name": s['student_name'],
                    "EMIS": s['emis_no'],
                    "Abs": m.get('is_absent', False),
                    "Theory": m.get('theory_mark', 0),
                    "Internal": m.get('internal_mark', 0),
                    "Total": m.get('total_mark', 0)
                }
                if max_p > 0: row["Practical"] = m.get('practical_mark', 0)
                data.append(row)

            df = pd.DataFrame(data)

            # --- 4. ⚡ விரைவு உள்ளீடு (Checkboxes) ---
            st.divider()
            st.subheader("⚙️ விரைவு உள்ளீடு (Bulk Fill)")
            f1, f2 = st.columns(2)
            
            fill_internal = f1.checkbox(f"அனைவருக்கும் Internal {max_i} வழங்குக")
            if fill_internal:
                df['Internal'] = max_i
                
            fill_practical = False
            if max_p > 0:
                fill_practical = f2.checkbox(f"அனைவருக்கும் Practical {max_p} வழங்குக")
                if fill_practical:
                    df['Practical'] = max_p

            # --- 5. எக்செல் எடிட்டர் ---
            st.write(f"### 📝 {sel_class} - {sel_sub_name}")
            
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
                    "Total": st.column_config.NumberColumn("Total", disabled=True),
                },
                hide_index=True,
                use_container_width=True,
                key=f"edit_{exam_id}_{sel_class}_{sub_code}"
            )

            # மொத்தம் கணக்கீடு
            edited_df['Total'] = edited_df['Theory'] + edited_df.get('Practical', 0) + edited_df['Internal']
            edited_df.loc[edited_df['Abs'] == True, ['Theory', 'Practical', 'Internal', 'Total']] = 0

            # --- 6. சேமித்தல் ---
            if st.button("🚀 மாற்றங்களைச் சேமி", use_container_width=True, type="primary"):
                final_list = []
                for _, r in edited_df.iterrows():
                    final_list.append({
                        "exam_id": exam_id, "emis_no": r['EMIS'], "subject_id": sub_code,
                        "theory_mark": int(r['Theory']), "practical_mark": int(r.get('Practical', 0)),
                        "internal_mark": int(r['Internal']), "total_mark": int(r['Total']), "is_absent": bool(r['Abs'])
                    })
                
                supabase.table("marks").upsert(final_list, on_conflict="exam_id, emis_no, subject_id").execute()
                st.success("✅ வெற்றிகரமாகப் புதுப்பிக்கப்பட்டது!")
                st.balloons()
