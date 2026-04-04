import streamlit as st
import pandas as pd
from supabase import create_client

# --- Supabase இணைப்பு ---
def get_supabase_client():
    if "supabase_instance" not in st.session_state:
        st.session_state.supabase_instance = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
    return st.session_state.supabase_instance

supabase = get_supabase_client()

st.set_page_config(page_title="Class Report", layout="wide")

st.title("📂 வகுப்பு வாரியான விரிவான மதிப்பெண் அறிக்கை")

# --- 1. தரவுகள் பெறுதல் ---
exams = supabase.table("exams").select("*").execute().data
all_classes = supabase.table("classes").select("*").execute().data
all_groups = supabase.table("groups").select("*").execute().data
all_subjects = supabase.table("subjects").select("*").execute().data

# --- 2. வடிகட்டிகள் ---
c1, c2 = st.columns(2)
sel_exam_name = c1.selectbox("1. தேர்வு:", [e['exam_name'] for e in exams])
class_list = sorted(list(set([c.get('class_n') or c.get('class_name') for c in all_classes])))
sel_class = c2.selectbox("2. வகுப்பு:", ["-- தேர்வு செய்க --"] + class_list)

if sel_exam_name and sel_class != "-- தேர்வு செய்க --":
    exam_id = next(e['id'] for e in exams if e['exam_name'] == sel_exam_name)
    
    # ⚡ அந்த வகுப்பிற்குரிய பாடங்களை மட்டும் கண்டறிதல்
    class_info = next((c for c in all_classes if (c.get('class_n') == sel_class or c.get('class_name') == sel_class)), None)
    relevant_subjects = []
    
    if class_info:
        group_info = next((g for g in all_groups if g['group_name'] == class_info.get('group_name')), None)
        if group_info and group_info.get('subjects'):
            group_subs = [s.strip() for s in group_info['subjects'].split(',')]
            relevant_subjects = [s for s in all_subjects if s['subject_name'] in group_subs]

    # மாணவர்கள் மற்றும் மதிப்பெண்கள் தரவு
    students = supabase.table("exam_mapping").select("exam_no, student_name, emis_no").eq("exam_id", exam_id).eq("class_name", sel_class).order("exam_no").execute().data
    marks_data = supabase.table("marks").select("*").eq("exam_id", exam_id).execute().data

    if not relevant_subjects:
        st.warning("⚠️ இந்த வகுப்பிற்குப் பாடங்கள் எதுவும் இணைக்கப்படவில்லை.")
    elif not students:
        st.info("ℹ️ இந்த வகுப்பில் மாணவர்கள் யாரும் இல்லை.")
    else:
        # ⚡ 3. விரிவான அறிக்கை தயாரித்தல்
        show_detailed = st.toggle("🔍 அகமதிப்பீடு & செய்முறை விவரங்களுடன் காட்டு (Detailed View)")

        report_data = []
        for s in students:
            row = {"தேர்வு எண்": s['exam_no'], "மாணவர் பெயர்": s['student_name']}
            total_all = 0
            
            for sub in relevant_subjects:
                s_name = sub['subject_name']
                s_code = sub['subject_code']
                m = next((m for m in marks_data if m['emis_no'] == s['emis_no'] and m['subject_id'] == s_code), None)
                
                if m:
                    if m.get('is_absent'):
                        val = "ABS"
                    else:
                        t = m.get('theory_mark', 0)
                        p = m.get('practical_mark', 0)
                        i = m.get('internal_mark', 0)
                        tot = m.get('total_mark', 0)
                        total_all += tot
                        # விரிவான பார்வை எனில் பிரிக்கவும்
                        val = f"T:{t} | P:{p} | I:{i} | Σ:{tot}" if show_detailed else tot
                else:
                    val = "-"
                
                row[s_name] = val
            
            row["மொத்தம்"] = total_all
            report_data.append(row)

        df = pd.DataFrame(report_data)
        
        # ரேங்க் வரிசைப்படுத்துதல்
        df = df.sort_values(by="மொத்தம்", ascending=False).reset_index(drop=True)
        df.index += 1
        df.index.name = "Rank"

        st.divider()
        st.subheader(f"📊 {sel_class} - {sel_exam_name} பட்டியல்")
        st.dataframe(df, use_container_width=True)

        # எக்செல் டவுன்லோட்
        csv = df.to_csv(index=True).encode('utf-8-sig')
        st.download_button("📥 தரவிறக்கம் (Excel)", data=csv, file_name=f"{sel_class}_Report.csv", mime="text/csv")
