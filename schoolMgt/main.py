import streamlit as st

# ஏற்கனவே உள்ள அமைப்புகள்
if "BASE_URL" not in st.session_state:
    st.session_state.BASE_URL = "https://script.google.com/macros/s/AKfycbxcCywCOjo9On8r3xpfyswIzkeroo6PGApMyjEaChLfsVEMwHQNfyBEXs2sqrd51zEN5w/exec"
    
st.set_page_config(page_title="GHSS Portal", layout="wide")
st.logo("school_logo.jpg")
st.sidebar.markdown("# **GHSS - தேவனங்குறிச்சி**")
# பக்கங்களை வகைப்படுத்துதல்
timetable_pages = [
    st.Page("pages/12_Staff_Allotment.py", title="Staff Allotments"),
    st.Page("pages/13_Combined_Groups.py", title="Combined Calss Creation"),
    st.Page("pages/14_Weekly_Time_Table.py", title="Weekly Time Table"),
    st.Page("pages/11_Staff Management.py", title="Staff Management"),
    st.Page("pages/15_Timetable_Report.py", title="Timetable Report"),
]

marks_pages = [
    st.Page("pages/5_Exam_Creation.py", title="Exam Creation"),
    st.Page("pages/6_Roll_No_Generator.py", title="Roll No Genetator"),
    st.Page("pages/7_Mark_Entry.py", title="Mark Entry"),
    st.Page("pages/8_ClassSecwise_Report.py", title="Class Section wise Report"),
    st.Page("pages/9_Classwise_Report.py", title="Classwise Report"),
    st.Page("pages/10_Student_Report_Card.py", title="Report Card"),
]

general_pages = [
    st.Page("pages/1_Subjects.py", title="Subjects"),
    st.Page("pages/2_Groups.py", title="Groups"),
    st.Page("pages/3_Classes.py", title="Classes"),
    st.Page("pages/11_1_Teacher Entry.py", title="Teacher Deatils"),
    st.Page("pages/4_Students.py", title="Students Entry"),
]
  

# நேவிகேஷன் மெனுவை உருவாக்குதல்
pg = st.navigation({
    "நிர்வாகம் (General)": general_pages,
    "கால அட்டவணை (Time Table)": timetable_pages,
    "தேர்வு மதிப்பெண் விவரங்கள் (Marks)": marks_pages,
})

pg.run()
