import streamlit as st
import pandas as pd
from supabase import create_client
from io import BytesIO

# --- Supabase Connection ---
def get_supabase_client():
    if "supabase_instance" not in st.session_state:
        st.session_state.supabase_instance = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
    return st.session_state.supabase_instance

supabase = get_supabase_client()

st.set_page_config(page_title="Mark Entry System", layout="wide")
st.title("📊 மதிப்பெண் பதிவேற்றம் & திருத்தம்")

# தரவுகளைப் பெறுதல்
exams = supabase.table("exams").select("*").eq("exam_status", "Active").execute().data
all_classes = supabase.table("classes").select("*").execute().data
all_groups = supabase.table("groups").select("*").execute().data
all_subjects = supabase.table("subjects").select("*").execute().data

sel_exam_name = st.selectbox("தேர்வைத் தேர்ந்தெடுக்கவும்:", ["-- தேர்வு செய்க --"] + [e['exam_name'] for e in exams])

if sel_exam_name != "-- தேர்வு செய்க --":
    exam_id = next(e['id'] for e in exams if e['exam_name'] == sel_exam_name)

    # 1. தரவை எக்செல்/எடிட்டர் வடிவில் தயார் செய்யும் பங்க்ஷன்
    def generate_df(c_name, sub_filter=None):
        mapping = supabase.table("exam_mapping").select("emis_no, student_name").eq("exam_id", exam_id).eq("class_name", c_name).execute().data
        df = pd.DataFrame(mapping)
        
        cls_info = next((c for c in all_classes if c['class_name'] == c_name), None)
        g_info = next((g for g in all_groups if g['group_name'] == cls_info.get('group_name')), None)
        sub_list = [sub_filter] if sub_filter else [s.strip() for s in g_info['subjects'].split(',')]

        for s_name in sub_list:
            sub = next((x for x in all_subjects if x['subject_name'] == s_name), None)
            if sub:
                marks_db = supabase.table("marks").select("emis_no, theory_mark, internal_mark, practical_mark, is_absent").eq("exam_id", exam_id).eq("subject_id", sub['subject_code']).execute().data
                m_dict = {str(m['emis_no']): m for m in marks_db}

                # Absent மற்றும் மதிப்பெண் காலங்களைச் சேர்த்தல்
                df[f"Absent_{s_name}"] = df['emis_no'].apply(lambda x: m_dict.get(str(x), {}).get('is_absent', False))
                df[f"Theory_{s_name}"] = df['emis_no'].apply(lambda x: m_dict.get(str(x), {}).get('theory_mark', 0))
                
                eval_type_raw = str(sub.get('eval_type', '100'))
                eval_parts = [int(p) for p in eval_type_raw.split('+') if p.strip().isdigit()]
                
                for i in range(1, len(eval_parts)):
                    score = eval_parts[i]
                    if score in [10, 40]:
                        df[f"Internal_{s_name}"] = df['emis_no'].apply(lambda x: m_dict.get(str(x), {}).get('internal_mark', 0))
                    elif score in [20, 25]:
                        df[f"Practical_{s_name}"] = df['emis_no'].apply(lambda x: m_dict.get(str(x), {}).get('practical_mark', 0))
        return df

    # 2. Supabase-ல் சேமிக்கும் பங்க்ஷன்
    def save_to_supabase(df_uploaded, class_name=None):
        final_data = []
        error_found = False
        for _, row in df_uploaded.iterrows():
            for sub in all_subjects:
                s_name = sub['subject_name']
                a_col = f"Absent_{s_name}"
                t_col, i_col, p_col = f"Theory_{s_name}", f"Internal_{s_name}", f"Practical_{s_name}"
                
                if t_col in row.index:
                    is_abs = row.get(a_col, False)
                    t_val = pd.to_numeric(row.get(t_col, 0), errors='coerce') or 0
                    i_val = pd.to_numeric(row.get(i_col, 0), errors='coerce') or 0
                    p_val = pd.to_numeric(row.get(p_col, 0), errors='coerce') or 0
                    
                    eval_parts = [int(p) for p in str(sub.get('eval_type', '100')).split('+') if p.strip().isdigit()]
                    
                    if not is_abs and t_val > eval_parts[0]:
                        st.error(f"பிழை: {row['student_name']} - {s_name} தியரி மதிப்பெண் அதிகம்!")
                        error_found = True; break
                    
                    # Absent என்றால் மதிப்பெண்களை 0 ஆக மாற்றிச் சேமிக்கும்
                    final_data.append({
                        "exam_id": int(exam_id),
                        "emis_no": str(row['emis_no']),
                        "subject_id": str(sub['subject_code']),
                        "theory_mark": 0 if is_abs else int(t_val),
                        "internal_mark": 0 if is_abs else int(i_val),
                        "practical_mark": 0 if is_abs else int(p_val),
                        "total_mark": 0 if is_abs else int(t_val + i_val + p_val),
                        "is_absent": bool(is_abs)
                    })
            if error_found: break
        if not error_found and final_data:
            supabase.table("marks").upsert(final_data, on_conflict="exam_id, emis_no, subject_id").execute()
            st.success("மதிப்பெண்கள் வெற்றிகரமாகச் சேமிக்கப்பட்டன!")

    # 3. Tabs அமைப்பு
    tab1, tab2, tab3 = st.tabs(["👨‍🏫 பாட ஆசிரியர்", "📂 வகுப்பு ஆசிரியர்", "🏢 வகுப்பின் அனைத்துப் பிரிவுகள்"])

    with tab1:
        class_list = sorted(list(set([c['class_name'] for c in all_classes])))
        c1, c2 = st.columns(2)
        sel_c = c1.selectbox("வகுப்பு:", ["-- தேர்வு செய்க --"] + class_list, key="t1_c")
        if sel_c != "-- தேர்வு செய்க --":
            g_name = next(c['group_name'] for c in all_classes if c['class_name'] == sel_c)
            sub_list = [s.strip() for s in next(g['subjects'] for g in all_groups if g['group_name'] == g_name).split(',')]
            sel_s = c2.selectbox("பாடம்:", ["-- தேர்வு செய்க --"] + sub_list, key="t1_s")
            
            if sel_s != "-- தேர்வு செய்க --":
                state_key = f"df_{sel_c}_{sel_s}"
                if state_key not in st.session_state: st.session_state[state_key] = generate_df(sel_c, sel_s)
                
                df = st.session_state[state_key]
                sub = next((x for x in all_subjects if x['subject_name'] == sel_s), None)
                remaining = [int(p) for p in str(sub.get('eval_type', '100')).split('+') if p.strip().isdigit()][1:]
                
                if remaining:
                    cols = st.columns(len(remaining))
                    for i, val in enumerate(remaining):
                        if cols[i].button(f"Fill {val} to ALL"):
                            target = f"Internal_{sel_s}" if val in [10, 40] else f"Practical_{sel_s}"
                            if target in df.columns:
                                df[target] = val
                                st.session_state[state_key] = df
                                st.rerun()
                
                # Column configurations for better UI
                col_config = {
                    f"Absent_{sel_s}": st.column_config.CheckboxColumn("வராதவர் (Abs)", default=False),
                    "emis_no": st.column_config.TextColumn("EMIS No", disabled=True),
                    "student_name": st.column_config.TextColumn("மாணவர் பெயர்", disabled=True)
                }

                edited_df = st.data_editor(df, use_container_width=True, key=f"editor_{state_key}", column_config=col_config)
                st.session_state[state_key] = edited_df
                if st.button("சேமி", key="save1"): save_to_supabase(edited_df, sel_c)

    with tab2:
        sel_c2 = st.selectbox("வகுப்பு:", ["-- தேர்வு செய்க --"] + class_list, key="t2_c")
        if sel_c2 != "-- தேர்வு செய்க --":
            df_down = generate_df(sel_c2)
            output = BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer: df_down.to_excel(writer, index=False)
            st.download_button("📥 வகுப்பு கோப்பைத் தரவிறக்கு", data=output.getvalue(), file_name=f"Marks_{sel_c2}.xlsx")
            up = st.file_uploader("பதிவேற்று:", type=["xlsx"], key="up2")
            if up and st.button("சேமி", key="save2"): save_to_supabase(pd.read_excel(up), sel_c2)

    with tab3:
        grade = st.text_input("வகுப்பு எண் (எ.கா: 11):")
        if grade:
            relevant = sorted([c['class_name'] for c in all_classes if c['class_name'].startswith(grade)])
            output = BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                for c in relevant: 
                    generate_df(c).to_excel(writer, sheet_name=c, index=False)
            st.download_button("📥 அனைத்தையும் தரவிறக்கு", data=output.getvalue(), file_name=f"Marks_{grade}_All.xlsx")
            
            up3 = st.file_uploader("பதிவேற்று:", type=["xlsx"], key="up3")
            if up3 and st.button("சேமி", key="save3"):
                xl = pd.ExcelFile(up3)
                for sheet in xl.sheet_names: 
                    save_to_supabase(pd.read_excel(xl, sheet_name=sheet), sheet)
    with tab4:
        st.subheader("📋 பாடவாரி விரிவான பகுப்பாய்வு")
        
        # தற்போதைய தேர்விற்கான அனைத்து மதிப்பெண்களையும் பெறுதல்
        marks_response = supabase.table("marks").select("*").eq("exam_id", exam_id).execute()
        marks_data = marks_response.data
        
        if not marks_data:
            st.warning("தேர்ந்தெடுக்கப்பட்ட தேர்விற்கு இன்னும் மதிப்பெண்கள் பதியப்படவில்லை.")
        else:
            m_df = pd.DataFrame(marks_data)
            analysis_list = []

            # ஒவ்வொரு பாடமாக ஆய்வு செய்தல்
            for sub in all_subjects:
                s_id = str(sub['subject_code'])
                s_name = sub['subject_name']
                
                # இந்த பாடத்திற்கான மதிப்பெண்கள் மட்டும்
                sub_marks = m_df[m_df['subject_id'] == s_id]
                
                if not sub_marks.empty:
                    # 1. Total - மொத்த மாணவர்கள்
                    total_stu = len(sub_marks)
                    
                    # 2. App - தேர்வு எழுதியவர்கள் (Absent அல்லாதவர்கள்)
                    appeared_df = sub_marks[sub_marks['is_absent'] == False]
                    app_count = len(appeared_df)
                    
                    # 3. Pass/Fail (35 மதிப்பெண் தேர்ச்சி எனில்)
                    pass_df = appeared_df[appeared_df['total_mark'] >= 35]
                    pass_count = len(pass_df)
                    fail_count = app_count - pass_count
                    
                    # 4. Pass%
                    pass_pc = round((pass_count / app_count) * 100, 2) if app_count > 0 else 0
                    
                    # 5. Min, Max, Avg
                    min_mark = appeared_df['total_mark'].min() if app_count > 0 else 0
                    max_mark = appeared_df['total_mark'].max() if app_count > 0 else 0
                    avg_mark = round(appeared_df['total_mark'].mean(), 2) if app_count > 0 else 0
                    
                    analysis_list.append({
                        "Subject": s_name,
                        "Total": total_stu,
                        "App": app_count,
                        "Pass": pass_count,
                        "Fail": fail_count,
                        "Pass%": f"{pass_pc}%",
                        "Min": min_mark,
                        "Max": max_mark,
                        "Avg": avg_mark
                    })

            if analysis_list:
                ana_df = pd.DataFrame(analysis_list)
                
                # அட்டவணையைத் திரையில் காட்டுதல்
                st.dataframe(ana_df, use_container_width=True, hide_index=True)
                
                # Excel தரவிறக்கம்
                output_ana = BytesIO()
                with pd.ExcelWriter(output_ana, engine='xlsxwriter') as writer:
                    ana_df.to_excel(writer, index=False, sheet_name='Analysis')
                st.download_button("📥 பகுப்பாய்வு அறிக்கையைத் தரவிறக்கு", data=output_ana.getvalue(), file_name=f"Subject_Analysis_{sel_exam_name}.xlsx")
