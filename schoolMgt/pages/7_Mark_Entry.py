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
st.title("📊 மதிப்பெண் பதிவேற்றம் & திருத்தம் (Excel Style)")

# --- 1. அடிப்படைத் தரவுகளைப் பெறுதல் ---
exams = supabase.table("exams").select("*").eq("exam_status", "Active").execute().data
all_subjects = supabase.table("subjects").select("*").execute().data
all_classes = supabase.table("classes").select("*").execute().data

# --- 2. டைனமிக் பில்டர் (Dynamic Filters) ---
c1, c2, c3 = st.columns(3)

sel_exam_name = c1.selectbox("1. தேர்வைத் தேர்ந்தெடுக்கவும்:", ["-- Select --"] + [e['exam_name'] for e in exams])

if sel_exam_name != "-- Select --":
    exam_id = next(e['id'] for e in exams if e['exam_name'] == sel_exam_name)
    
    # தேர்வு செய்த தேர்வுக்குரிய வகுப்புகள்
    class_list = sorted(list(set([c['class_name'] for c in all_classes])))
    sel_class = c2.selectbox("2. வகுப்பைத் தேர்ந்தெடுக்கவும்:", ["-- Select --"] + class_list)

    if sel_class != "-- Select --":
        # தேர்வு செய்த வகுப்பிற்குரிய பாடங்கள்
        sub_list = [s['subject_name'] for s in all_subjects]
        sel_sub_name = c3.selectbox("3. பாடத்தைத் தேர்ந்தெடுக்கவும்:", ["-- Select --"] + sub_list)

        if sel_sub_name != "-- Select --":
            sub_info = next(s for s in all_subjects if s['subject_name'] == sel_sub_name)
            sub_code = sub_info.get('subject_code')
            eval_type = sub_info.get('eval_type', '90+10')
            parts = eval_type.split('+')
            max_t, max_p, max_i = int(parts[0]), (int(parts[1]) if len(parts) > 2 else 0), int(parts[-1])

            # --- 3. மாணவர் பட்டியல் & ஏற்கனவே உள்ள மதிப்பெண்கள் ---
            # மாணவர் விவரம் (Exam Mapping-லிருந்து)
            students = supabase.table("exam_mapping").select("exam_no, student_name, emis_no").eq("exam_id", exam_id).eq("class_name", sel_class).order("exam_no").execute().data
            
            # ஏற்கனவே வழங்கப்பட்ட மதிப்பெண்கள் (Marks Table-லிருந்து)
            existing_marks = supabase.table("marks").select("*").eq("exam_id", exam_id).eq("subject_id", sub_code).execute().data
            marks_dict = {m['emis_no']: m for m in existing_marks}

            # அட்டவணைத் தரவை உருவாக்குதல்
            table_data = []
            for s in students:
                m = marks_dict.get(s['emis_no'], {}) # ஏற்கனவே மதிப்பெண் இருந்தால் அதை எடுக்கும்
                row = {
                    "Exam No": s['exam_no'],
                    "Student Name": s['student_name'],
                    "EMIS": s['emis_no'],
                    "Abs": m.get('is_absent', False),
                    "Theory": m.get('theory_mark', 0),
                    "Internal": m.get('internal_mark', i_val if 'i_val' in locals() else 0),
                    "Total": m.get('total_mark', 0)
                }
                if max_p > 0:
                    row["Practical"] = m.get('practical_mark', 0)
                table_data.append(row)

            df = pd.DataFrame(table_data)

            # --- 4. எக்செல் எடிட்டர் (Freeze Panes & Edit Enabled) ---
            st.divider()
            st.subheader(f"📝 {sel_class} - {sel_sub_name} மதிப்பெண் பட்டியல்")
            
            # Key-ஐ மாற்றுவதன் மூலம் புதிய பாடம் எடுக்கும்போது அட்டவணை புதுப்பிக்கப்படும்
            editor_key = f"edit_{exam_id}_{sel_class}_{sub_code}"
            
            edited_df = st.data_editor(
                df,
                column_config={
                    "Exam No": st.column_config.TextColumn("தேர்வு எண்", disabled=True, pinned=True),
                    "Student Name": st.column_config.TextColumn("மாணவர் பெயர்", disabled=True, pinned=True),
                    "EMIS": None, # EMIS எண்ணை மறைக்க
                    "Abs": st.column_config.CheckboxColumn("Abs"),
                    "Theory": st.column_config.NumberColumn(f"Theo({max_t})", min_value=0, max_value=max_t),
                    "Practical": st.column_config.NumberColumn(f"Prac({max_p})", min_value=0, max_value=max_p) if max_p > 0 else None,
                    "Internal": st.column_config.NumberColumn(f"Int({max_i})", min_value=0, max_value=max_i),
                    "Total": st.column_config.NumberColumn("Total", disabled=True),
                },
                hide_index=True,
                use_container_width=True,
                key=editor_key
            )

            # ⚡ 5. மொத்தம் கணக்கிடுதல் (திருத்தம் செய்யும்போதும் இது மாறும்)
            edited_df['Total'] = edited_df['Theory'] + edited_df.get('Practical', 0) + edited_df['Internal']
            edited_df.loc[edited_df['Abs'] == True, ['Theory', 'Practical', 'Internal', 'Total']] = 0

            # --- 6. சேமித்தல் (Upsert - புதிய தரவு என்றால் சேமிக்கும், பழையது என்றால் திருத்தும்) ---
            if st.button("🚀 மாற்றங்களைச் சேமி", use_container_width=True, type="primary"):
                final_list = []
                for _, r in edited_df.iterrows():
                    final_list.append({
                        "exam_id": exam_id,
                        "emis_no": r['EMIS'],
                        "subject_id": sub_code,
                        "theory_mark": int(r['Theory']),
                        "practical_mark": int(r.get('Practical', 0)),
                        "internal_mark": int(r['Internal']),
                        "total_mark": int(r['Total']),
                        "is_absent": bool(r['Abs'])
                    })
                
                # 'upsert' பழைய மதிப்பெண்களைத் தானாகவே திருத்திவிடும் (Update)
                supabase.table("marks").upsert(final_list, on_conflict="exam_id, emis_no, subject_id").execute()
                st.success(f"✅ {sel_sub_name} மதிப்பெண்கள் வெற்றிகரமாகப் புதுப்பிக்கப்பட்டன!")
                st.balloons()
