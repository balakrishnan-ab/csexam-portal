import streamlit as st
import pandas as pd
from supabase import create_client

# --- Supabase இணைப்பு ---
def get_supabase_client():
    if "supabase_instance" not in st.session_state:
        st.session_state.supabase_instance = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
    return st.session_state.supabase_instance

supabase = get_supabase_client()

st.set_page_config(page_title="Evaluation Type Based Analysis", layout="wide")

# ⚡ CSS - ஸ்டைலிங்
st.markdown("""
    <style>
    .stDataFrame td { font-weight: bold !important; font-size: 14px !important; white-space: pre !important; }
    .main-stat { background-color: #f8fafc; border: 1px solid #e2e8f0; padding: 10px; border-radius: 10px; text-align: center; min-height: 100px; }
    .stat-val { font-size: 20px; font-weight: bold; color: #1e293b; line-height: 1.2; }
    .stat-label { font-size: 13px; color: #64748b; font-weight: bold; margin-bottom: 5px; }
    .gender-sub { font-size: 12px; color: #3b82f6; font-weight: bold; display: block; margin-top: 3px; }
    .info-card { padding: 8px; border-radius: 5px; margin-bottom: 5px; border-left: 4px solid #10b981; background-color: #f0fdf4; font-size: 14px; }
    </style>
    """, unsafe_allow_html=True)

st.title("📊 வகுப்பு வாரி விரிவான தேர்ச்சிப் பகுப்பாய்வு")

# --- 1. தரவுகள் பெறுதல் ---
exams_data = supabase.table("exams").select("*").execute().data
classes_data = supabase.table("classes").select("*").execute().data
groups_data = supabase.table("groups").select("*").execute().data
subjects_data = supabase.table("subjects").select("*").execute().data

c1, c2 = st.columns(2)
sel_exam_name = c1.selectbox("1. தேர்வு:", [e['exam_name'] for e in exams_data])
all_classes_raw = [c.get('class_n') or c.get('class_name') for c in classes_data]
base_classes = sorted(list(set([str(c).split('-')[0].strip() for c in all_classes_raw if c])), key=lambda x: int(x) if x.isdigit() else x)
sel_base_class = c2.selectbox("2. வகுப்பு:", ["-- தேர்வு செய்க --"] + base_classes)

if sel_exam_name and sel_base_class != "-- தேர்வு செய்க --":
    exam_id = next(e['id'] for e in exams_data if e['exam_name'] == sel_exam_name)
    st.divider()
    split_gender = st.toggle("🔍 ஆண் பெண் பிரித்து (Female + Male = Total)", value=True)

    matching_sections = sorted([c for c in all_classes_raw if str(c).startswith(sel_base_class)])
    all_students, union_subs = [], []
    
    for section in matching_sections:
        c_info = next((c for c in classes_data if (c.get('class_n') == section or c.get('class_name') == section)), None)
        if c_info:
            g_info = next((g for g in groups_data if g['group_name'] == c_info.get('group_name')), None)
            if g_info and g_info.get('subjects'):
                g_list = [s.strip() for s in g_info['subjects'].split(',')]
                studs = supabase.table("exam_mapping").select("exam_no, student_name, emis_no, gender").eq("exam_id", exam_id).eq("class_name", section).execute().data
                if studs:
                    for s in studs:
                        s['section'] = section; s['my_subjects'] = g_list
                        all_students.append(s)
                for gs in g_list:
                    if gs not in union_subs: union_subs.append(gs)

    marks_data = supabase.table("marks").select("*").eq("exam_id", exam_id).execute().data
    sub_info_map = {s['subject_name']: s for s in subjects_data}

    if all_students:
        report_rows, centum_list, absent_list = [], [], []
        st_count = {"total": {"A": 0, "M": 0, "F": 0}, "present": {"A": 0, "M": 0, "F": 0}, "pass": {"A": 0, "M": 0, "F": 0}}
        all_marks_list = {"A": [], "M": [], "F": []}
        fail_cats = {1: [], 2: [], 3: [], 4: [], 5: [], "All": []}
        
        # பாடவாரி தரவுகளை சேமிக்க (Subject Analysis Storage)
        subject_stats = {sn: {"app": 0, "pass": 0, "fail": 0, "marks": [], "only_this": 0} for sn in union_subs}

        for s in all_students:
            raw_gen = str(s.get('gender', 'Male')).strip().upper()
            gen = 'F' if raw_gen.startswith('F') else 'M'
            st_count["total"]["A"] += 1; st_count["total"][gen] += 1
            
            row_raw = {"பிரிவு": s['section'], "பெயர்": s['student_name'], "gender": gen}
            total_m, fails, wrote_any, fail_subs = 0, 0, False, []
            my_subs = s['my_subjects']

            for sn in union_subs:
                if sn not in my_subs:
                    row_raw[sn] = "-"; continue
                
                s_obj = sub_info_map.get(sn)
                if not s_obj: continue
                
                m = next((m for m in marks_data if m['emis_no'] == s['emis_no'] and m['subject_id'] == s_obj['subject_code']), None)
                if m and not m.get('is_absent'):
                    wrote_any = True
                    tot, th, pr = m.
