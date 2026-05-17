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

# --- 3. X-Coordinates அடிப்படையிலான துல்லியமான PDF Parsing லாஜிக் ---
def parse_sslc_pdf(pdf_file):
    students_list = []
    
    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages:
            # பிடிஎஃப் பக்கத்தில் உள்ள சொற்களை அவற்றின் எக்ஸ்-அச்சு (X-position) புள்ளிகளோடு எடுத்தல்
            words = page.extract_words()
            if not words:
                continue
                
            # சொற்களை வரிகளாக (Y-position அடிப்படையில்) வகைப்படுத்துதல்
            lines_dict = {}
            for w in words:
                y = round(w['top'], 1)  # ஒரே வரியில் உள்ளவற்றை இணைக்க
                found = False
                for existing_y in lines_dict.keys():
                    if abs(y - existing_y) < 4:  # 4 பிக்சல் இடைவெளிக்குள் இருந்தால் ஒரே வரி
                        lines_dict[existing_y].append(w)
                        found = True
                        break
                if not found:
                    lines_dict[y] = [w]
            
            # வரிகளை மேலிருந்து கீழாக வரிசைப்படுத்துதல்
            sorted_y = sorted(lines_dict.keys())
            
            for idx, y in enumerate(sorted_y):
                # சொற்களை இடமிருந்து வலமாக வரிசைப்படுத்துதல்
                line_words = sorted(lines_dict[y], key=lambda x: x['x0'])
                line_text = " ".join([w['text'] for w in line_words]).strip()
                
                # 7 இலக்க ரோல் நம்பர் உள்ள வரியைக் கண்டறிதல்
                if re.match(r'^\d{7}\b', line_text):
                    try:
                        roll_no = line_words[0]['text']
                        tmr_no = line_words[1]['text']
                        
                        # மாணவர் பெயர் பிரித்தல்
                        name_parts = []
                        w_idx = 2
                        while w_idx < len(line_words) and not (re.match(r'^\d{2}/\d{2}/\d{4}$', line_words[w_idx]['text']) or line_words[w_idx]['text'] in ['M', 'F', 'T', 'E']):
                            name_parts.append(line_words[w_idx]['text'])
                            w_idx += 1
                        student_name = " ".join(name_parts)
                        
                        # பாலினம் அறிதல்
                        gender = "M"
                        for w in line_words[w_idx:]:
                            if w['text'] in ['M', 'F']:
                                gender = w['text']
                        
                        # X-Position (நெடுவரிசைப் புள்ளி) அடிப்படையில் மதிப்பெண்களை மட்டும் பிரித்தல்
                        lang, eng, mat, sci_theory, sci_practical, sci_total, soc_science = "000", "000", "000", "000", "000", "000", "000"
                        
                        # மதிப்பெண் மற்றும் ஒட்டுமொத்தக் குறியீடுகள் உள்ள அனைத்துச் சொற்களையும் அடுத்தடுத்த வரிகளில் இருந்தும் சேர்த்தல்
                        all_marks_words = []
                        for lookahead in range(0, 4):
                            if (idx + lookahead) < len(sorted_y):
                                current_words = sorted(lines_dict[sorted_y[idx + lookahead]], key=lambda x: x['x0'])
                                for lw in current_words:
                                    txt = lw['text'].strip()
                                    # 3 இலக்க எண்கள் அல்லது AAA/XXX/P/W குறியீடுகளை மட்டும் எடுத்தல்
                                    if re.match(r'^\d{3}$|^AAA$|^XXX$|\b[PW]\b', txt) or (txt.isdigit() and len(txt) <= 3):
                                        all_marks_words.append(lw)
                        
                        # எக்ஸ்-அச்சுப் புள்ளியின் (x0) எல்லைகளுக்குள் மதிப்பெண்களைச் சரியாக அமர்த்துதல்
                        for mw in all_marks_words:
                            x = mw['x0']
                            txt = mw['text']
                            
                            if 400 < x < 450: lang = txt          # LANGUAGE 
                            elif 450 < x < 510: eng = txt         # ENGLISH 
                            elif 510 < x < 580: mat = txt         # MATHS 
                            elif 580 < x < 625: sci_theory = txt  # SCIENCE - THE 
                            elif 625 < x < 655: sci_practical = txt # SCIENCE - PRA 
                            elif 655 < x < 695: sci_total = txt    # SCIENCE - TOT 
                            elif 695 < x < 765: soc_science = txt  # SOCIAL SCIENCE 
                        
                        # ஒட்டுமொத்த மொத்தம் மற்றும் முடிவு
                        total_mark = 0
                        result = "Fail"
                        
                        # வரிசையில் உள்ள கடைசி டோக்கன்களைக் கொண்டு மொத்தம் மற்றும் முடிவை எடுத்தல்
                        valid_tokens = [w['text'] for w in line_words if w['text'].isdigit() or w['text'] in ['P', 'W']]
                        if len(valid_tokens) >= 2:
                            for tok in reversed(valid_tokens):
                                if tok == 'P': result = "Pass"
                                elif tok.isdigit() and total_mark == 0:
                                    total_mark = int(tok)
                        
                        # இனம் (Community) கண்டறிதல்
                        community = "BC"
                        for k in range(1, 4):
                            if (idx + k) < len(sorted_y):
                                check_words = sorted(lines_dict[sorted_y[idx + k]], key=lambda x: x['x0'])
                                check_line = " ".join([cw['text'] for cw in check_words]).lower()
                                if "mbc" in check_line: community = "MBC"; break
                                elif "sc" in check_line: community = "SC"; break
                                elif "bc" in check_line: community = "BC"; break
                                elif "st" in check_line: community = "ST"; break
                                elif "dnc" in check_line: community = "DNC"; break
                        
                        students_list.append({
                            "தேர்வு எண்": roll_no, "பெயர்": student_name, "பாலினம்": gender, "இனம்": community,
                            "TAMIL": lang, "ENGLISH": eng, "MATHS": mat, 
                            "SCIENCE": f"{sci_total} ({sci_theory}+{sci_practical})", 
                            "sci_pure_total": sci_total,
                            "SOCIAL SCIENCE": soc_science,
                            "மொத்தம்": total_mark, "Result": result, "பிரிவு": "10-A"
                        })
                    except Exception as e:
                        pass
                        
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
                if sn == "SCIENCE":
                    mark_val = str(row["sci_pure_total"]).strip()
                    display_val = row["SCIENCE"]
                else:
                    mark_val = str(row[sn]).strip()
                    display_val = mark_val
                    
                subject_stats[sn]["total"][gen] += 1
                
                if mark_val in ["AAA", "XXX"] or "ABS" in mark_val or mark_val == "000":
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
                        
                    row_raw[sn] = display_val
                    
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

        # --- 9. 📋 முழுமையான மதிப்பெண் பட்டியல் (அட்டவணை) ---
        st.markdown('<div class="responsive-subtitle">📋 முழுமையான மதிப்பெண் பட்டியல்</div>', unsafe_allow_html=True)
        df_sorted = df_overall.sort_values(by=["Fails", "மொத்தம்"], ascending=[True, False]).reset_index(drop=True)
        
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
                d_row[sn] = r.get(sn)
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
        st.error("PDF கோப்பில் இருந்து தரவுகளைப் பிரித்தெடுக்க முடியவில்லை. அமைப்பைச் சரிபார்க்கவும்.")
