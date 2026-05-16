import streamlit as st
import pdfplumber
import pandas as pd
import re
from io import BytesIO
from utils import add_school_header 

# --- 1. பக்க அமைப்பு மற்றும் ஹெட்டர் ---
st.set_page_config(page_title="PDF TML Overall Analysis", layout="wide")
add_school_header()

# --- 2. CSS ஸ்டைலிங் (Dashboard UI) ---
st.markdown("""
    <style>
    .stDataFrame td { font-weight: bold !important; font-size: 13px !important; white-space: pre !important; }
    .metric-container { display: flex; flex-wrap: wrap; gap: 10px; justify-content: space-between; width: 100%; margin-bottom: 20px; }
    .metric-card { background-color: #f8fafc; border: 1px solid #e2e8f0; padding: 12px 8px; border-radius: 10px; text-align: center; flex: 1 1 calc(15% - 10px); min-width: 110px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    .stat-val { font-size: 22px; font-weight: bold; color: #1e293b; line-height: 1.2; }
    .stat-label { font-size: 11px; color: #64748b; font-weight: bold; text-transform: uppercase; }
    .gender-sub { font-size: 10px; color: #3b82f6; font-weight: bold; display: block; margin-top: 2px; }
    .responsive-subtitle { font-size: 20px; font-weight: bold; color: #334155; border-bottom: 2px solid #e2e8f0; margin: 15px 0 10px 0; }
    .info-card { padding: 10px; border-radius: 6px; margin-bottom: 8px; border-left: 4px solid #10b981; background-color: #f0fdf4; font-size: 14px; font-weight: bold; }
    .topper-card { padding: 8px; border-radius: 5px; margin-bottom: 5px; background-color: #fffbeb; border-left: 4px solid #f59e0b; font-size: 13px; }
    .community-topper { background-color: #f0f9ff; border-left-color: #0ea5e9; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. துல்லியமான பிடிஎஃப் (PDF Parsing) லாஜிக் ---
def parse_sslc_pdf(pdf_file):
    students_list = []
    
    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if not text:
                continue
                
            lines = text.split('\n')
            i = 0
            while i < len(lines):
                line = lines[i].strip()
                
                # 7 இலக்க ரோல் நம்பர் கொண்டு ஆரம்பிக்கும் வரிகளை மட்டும் கண்டறிதல்
                if re.match(r'^["\']?\d{7}\b', line):
                    try:
                        # மேற்கோள் குறிகள், கமாக்களைச் சுத்தம் செய்தல்
                        clean_line = line.replace('"', '').replace("'", '').replace(',,', ',').replace(',', ' ')
                        tokens = clean_line.split()
                        
                        roll_no = tokens[0]
                        tmr_no = tokens[1]
                        
                        # ஆங்கிலப் பெயரைப் பிரித்தெடுத்தல்
                        name_parts = []
                        idx = 2
                        while idx < len(tokens) and not (re.match(r'^\d{2}/\d{2}/\d{4}$', tokens[idx]) or tokens[idx] in ['M', 'F', 'T', 'E']):
                            name_parts.append(tokens[idx])
                            idx += 1
                        student_name = " ".join(name_parts)
                        
                        # பாலினம் மற்றும் பிறந்த தேதி விவரம்
                        dob, gender = "-", "M"
                        for t in tokens[idx:]:
                            if re.match(r'^\d{2}/\d{2}/\d{4}$', t):
                                dob = t
                            elif t in ['M', 'F']:
                                gender = t
                        
                        # மதிப்பெண்கள் மற்றும் ஒட்டுமொத்த விவரங்கள் (AAA, XXX அல்லது 3 இலக்க எண்கள்)
                        mark_tokens = [t for t in tokens if re.match(r'^\d{3}$|^AAA$|^XXX$', t)]
                        
                        # SSLC பொதுத்தேர்வு முறைப்படி மதிப்பெண்களின் வரிசை
                        if len(mark_tokens) >= 5:
                            lang = mark_tokens[0]
                            eng = mark_tokens[1]
                            mat = mark_tokens[2]
                            sci = mark_tokens[3]  # தியரி + ப்ராக்டிகல் கூட்டு மார்க்
                            soc = mark_tokens[4]
                        else:
                            i += 1
                            continue
                            
                        # மொத்தம் மற்றும் பாஸ்/பெயில் குறியீடு (P / W)
                        total_mark = int(tokens[-2]) if tokens[-2].isdigit() else 0
                        res_char = tokens[-1]
                        result = "Pass" if res_char == "P" else "Fail"
                        
                        # அடுத்த வரியில் இருந்து கம்யூனிட்டி (இனம்) கண்டறிதல்
                        community = "BC"  # Default fallback
                        if i + i < len(lines):
                            next_line = lines[i+1].lower()
                            if "mbc" in next_line: community = "MBC"
                            elif "sc" in next_line: community = "SC"
                            elif "st" in next_line: community = "ST"
                            elif "bc" in next_line: community = "BC"
                            elif "dnc" in next_line: community = "DNC"
                        
                        students_list.append({
                            "தேர்வு எண்": roll_no, "பெயர்": student_name, "பாலினம்": gender, "இனம்": community,
                            "TAMIL": lang, "ENGLISH": eng, "MATHS": mat, "SCIENCE": sci, "SOCIAL SCIENCE": soc,
                            "மொத்தம்": total_mark, "Result": result, "பிரிவு": "10-A"
                        })
                    except Exception as e:
                        pass
                i += 1
                
    return pd.DataFrame(students_list)

# --- 4. முதன்மைப் பக்கம் மற்றும் கோப்புப் பதிவேற்றம் ---
st.markdown('<div class="responsive-subtitle">📅 PDF Tabulated Mark List (TML) பகுப்பாய்வு</div>', unsafe_allow_html=True)
uploaded_file = st.file_uploader("பள்ளி வாரியான SSLC TML PDF கோப்பைப் பதிவேற்றவும்:", type=["pdf"])

if uploaded_file:
    df_base = parse_sslc_pdf(uploaded_file)
    
    if not df_base.empty:
        split_gender = st.toggle("🔍 ஆண் பெண் பிரித்து காட்டு", value=True)
        st.divider()
        
        g_list = ["TAMIL", "ENGLISH", "MATHS", "SCIENCE", "SOCIAL SCIENCE"]
        
        # புள்ளிவிவரக் கணக்கீட்டுப் பெட்டகங்கள்
        st_count = {
            "total": {"A": len(df_base), "M": len(df_base[df_base['பாலினம்']=='M']), "F": len(df_base[df_base['பாலினம்']=='F'])},
            "present": {"A": 0, "M": 0, "F": 0},
            "pass": {"A": 0, "M": 0, "F": 0},
            "fail": {"A": 0, "M": 0, "F": 0}
        }
        
        report_rows, centum_list, absent_list = [], [], []
        fail_cats = {1: [], 2: [], 3: [], 4: [], 5: [], "All": []}
        subject_stats = {sn: {"total": {"M":0,"F":0}, "app": {"M":0,"F":0}, "pass": {"M":0,"F":0}, "fail": {"M":0,"F":0}, "marks": [], "student_marks": []} for sn in g_list}
        
        for _, row in df_base.iterrows():
            gen = row['பாலினம்']
            roll = row['தேர்வு எண்']
            name = row['பெயர்']
            sec = row['பிரிவு']
            comm = row['இனம்']
            
            wrote_any = False
            fails = 0
            fail_subs = []
            student_centums = []
            
            row_raw = {"Rank": "-", "தேர்வு எண்": roll, "பெயர்": name, "பிரிவு": sec, "gender": gen, "இனம்": comm}
            
            for sn in g_list:
                mark_val = str(row[sn]).strip()
                subject_stats[sn]["total"][gen] += 1
                
                if mark_val in ["AAA", "XXX"]:
                    row_raw[sn] = "ABS"
                    fails += 1
                    fail_subs.append(sn)
                    subject_stats[sn]["app"][gen] += 1
                    subject_stats[sn]["fail"][gen] += 1
                else:
                    wrote_any = True
                    mark_int = int(mark_val) if mark_val.isdigit() else 0
                    is_subj_pass = mark_int >= 35
                    
                    subject_stats[sn]["app"][gen] += 1
                    subject_stats[sn]["marks"].append(mark_int)
                    subject_stats[sn]["student_marks"].append({"name": name, "sec": sec, "mark": mark_int, "exam_no": roll})
                    
                    if is_subj_pass:
                        subject_stats[sn]["pass"][gen] += 1
                        if mark_int == 100:
                            student_centums.append(sn)
                    else:
                        subject_stats[sn]["fail"][gen] += 1
                        fails += 1
                        fail_subs.append(sn)
                        
                    row_raw[sn] = {"tot": mark_int, "tag": "", "pass": is_subj_pass}
                    
            if wrote_any:
                st_count["present"]["A"] += 1; st_count["present"][gen] += 1
                if fails == 0:
                    st_count["pass"]["A"] += 1; st_count["pass"][gen] += 1
                else:
                    st_count["fail"]["A"] += 1; st_count["fail"][gen] += 1
                    txt = f"{name} ({sec}) - ({', '.join(fail_subs)})"
                    if fails >= len(g_list): fail_cats["All"].append(txt)
                    elif fails in [1,2,3,4,5]: fail_cats[fails].append(txt)
                if student_centums:
                    centum_list.append(f"🥇 {name} ({sec}) - {', '.join(student_centums)}")
            else:
                absent_list.append(f"❌ {name} ({sec})")
                
            row_raw.update({"மொத்தம்": row['மொத்தம்'], "Fails": fails, "தோல்வி விவரம்": f"({', '.join(fail_subs)})" if fail_subs else ""})
            report_rows.append(row_raw)
            
        # --- 5. ஒட்டுமொத்தப் புள்ளிவிவரக் கட்டங்கள் (Metrics Dashboard) ---
        st.markdown('<div class="responsive-subtitle">📊 ஒட்டுமொத்தப் புள்ளிவிவரம்</div>', unsafe_allow_html=True)
        def get_gt(k): return f"<span class='gender-sub'>({st_count[k]['F']}F|{st_count[k]['M']}M)</span>" if split_gender else ""
        avg_v = round(sum([r['மொத்தம்'] for r in report_rows if r['மொத்தம்'] > 0])/st_count['present']['A'], 1) if st_count['present']['A'] > 0 else 0

        st.markdown(f"""
            <div class="metric-container">
                <div class="metric-card"><div class="stat-label">Total</div><div class="stat-val">{st_count['total']['A']}{get_gt('total')}</div></div>
                <div class="metric-card"><div class="stat-label">Present</div><div class="stat-val">{st_count['present']['A']}{get_gt('present')}</div></div>
                <div class="metric-card"><div class="stat-label">Pass</div><div class="stat-val" style="color:green">{st_count['pass']['A']}{get_gt('pass')}</div></div>
                <div class="metric-card"><div class="stat-label">Fail</div><div class="stat-val" style="color:red">{st_count['fail']['A']}{get_gt('fail')}</div></div>
                <div class="metric-card"><div class="stat-label">Pass %</div><div class="stat-val" style="color:green">{round((st_count['pass']['A']/st_count['present']['A'])*100,1) if st_count['present']['A']>0 else 0}%</div></div>
                <div class="metric-card"><div class="stat-label">Avg</div><div class="stat-val" style="color:blue">{avg_v}</div></div>
            </div>
        """, unsafe_allow_html=True)

        st.divider()
        c_e1, c_e2 = st.columns(2)
        with c_e1:
            with st.expander(f"🏆 100/100 பெற்றவர்கள்: {len(centum_list)} பேர்"):
                if centum_list:
                    for itm in centum_list: st.markdown(f'<div class="info-card">{itm}</div>', unsafe_allow_html=True)
                else: st.write("யாரும் இல்லை.")
        with c_e2:
            with st.expander(f"🚶 தேர்வு எழுதாதவர்கள்: {len(absent_list)} பேர்"):
                if absent_list:
                    for itm in absent_list: st.markdown(f'<div class="info-card" style="border-left-color:red; background-color:#fff5f5;">{itm}</div>', unsafe_allow_html=True)
                else: st.write("யாரும் இல்லை.")

        # --- 6. 📈 பாடவாரி விரிவான பகுப்பாய்வு ---
        st.markdown('<div class="responsive-subtitle">📈 பாடவாரி விரிவான பகுப்பாய்வு</div>', unsafe_allow_html=True)
        sub_df_list = []
        for sn in g_list:
            stt = subject_stats[sn]
            if not (stt['app']['F'] + stt['app']['M']) > 0: continue
            avg_s = round(sum(stt["marks"])/len(stt["marks"]),1) if stt["marks"] else 0
            sub_df_list.append({
                "Subject": sn, "Total": f"{stt['total']['F']+stt['total']['M']} ({stt['total']['F']}F|{stt['total']['M']}M)", 
                "App": f"{stt['app']['F']+stt['app']['M']} ({stt['app']['F']}F|{stt['app']['M']}M)",
                "Pass": f"{stt['pass']['F']+stt['pass']['M']} ({stt['pass']['F']}F|{stt['pass']['M']}M)", 
                "Fail": f"{stt['fail']['F']+stt['fail']['M']} ({stt['fail']['F']}F|{stt['fail']['M']}M)",
                "Pass%": f"{round((stt['pass']['F']+stt['pass']['M'])/(stt['app']['F']+stt['app']['M'])*100,1)}%",
                "Min": min(stt["marks"]) if stt["marks"] else 0, "Max": max(stt["marks"]) if stt["marks"] else 0, "Avg": avg_s
            })
        st.table(pd.DataFrame(sub_df_list))

        # --- 7. 🏅 பாடவாரி முதல் 3 இடங்கள் ---
        with st.expander("🏅 பாடவாரியாக முதல் மூன்று இடங்கள் மற்றும் கடைசி இடம்"):
            t_col1, t_col2 = st.columns(2)
            for i, sn in enumerate(g_list):
                target_col = t_col1 if i % 2 == 0 else t_col2
                with target_col:
                    st.write(f"**{sn}**")
                    sorted_m = sorted(subject_stats[sn]["student_marks"], key=lambda x: x['mark'], reverse=True)
                    if sorted_m:
                        top3 = sorted_m[:3]
                        for rank, sm in enumerate(top3, 1):
                            st.markdown(f"<div class='topper-card'>#{rank} - {sm['name']} - {sm['sec']} (No: {sm['exam_no']}) -> <b>{sm['mark']}</b></div>", unsafe_allow_html=True)
                        last = sorted_m[-1]
                        st.markdown(f"<div class='topper-card' style='border-left-color:red; background-color:#fff5f5;'>🔻 கடைசி: {last['name']} - {last['sec']} ({last['mark']})</div>", unsafe_allow_html=True)

        # --- 8. 🏢 இனம் வாரியாக முதல் மூன்று இடங்கள் (Community Toppers) ---
        st.markdown('<div class="responsive-subtitle">🏢 இனம் வாரியாக முதல் மூன்று இடங்கள் (Community-wise Toppers)</div>', unsafe_allow_html=True)
        df_overall = pd.DataFrame(report_rows)
        with st.expander("🔍 இனம் வாரியான விவரங்களைக் காண இங்கே கிளிக் செய்யவும்"):
            all_communities = sorted(df_overall['இனம்'].unique())
            c_top_1, c_top_2 = st.columns(2)
            for i, comm_name in enumerate(all_communities):
                t_col = c_top_1 if i % 2 == 0 else c_top_2
                with t_col:
                    st.write(f"🔷 **{comm_name}**")
                    comm_df = df_overall[df_overall['இனம்'] == comm_name].sort_values(by="மொத்தம்", ascending=False)
                    if not comm_df.empty:
                        for rank, (_, r_data) in enumerate(comm_df.head(3).iterrows(), 1):
                            st.markdown(f"<div class='topper-card community-topper'>#{rank} - {r_data['பெயர்']} - {r_data['பிரிவு']} (No: {r_data['தேர்வு எண்']}) -> <b>{r_data['மொத்தம்']}</b></div>", unsafe_allow_html=True)

        # --- 9. 📋 முழுமையான மதிப்பெண் பட்டியல் ---
        st.markdown('<div class="responsive-subtitle">📋 முழுமையான மதிப்பெண் பட்டியல்</div>', unsafe_allow_html=True)
        df_sorted = df_overall.sort_values(by=["Fails", "மொத்தம்"], ascending=[True, False]).reset_index(drop=True)
        
        # தானியங்கி ரேங்க் (தோல்வி இல்லாதவர்களுக்கு மட்டும்)
        df_sorted["Rank"] = "-"
        df_sorted["Rank"] = df_sorted["Rank"].astype(object)
        rv = 1
        for idx, row in df_sorted.iterrows():
            if int(row["Fails"]) == 0: 
                df_sorted.at[idx, "Rank"] = rv; rv += 1
        
        final_disp = []
        for _, r in df_sorted.iterrows():
            d_row = {"Rank": r["Rank"], "தேர்வு எண்": r["தேர்வு எண்"], "பெயர்": r['பெயர்'], "பிரிவு": r['பிரிவு'], "இனம்": r['இனம்'], "மொத்தம்": r['மொத்தம்'], "Fails": r['Fails'], "தோல்வி விவரம்": r['தோல்வி விவரம்']}
            for sn in g_list:
                v = r.get(sn)
                if isinstance(v, dict): d_row[sn] = v['tot']
                else: d_row[sn] = v
            final_disp.append(d_row)

        st.dataframe(pd.DataFrame(final_disp).style.map(lambda v: 'color: red' if 'ABS' in str(v) or (isinstance(v, (int,float)) and 0<v<35) else ''), use_container_width=True, hide_index=True)

        # --- 10. 📉 தோல்வி விவரங்கள் வகைப்படுத்துதல் ---
        st.markdown('<div class="responsive-subtitle">📉 தோல்வி அடைந்த மாணவர்களின் விவரம்</div>', unsafe_allow_html=True)
        f_c1, f_c2 = st.columns(2)
        with f_c1:
            for n in [1, 2, 3]:
                if fail_cats[n]:
                    with st.expander(f"❌ {n} பாடத்தில் தோல்வி: {len(fail_cats[n])} பேர்"):
                        for itm in fail_cats[n]: st.write(f"⚠️ {itm}")
        with f_c2:
            for n in [4, 5, "All"]:
                if fail_cats[n]:
                    lbl = f"{n} பாடத்தில் தோல்வி" if n!='All' else 'அனைத்து'
                    with st.expander(f"🔴 {lbl} பாடத்தில் தோல்வி: {len(fail_cats[n])} பேர்"):
                        for itm in fail_cats[n]: st.write(f"🚩 {itm}")
    else:
        st.error("PDF கோப்பில் இருந்து தரவுகளைப் பிரித்தெடுக்க முடியவில்லை. குறியீட்டின் Regex-ஐச் சரிபார்க்கவும்.")
