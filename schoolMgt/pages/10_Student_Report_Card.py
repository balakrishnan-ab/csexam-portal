import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from supabase import create_client

# --- Supabase இணைப்பு ---
def get_supabase_client():
    if "supabase_instance" not in st.session_state:
        st.session_state.supabase_instance = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
    return st.session_state.supabase_instance

supabase = get_supabase_client()

st.set_page_config(page_title="Student Report Card", layout="wide")

# ⚡ CSS ஸ்டைலிங்
st.markdown("""
    <style>
    .report-card { background-color: #ffffff; padding: 20px; border-radius: 15px; border: 1px solid #e2e8f0; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1); }
    .student-name { font-size: 24px; font-weight: bold; color: #1e293b; margin-bottom: 5px; }
    .stat-box { background-color: #f8fafc; padding: 15px; border-radius: 10px; text-align: center; border: 1px solid #cbd5e1; }
    </style>
    """, unsafe_allow_html=True)

st.title("🎓 மாணவர் தனிப்பட்ட ரிப்போர்ட் கார்டு")

# --- 1. தேடல் வசதிகள் ---
classes_data = supabase.table("classes").select("*").execute().data
all_classes = sorted(list(set([c.get('class_n') or c.get('class_name') for c in classes_data if c.get('class_n') or c.get('class_name')])))

c1, c2 = st.columns(2)
sel_class = c1.selectbox("வகுப்பைத் தேர்வு செய்க:", ["-- தேர்வு செய்க --"] + all_classes)

if sel_class != "-- தேர்வு செய்க --":
    # அந்த வகுப்பில் உள்ள மாணவர்களை எடுத்தல்
    students = supabase.table("exam_mapping").select("student_name, emis_no").eq("class_name", sel_class).execute().data
    unique_students = {s['student_name']: s['emis_no'] for s in students}
    sel_student_name = c2.selectbox("மாணவரைத் தேர்வு செய்க:", list(unique_students.keys()))
    
    if sel_student_name:
        emis_no = unique_students[sel_student_name]
        
        # மாணவரின் அனைத்து மதிப்பெண்களையும் எடுத்தல்
        marks_data = supabase.table("marks").select("*, exams(exam_name)").eq("emis_no", emis_no).execute().data
        exams_info = supabase.table("exams").select("*").execute().data
        subjects_info = supabase.table("subjects").select("*").execute().data
        sub_map = {s['subject_code']: s['subject_name'] for s in subjects_info}

        if marks_data:
            # தரவுகளை ஒழுங்குபடுத்துதல்
            df_marks = pd.DataFrame(marks_data)
            df_marks['exam_name'] = df_marks['exams'].apply(lambda x: x['exam_name'])
            df_marks['subject_name'] = df_marks['subject_id'].map(sub_map)
            
            # --- UI: மாணவர் விபரம் ---
            st.markdown(f"""
            <div class="report-card">
                <div class="student-name">👤 {sel_student_name}</div>
                <p>EMIS No: {emis_no} | வகுப்பு: {sel_class}</p>
            </div>
            """, unsafe_allow_html=True)
            
            st.divider()

            # --- 2. முன்னேற்ற வரைபடம் (Trend Analysis) ---
            st.subheader("📈 தேர்வு வாரியான முன்னேற்றம் (Total Marks Trend)")
            trend_data = df_marks.groupby('exam_name')['total_mark'].sum().reset_index()
            fig_trend = px.line(trend_data, x='exam_name', y='total_mark', markers=True, 
                                labels={'total_mark': 'மொத்த மதிப்பெண்', 'exam_name': 'தேர்வு'},
                                color_discrete_sequence=['#3b82f6'])
            st.plotly_chart(fig_trend, use_container_width=True)

            # --- 3. பலம் மற்றும் பலவீனம் (Spider/Radar Chart) ---
            # சமீபத்திய தேர்வின் மதிப்பெண்களை மட்டும் எடுத்தல்
            latest_exam = trend_data['exam_name'].iloc[-1]
            latest_marks = df_marks[df_marks['exam_name'] == latest_exam]
            
            st.subheader(f"🎯 பாடவாரியான திறன் பகுப்பாய்வு ({latest_exam})")
            
            # Spider Chart உருவாக்க
            fig_radar = go.Figure()
            fig_radar.add_trace(go.Scatterpolar(
                r=latest_marks['total_mark'],
                theta=latest_marks['subject_name'],
                fill='toself',
                name=sel_student_name,
                line_color='#10b981'
            ))
            fig_radar.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100])), showlegend=False)
            st.plotly_chart(fig_radar, use_container_width=True)
            
            

            # --- 4. விரிவான மதிப்பெண் அட்டவணை ---
            st.subheader("📋 அனைத்துத் தேர்வு மதிப்பெண் விவரங்கள்")
            pivot_df = df_marks.pivot(index='subject_name', columns='exam_name', values='total_mark').fillna('-')
            st.table(pivot_df)

        else:
            st.info("இந்த மாணவருக்குரிய தேர்வுத் தரவுகள் இன்னும் பதிவேற்றப்படவில்லை.")
