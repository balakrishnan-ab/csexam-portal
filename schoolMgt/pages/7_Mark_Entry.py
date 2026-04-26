import streamlit as st
import pandas as pd
from supabase import create_client
from io import BytesIO

# --- Supabase இணைப்பு ---
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

    # --- தரவை எக்செல் வடிவில் தயார் செய்யும் பங்க்ஷன் ---
    def generate_df(c_name, sub_filter=None):
        mapping = supabase.table("exam_mapping").select("emis_no, student_name").eq("exam_id", exam_id).eq("class_name", c_name).execute().data
        df = pd.DataFrame(mapping)
        cls_info = next((c for c in all_classes if c['class_name'] == c_name), None)
        g_info = next((g for g in all_groups if g['group_name'] == cls_info.get('group_name')), None)
        sub_list = [sub_filter] if sub_filter else [s.strip() for s in g_info['subjects'].split(',')]

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

    # --- Supabase-ல் சேமிக்கும் பங்க்ஷன் ---
    def save_to_supabase(df_uploaded):
        final_data = []
        # எக்செல் கோப்பில் உள்ள அனைத்து நெடுவரிசைகளையும் ஆய்வு செய்தல்
        for _, row in df_uploaded.iterrows():
            for col in df_uploaded.columns:
                if col.startswith(("Theory_", "Internal_", "Practical_")):
                    # பாடத்தின் பெயரை எடுத்தல் (எ.கா: Theory_Tamil -> Tamil)
                    parts = col.split('_', 1)
                    s_name = parts[1]
                    mark_type = parts[0]
                    
                    sub = next((s for s in all_subjects if s['subject_name'] == s_name), None)
                    if not sub: continue
                    
                    # மதிப்பெண் மதிப்பு
                    val = row[col]
                    
                    # ஒவ்வொரு பாடத்திற்கும் ஒரு தனி பதிவு
                    # (இந்த பதிவு அந்த குறிப்பிட்ட பாடம் மற்றும் அந்த குறிப்பிட்ட மாணவருக்கு மட்டுமே)
                    final_data.append({
                        "exam_id": exam_id,
                        "emis_no": row['emis_no'],
                        "subject_id": sub['subject_code'],
                        "theory_mark": val if mark_type == "Theory" else 0,
                        "internal_mark": val if mark_type == "Internal" else 0,
                        "practical_mark": val if mark_type == "Practical" else 0
                    })
        
        # Supabase-ல் பதிவேற்றுதல்
        # இது அந்த குறிப்பிட்ட பாடத்திற்குரிய மதிப்பெண்களை மட்டுமே அந்த மாணவருக்கு மாற்றும்.
        # மற்ற பாட மதிப்பெண்களை இது தொடாது.
        if final_data:
            supabase.table("marks").upsert(final_data, on_conflict="exam_id, emis_no, subject_id").execute()
            st.success("மதிப்பெண்கள் வெற்றிகரமாகச் சேமிக்கப்பட்டன!")

    # --- Tabs ---
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
                df = generate_df(sel_c, sel_s)
                edited_df = st.data_editor(df, use_container_width=True)
                if st.button("சேமி", key="save1"): save_to_supabase(edited_df)

    with tab2:
        sel_c2 = st.selectbox("வகுப்பு:", ["-- தேர்வு செய்க --"] + class_list, key="t2_c")
        if sel_c2 != "-- தேர்வு செய்க --":
            df = generate_df(sel_c2)
            output = BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer: df.to_excel(writer, index=False)
            st.download_button("📥 வகுப்பு கோப்பைத் தரவிறக்கு", data=output.getvalue(), file_name=f"Marks_{sel_c2}.xlsx")
            up = st.file_uploader("பதிவேற்று:", type=["xlsx"], key="up2")
            if up and st.button("சேமி", key="save2"): save_to_supabase(pd.read_excel(up))

    with tab3:
        grade = st.text_input("வகுப்பு எண் (எ.கா: 11):")
        if grade:
            relevant = sorted([c['class_name'] for c in all_classes if c['class_name'].startswith(grade)])
            output = BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                for c in relevant: generate_df(c).to_excel(writer, sheet_name=c, index=False)
            st.download_button("📥 அனைத்தையும் தரவிறக்கு", data=output.getvalue(), file_name=f"Marks_{grade}_All.xlsx")
            up3 = st.file_uploader("பதிவேற்று:", type=["xlsx"], key="up3")
            if up3 and st.button("சேமி", key="save3"):
                xl = pd.ExcelFile(up3)
                for sheet in xl.sheet_names: save_to_supabase(pd.read_excel(xl, sheet_name=sheet))
