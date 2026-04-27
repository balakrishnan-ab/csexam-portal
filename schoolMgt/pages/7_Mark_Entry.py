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
        
        # பாட ஆசிரியர் பக்கம் எனில் ஒரு பாடம், இல்லையெனில் அனைத்து பாடங்கள்
        sub_list = [sub_filter] if sub_filter else [s.strip() for s in g_info['subjects'].split(',')]

        for s_name in sub_list:
            sub = next((x for x in all_subjects if x['subject_name'] == s_name), None)
            if sub:
                eval_type = str(sub.get('eval_type', '100'))
                marks_db = supabase.table("marks").select("emis_no, theory_mark, internal_mark, practical_mark").eq("exam_id", exam_id).eq("subject_id", sub['subject_code']).execute().data
                m_dict = {str(m['emis_no']): m for m in marks_db}

                # ஏற்கனவே மதிப்பெண் இருந்தால் அதைக் காட்டும், இல்லையெனில் 0
                df[f"Theory_{s_name}"] = df['emis_no'].apply(lambda x: m_dict.get(str(x), {}).get('theory_mark', 0))
                
                if "+" in eval_type:
                    # பாடத்தின் மதிப்பீட்டு முறையை பட்டியலாக மாற்றவும் (எ.கா: "70+20+10" -> [70, 20, 10])
                    parts = [int(p) for p in eval_type.split('+')]
                    # தியரி மதிப்பெண் (முதல் பகுதி எப்போதும் தியரி)
                    df[f"Theory_{s_name}"] = df['emis_no'].apply(lambda x: m_dict.get(str(x), {}).get('theory_mark', 0))
    
                    # மீதமுள்ள பகுதிகளை ஒவ்வொன்றாகச் சோதித்து Internal அல்லது Practical-ஆ எனத் தீர்மானிக்கவும்
                    for i in range(1, len(parts)):
                        score = parts[i]
                        
                        # 10 அல்லது 40 இருந்தால் அது 'Internal'
                        if score in [10, 40]:
                            df[f"Internal_{s_name}"] = df['emis_no'].apply(lambda x: m_dict.get(str(x), {}).get('internal_mark', 0))
    
                        # 20 அல்லது 25 இருந்தால் அது 'Practical'
                        elif score in [20, 25]:
                            df[f"Practical_{s_name}"] = df['emis_no'].apply(lambda x: m_dict.get(str(x), {}).get('practical_mark', 0))
        
        return df

    # 2. Supabase-ல் சேமிக்கும் பங்க்ஷன் (Validation-உடன்)
    def save_to_supabase(df_uploaded, class_name=None):
        final_data = []
        error_found = False
    
        for _, row in df_uploaded.iterrows():
            for sub in all_subjects:
                s_name = sub['subject_name']
                t_col, i_col, p_col = f"Theory_{s_name}", f"Internal_{s_name}", f"Practical_{s_name}"
            
                if t_col in row.index:
                    t_val = pd.to_numeric(row.get(t_col, 0), errors='coerce') or 0
                    i_val = pd.to_numeric(row.get(i_col, 0), errors='coerce') or 0
                    p_val = pd.to_numeric(row.get(p_col, 0), errors='coerce') or 0
                
                    # மதிப்பீட்டு முறை (எ.கா: 70+20+10)
                    eval_parts = [int(p) for p in str(sub.get('eval_type', '100')).split('+')]
                
                    # 1. தியரி மதிப்பெண் சரிபார்ப்பு (முதல் பகுதி)
                    if t_val > eval_parts[0]:
                        st.error(f"பிழை: {row['student_name']} - {s_name} தியரி மதிப்பெண் {eval_parts[0]-க்கு மேல் உள்ளது!")
                        error_found = True; break
                
                    # 2. மீதமுள்ள பகுதிகளை அதன் மதிப்புகளை வைத்து சரிபார்க்கவும்
                    for i in range(1, len(eval_parts)):
                        limit = eval_parts[i]
                        # limit 10 அல்லது 40 ஆக இருந்தால் அது Internal-ஐக் குறிக்கும்
                        if limit in [10, 40]:
                            if i_val > limit:
                                st.error(f"பிழை: {row['student_name']} - {s_name} Internal மதிப்பெண் {limit}-க்கு மேல் உள்ளது!")
                                error_found = True; break
                        # limit 20 அல்லது 25 ஆக இருந்தால் அது Practical-ஐக் குறிக்கும்
                        elif limit in [20, 25]:
                            if p_val > limit:
                                st.error(f"பிழை: {row['student_name']} - {s_name} Practical மதிப்பெண் {limit}-க்கு மேல் உள்ளது!")
                                error_found = True; break
                
                    if error_found: break
                
                    final_data.append({
                        "exam_id": int(exam_id),
                        "emis_no": str(row['emis_no']),
                        "subject_id": str(sub['subject_code']),
                        "theory_mark": int(t_val),
                        "internal_mark": int(i_val),
                        "practical_mark": int(p_val),
                        "total_mark": int(t_val + i_val + p_val)
                    })
            if error_found: break
    
        if not error_found and final_data:
            try:
                supabase.table("marks").upsert(final_data, on_conflict="exam_id, emis_no, subject_id").execute()
                st.success(f"வகுப்பு: {class_name if class_name else ''} - மதிப்பெண்கள் சேமிக்கப்பட்டன! 🎉")
            except Exception as e:
                st.error(f"சேமிப்பதில் பிழை: {e}")
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
                if state_key not in st.session_state:
                    st.session_state[state_key] = generate_df(sel_c, sel_s)
                
                df = st.session_state[state_key]
                
                # --- டைனமிக் பட்டன்கள் ---
                sub = next((x for x in all_subjects if x['subject_name'] == sel_s), None)
                eval_type = str(sub.get('eval_type', '100'))
                parts = eval_type.split('+')
                remaining_parts = parts[1:] 
                
                if remaining_parts:
                    cols = st.columns(len(remaining_parts))
                    for i, val in enumerate(remaining_parts):
                        if cols[i].button(f"Fill {val} to ALL"):
                            target_col = f"Internal_{sel_s}" if i == 0 else f"Practical_{sel_s}"
                            if target_col in df.columns:
                                df[target_col] = int(val)
                                st.session_state[state_key] = df
                                st.rerun()
                
                st.write("---")
                edited_df = st.data_editor(df, use_container_width=True, key=f"editor_{state_key}")
                st.session_state[state_key] = edited_df
                
                if st.button("சேமி", key="save1"): 
                    save_to_supabase(edited_df, sel_c)

    with tab2:
        sel_c2 = st.selectbox("வகுப்பு:", ["-- தேர்வு செய்க --"] + class_list, key="t2_c")
        if sel_c2 != "-- தேர்வு செய்க --":
            # இங்கே ஏற்கனவே உள்ள மதிப்பெண்களுடன் கோப்பு தரவிறக்கம் ஆகும்
            df_down = generate_df(sel_c2)
            output = BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer: 
                df_down.to_excel(writer, index=False)
            st.download_button("📥 வகுப்பு கோப்பைத் தரவிறக்கு", data=output.getvalue(), file_name=f"Marks_{sel_c2}.xlsx")
            
            up = st.file_uploader("பதிவேற்று:", type=["xlsx"], key="up2")
            if up and st.button("சேமி", key="save2"): 
                save_to_supabase(pd.read_excel(up), sel_c2)

    with tab3:
        grade = st.text_input("வகுப்பு எண் (எ.கா: 11):")
        if grade:
            relevant = sorted([c['class_name'] for c in all_classes if c['class_name'].startswith(grade)])
            output = BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                for c in relevant: 
                    # அந்தந்த வகுப்பின் தற்போதைய மதிப்பெண்களுடன் ஷீட்கள் உருவாகும்
                    generate_df(c).to_excel(writer, sheet_name=c, index=False)
            st.download_button("📥 அனைத்தையும் தரவிறக்கு", data=output.getvalue(), file_name=f"Marks_{grade}_All.xlsx")
            
            up3 = st.file_uploader("பதிவேற்று:", type=["xlsx"], key="up3")
            if up3 and st.button("சேமி", key="save3"):
                xl = pd.ExcelFile(up3)
                for sheet in xl.sheet_names: 
                    save_to_supabase(pd.read_excel(xl, sheet_name=sheet), sheet)
