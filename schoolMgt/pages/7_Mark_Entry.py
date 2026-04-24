def process_bulk_upload(target_classes):
    # 'exam_id' என்பது இந்த function-க்கு வெளியே இருப்பதால், அதை global-ஆகக் கருதவோ அல்லது argument-ஆக அனுப்பவோ வேண்டும்.
    # இங்கே argument-ஆக அனுப்புவது சிறந்தது.
    
    # தற்காலிக தரவு சேமிப்பு
    all_data = []
    
    for cls in target_classes:
        # பிழை வராமல் இருக்க class_name-ஐப் பாதுகாப்பாக எடுத்தல்
        class_name_val = cls.get('class_n') or cls.get('class_name')
        
        # மாணவர் பட்டியலை எடுத்தல்
        mapping = supabase.table("exam_mapping")\
            .select("emis_no, student_name")\
            .eq("exam_id", exam_id)\
            .eq("class_name", class_name_val)\
            .execute().data
            
        df_temp = pd.DataFrame(mapping)
        
        # பாடங்கள் வடிகட்டுதல்
        group_name = cls.get('group_name')
        g_info = next((g for g in all_groups if g['group_name'] == group_name), None)
        sub_names = g_info['subjects'].split(',') if g_info and g_info.get('subjects') else []
        
        for s_name in sub_names:
            s_name = s_name.strip()
            sub_data = next((s for s in all_subjects if s['subject_name'] == s_name), None)
            if sub_data and sub_data.get('eval_type') != 'NIL':
                df_temp[f"Theory_{s_name}"] = 0
                eval_type = str(sub_data.get('eval_type', '100'))
                if len(eval_type.split('+')) >= 2: df_temp[f"Internal_{s_name}"] = 0
                if len(eval_type.split('+')) == 3: df_temp[f"Practical_{s_name}"] = 0
        
        # ஒவ்வொரு குரூப் தரவையும் சேர்த்துக்கொள்ளுதல்
        all_data.append(df_temp)
    
    # அனைத்து குரூப்களின் தரவையும் இணைத்து ஒரே DataFrame-ஆகத் தருதல்
    return pd.concat(all_data, ignore_index=True) if all_data else pd.DataFrame()
