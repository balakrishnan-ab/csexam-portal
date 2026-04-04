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

# ⚡ CSS - தடிமனான எழுத்துக்கள்
st.markdown("<style>.stDataFrame { font-size: 18px !important; font-weight: bold !important; }</style>", unsafe_allow_html=True)

st.title("📊 மதிப்பெண் பதிவேற்றம் & திருத்தம்")

# --- 1. தரவுகள் (Exams, Classes, Groups, Subjects) ---
exams = supabase.table("exams").select("*").eq("exam_status", "Active").execute().data
all_classes = supabase.table("classes").select("*").execute().data
all_groups = supabase.table("groups").select("*").execute().data
all_subjects = supabase.table("subjects").select("*").execute().data

# --- 2. தேர்வுப் பெட்டிகள் (Dynamic Selection) ---
c1, c2, c3 = st.columns(3)

sel_exam_name = c1.selectbox("1. தேர்வு:", ["-- தேர்வு செய்க --"] + [e['exam_name'] for e in exams])

if sel_exam_name != "-- தேர்வு செய்க --":
    exam_id = next(e['id'] for e in exams if e['exam_name'] == sel_exam_name)
    
    # வகுப்புத் தெரிவு
    class_names = [c['class_n'] for c in all_classes] # உங்கள் படத்தில் 'class_n' என்று உள்ளது
    sel_class = c2.selectbox("2. வகுப்பு:", ["-- தேர்வு செய்க --"] + class_names)

    if sel_class != "-- தேர்வு செய்க --":
        # ⚡ 3. டைனமிக் பாடப்பிரிவு மற்றும் பாடங்கள் கண்டறிதல்
        # அ. வகுப்பிலிருந்து பாடப்பிரிவுப் பெயரைக் கண்டுபிடித்தல் (group_name)
        class_info = next(c for c in all_classes if c['class_n'] == sel_class)
        group_name_from_class = class_info.get('group_name')

        filtered_subs = []
        if group_name_from_class:
            # ஆ. பாடப்பிரிவு அட்டவணையில் இருந்து அந்தப் பிரிவின் பாடங்களை எடுத்தல் (subjects column)
            group_info = next((g for g in all_groups if g['group_name'] == group_name_from_class), None)
            
            if group_info and group_info.get('subjects'):
                # இ. கமாவால் பிரிக்கப்பட்ட பாடங்களை தனித்தனியாகப் பிரித்தல் (Split by comma)
                raw_subs = [s.strip() for s in group_info['subjects'].split(',')]
                # ஈ. பெயர்களைச் சரிபார்த்துப் பட்டியலிடுதல்
                filtered_subs = raw_subs

        # பாடத் தெரிவு
        sel_sub_name = c3.selectbox("3. பாடம்:", ["-- தேர்வு செய்க --"] + filtered_subs)

        if sel_sub_name != "-- தேர்வு செய்க --":
            # பாட விவரம் (max marks போன்றவை)
            sub_info = next((s for s in all_subjects if s['subject_name'] == sel_sub_name), None)
            
            if sub_info:
                sub_code = sub_info.get('subject_code')
                eval_type = sub_info.get('eval_type', '90+10')
                parts = eval_type.split('+')
                max_t, max_p, max_i = int(parts[0]), (int(parts[1]) if len(parts) > 2 else 0), int(parts[-1])

                # --- 4. மாணவர் மற்றும் மதிப்பெண் பதிவுகள் ---
                students = supabase.table("exam_mapping").select("exam_no, student_name, emis_no").eq("exam_id", exam_id).eq("class_name", sel_class).order("exam_no").execute().data
                existing_marks = supabase.table("marks").select("*").eq("exam_id", exam_id).eq("subject_id", sub_code).execute().data
                marks_dict = {m['emis_no']: m for m in existing_marks}

                data = []
                for s in students:
                    m = marks_dict.get(s['emis_no'], {})
                    row = {
                        "Exam No": s['exam_no'], "Student Name": s['student_name'], "EMIS": s['emis_no'],
                        "Abs": m.get('is_absent', False), "Theory": m.get('theory_mark', 0),
                        "Internal": m.get('internal_mark', 0)
                    }
                    if max_p > 0: row["Practical"] = m.get('practical_mark', 0)
                    row["Total"] = m.get('total_mark', 0)
                    data.append(row)

                df = pd.DataFrame(data)

                # --- 5. எக்செல் எடிட்டர் ---
                st.divider()
                # வரிசை அமைப்பு: Theory, Practical (இருந்தால்), Internal, Total
                cols_config = ["Exam No", "Student Name", "Abs", "Theory"]
                if max_p > 0: cols_config.append("Practical")
                cols_config.extend(["Internal", "Total"])

                edited_df = st.data_editor(
                    df[cols_config],
                    column_config={
                        "Exam No": st.column_config.TextColumn("தேர்வு எண்", disabled=True, pinned=True),
                        "Student Name": st.column_config.TextColumn("மாணவர் பெயர்", disabled=True, pinned=True),
                        "Theory": st.column_config.NumberColumn(f"Theo({max_t})"),
                        "Practical": st.column_config.NumberColumn(f"Prac({max_p})") if max_p > 0 else None,
                        "Internal": st.column_config.NumberColumn(f"Int({max_i})"),
                        "Total": st.column_config.NumberColumn("மொத்தம்", disabled=True),
                    },
                    hide_index=True, use_container_width=True,
                    key=f"edit_{exam_id}_{sel_class}_{sub_code}"
                )

                # கணக்கீடு
                edited_df['Total'] = edited_df['Theory'] + edited_df.get('Practical', 0) + edited_df['Internal']
                edited_df.loc[edited_df['Abs'] == True, ['Theory', 'Practical', 'Internal', 'Total']] = 0

                # --- 6. சேமித்தல் ---
                if st.button("🚀 சேமிக்க", use_container_width=True, type="primary"):
                    final_list = []
                    for _, r in edited_df.iterrows():
                        final_list.append({
                            "exam_id": exam_id, "emis_no": r['EMIS'] if 'EMIS' in r else df.iloc[_]['EMIS'], 
                            "subject_id": sub_code, "theory_mark": int(r['Theory']), 
                            "practical_mark": int(r.get('Practical', 0)), "internal_mark": int(r['Internal']), 
                            "total_mark": int(r['Total']), "is_absent": bool(r['Abs'])
                        })
                    supabase.table("marks").upsert(final_list, on_conflict="exam_id, emis_no, subject_id").execute()
                    st.success("✅ வெற்றிகரமாகச் சேமிக்கப்பட்டது!")
            else:
                st.warning("⚠️ தேர்ந்தெடுக்கப்பட்ட பாடத்தின் விவரங்கள் 'subjects' அட்டவணையில் இல்லை.")
