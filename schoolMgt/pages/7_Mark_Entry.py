import streamlit as st
import pandas as pd
from supabase import create_client
from io import BytesIO

def get_supabase_client():
    if "supabase_instance" not in st.session_state:
        st.session_state.supabase_instance = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
    return st.session_state.supabase_instance

supabase = get_supabase_client()

st.set_page_config(page_title="Mark Entry System", layout="wide")
st.title("📊 மதிப்பெண் பதிவேற்றம் & திருத்தம்")

# 1. தரவுகளைப் பெறுதல்
exams = supabase.table("exams").select("*").eq("exam_status", "Active").execute().data
all_classes = supabase.table("classes").select("*").execute().data
all_groups = supabase.table("groups").select("*").execute().data
all_subjects = supabase.table("subjects").select("*").execute().data

sel_exam_name = st.selectbox("தேர்வைத் தேர்ந்தெடுக்கவும்:", ["-- தேர்வு செய்க --"] + [e['exam_name'] for e in exams])

if sel_exam_name != "-- தேர்வு செய்க --":
    exam_id = next(e['id'] for e in exams if e['exam_name'] == sel_exam_name)
    
    # தரவு உள்ளதா என சரிபார்க்க
    check_mapping = supabase.table("exam_mapping").select("id").eq("exam_id", exam_id).limit(1).execute().data
    if not check_mapping:
        st.error(f"இந்தத் தேர்வுக்கு ('{sel_exam_name}') 'exam_mapping' அட்டவணையில் மாணவர்கள் ஒதுக்கப்படவில்லை!")
        st.stop()

    # --- மதிப்பெண்களை நிரப்பும் பங்க்ஷன் ---
    def generate_bulk_df(c_name):
        mapping = supabase.table("exam_mapping").select("emis_no, student_name").eq("exam_id", exam_id).eq("class_name", c_name).execute().data
        if not mapping: return None
        df = pd.DataFrame(mapping)
        
        cls_info = next((c for c in all_classes if c['class_name'] == c_name), None)
        if not cls_info: return df
        g_info = next((g for g in all_groups if g['group_name'] == cls_info.get('group_name')), None)
        if not g_info: return df
        
        sub_list = [s.strip() for s in g_info['subjects'].split(',')]
        for s in sub_list:
            sub = next((x for x in all_subjects if x['subject_name'] == s), None)
            if sub and sub.get('eval_type') != 'NIL':
                p = str(sub.get('eval_type', '100')).split('+')
                marks_db = supabase.table("marks").select("emis_no, theory_mark, internal_mark, practical_mark").eq("exam_id", exam_id).eq("subject_id", sub['subject_code']).execute().data
                m_dict = {m['emis_no']: m for m in marks_db}
                df[f"Theory_{s}"] = df['emis_no'].apply(lambda x: m_dict.get(x, {}).get('theory_mark', 0))
                if len(p) >= 2: df[f"Internal_{s}"] = df['emis_no'].apply(lambda x: m_dict.get(x, {}).get('internal_mark', 0))
                if len(p) == 3: df[f"Practical_{s}"] = df['emis_no'].apply(lambda x: m_dict.get(x, {}).get('practical_mark', 0))
        return df

    # --- Tabs ---
    tab1, tab2, tab3 = st.tabs(["👨‍🏫 பாட ஆசிரியர்", "📂 வகுப்பு ஆசிரியர்", "🏢 வகுப்பின் அனைத்துப் பிரிவுகள்"])

    with tab1:
        class_list = sorted(list(set([c['class_name'] for c in all_classes])))
        sel_class = st.selectbox("வகுப்பு:", ["-- தேர்வு செய்க --"] + class_list, key="t1")
        if sel_class != "-- தேர்வு செய்க --":
            df = generate_bulk_df(sel_class)
            if df is not None: st.dataframe(df, use_container_width=True)
            else: st.warning("இந்த வகுப்பிற்கு மாணவர்கள் ஒதுக்கப்படவில்லை.")
    # --- TAB 2: வகுப்பு ஆசிரியர் (தனி வகுப்பு - Bulk Entry) ---
    with tab2:
        st.subheader("வகுப்பு வாரியான மதிப்பெண் பதிவேற்றம்")
        
        # 1. வகுப்புகளைத் தேர்வு செய்ய ஒரு Selectbox அவசியம்
        class_list = sorted(list(set([c['class_name'] for c in all_classes])))
        sel_class_t2 = st.selectbox("வகுப்பைத் தேர்ந்தெடுக்கவும்:", ["-- தேர்வு செய்க --"] + class_list, key="t2_class")
        
        # 2. வகுப்பு தேர்வு செய்தவுடன் தரவை எடுத்தல்
        if sel_class_t2 != "-- தேர்வு செய்க --":
            df_b = generate_bulk_df(sel_class_t2) # உங்கள் ஏற்கனவே உள்ள பங்க்ஷன்
            
            if df_b is not None:
                st.write(f"வகுப்பு: {sel_class_t2} - மாணவர் பட்டியல்")
                
                # 3. தரவிறக்க பொத்தான்
                output = BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    df_b.to_excel(writer, index=False)
                
                st.download_button(
                    label="📥 வகுப்பு கோப்பைத் தரவிறக்கு", 
                    data=output.getvalue(), 
                    file_name=f"Marks_{sel_class_t2}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
                
                # 4. பதிவேற்றம்
                uploaded_file = st.file_uploader("பூர்த்தி செய்த கோப்பைப் பதிவேற்றவும்:", type=["xlsx"], key="up2")
                if uploaded_file:
                    st.success("கோப்பு பதிவேற்றப்பட்டது! (இதற்கான சேமிப்பு லாஜிக்கை கீழே சேர்க்கவும்)")
            else:
                st.warning("இந்த வகுப்பிற்குத் தரவு இல்லை.")
        else:
            st.info("தயவுசெய்து ஒரு வகுப்பைத் தேர்ந்தெடுக்கவும்.")
    with tab3:
        grade_val = st.text_input("வகுப்பு எண் (எ.கா: 11):")
        if grade_val:
            relevant = sorted([c['class_name'] for c in all_classes if c['class_name'].startswith(grade_val)])
            output = BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                for c in relevant:
                    df_c = generate_bulk_df(c)
                    if df_c is not None: df_c.to_excel(writer, sheet_name=c, index=False)
            st.download_button("📥 அனைத்துப் பிரிவுகளையும் தரவிறக்கு", data=output.getvalue(), file_name=f"Marks_{grade_val}.xlsx")
