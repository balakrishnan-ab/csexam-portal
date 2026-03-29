# --- 1. முந்தைய முயற்சிகளைச் சரிபார்க்கும் தர்க்கம் ---
def get_attempt_count(student_name, subject_code):
    API_URL = f"https://sheetdb.io/api/v1/w7ktpqhwxaiy9/search?Name={student_name}&Subject={subject_code}"
    try:
        response = requests.get(API_URL, timeout=5)
        if response.status_code == 200:
            past_data = response.json()
            return len(past_data) + 1  # ஏற்கனவே உள்ள எண்ணிக்கையுடன் 1-ஐக் கூட்டவும்
        return 1
    except:
        return 1

# --- 2. மேம்படுத்தப்பட்ட மதிப்பெண் சேமிப்பு ---
def save_score(name, std, subject, correct, total, attempted, attempt_no):
    API_URL = "https://sheetdb.io/api/v1/w7ktpqhwxaiy9" 
    
    # உங்கள் புதிய தலைப்புகளுக்கு (Name, Attempt_No) ஏற்ப மாற்றப்பட்டது
    payload = {
        "data": [
            {
                "Name": str(name),                # 'N' பெரிய எழுத்து
                "Standard": str(std),
                "Datetime": datetime.now().strftime("%d-%m-%Y %H:%M"),
                "Subject": str(subject),
                "Total qus": str(total),
                "Attan": str(attempted),
                "Correct": str(correct),
                "Wrong": str(attempted - correct),
                "Score": f"{(correct/total)*100:.1f}%",
                "Attempt_No": str(attempt_no)      # மறுமுயற்சி அடையாளம்
            }
        ]
    }
    try:
        response = requests.post(API_URL, json=payload, timeout=10)
        return response.status_code in [200, 201]
    except:
        return False

# --- லாகின் பொத்தானில் செய்ய வேண்டிய மாற்றம் ---
if st.button("தேர்வைத் தொடங்கு ➡️", type="primary") and u_name:
    # மாணவர் ஏற்கனவே எழுதியுள்ளாரா எனப் பார்த்தல்
    current_attempt = get_attempt_count(u_name, sel_sub)
    st.session_state.attempt_no = current_attempt
    
    if current_attempt > 1:
        st.warning(f"கவனம் {u_name}! இது உங்களின் {current_attempt}-வது முயற்சி.")
    
    st.session_state.user_name = u_name
    # ... (மற்ற செஷன் ஸ்டேட் வரிகள்)
