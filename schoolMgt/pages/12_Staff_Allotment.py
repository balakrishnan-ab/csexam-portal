with col_visual:
    st.subheader("🏫 வகுப்பு வாரியான பாடவேளைகள்")
    
    # --- 🧮 கணக்கீடு லாஜிக் ---
    class_totals = {c: 0 for c in base_classes}
    for entry in allotment_list:
        target = entry['class_name']
        periods = entry['periods_per_week']
        if target in comb_groups:
            for sub_class in comb_groups[target]:
                if sub_class in class_totals: class_totals[sub_class] += periods
        elif target in class_totals:
            class_totals[target] += periods

    # --- 🎨 காட்சியாக்கம் (Grid Layout: 4 to 6 per row) ---
    # ஒரு வரிசைக்கு எத்தனை வகுப்புகள் என்பதை இங்கே மாற்றலாம் (எ.கா: 4)
    cols_per_row = 4 
    
    # வகுப்புகளை சிறு சிறு குழுக்களாகப் பிரித்தல்
    class_list = list(class_totals.items())
    for i in range(0, len(class_list), cols_per_row):
        cols = st.columns(cols_per_row)
        for j in range(cols_per_row):
            if i + j < len(class_list):
                cls, total = class_list[i + j]
                
                # ஸ்டைலிங்
                bg_color = "#FF4B4B" if total > 45 else "#F0F2F6"
                txt_color = "white" if total > 45 else "#31333F"
                
                cols[j].markdown(f"""
                    <div style="
                        background-color: {bg_color};
                        padding: 8px;
                        border-radius: 6px;
                        border: 1px solid #ddd;
                        text-align: center;
                        margin-bottom: 8px;
                        min-height: 80px;
                        display: flex;
                        flex-direction: column;
                        justify-content: center;
                    ">
                        <div style="font-size: 14px; font-weight: bold; color: {txt_color};">{cls}</div>
                        <div style="font-size: 20px; font-weight: 800; color: {txt_color};">{total}</div>
                    </div>
                """, unsafe_allow_html=True)
