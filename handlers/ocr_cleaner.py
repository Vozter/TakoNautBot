import re

def clean_ocr_text(text: str, lang: str) -> str:
    cleaners = {
        'hin': clean_hindi,
        'jpn': clean_japanese,
        'kor': clean_korean,
        'chi_sim': clean_chinese,
        'chi_tra': clean_chinese,
        'ara': clean_arabic,
        'rus': clean_russian,
        'heb': clean_hebrew,
        'tha': clean_thai,
        'ben': clean_bengali,
        'guj': clean_gujarati,
        'tel': clean_telugu,
        'tam': clean_tamil,
        'kan': clean_kannada,
        'mal': clean_malayalam,
        'amh': clean_amharic,
        'ell': clean_greek,
        'kat': clean_georgian,
        'hye': clean_armenian,
    }
    cleaner = cleaners.get(lang)
    return cleaner(text) if cleaner else text

def clean_hindi(text: str) -> str:
    # Common OCR glitches in Devanagari (sample set)
    corrections = {
        'त्र': '',  # false conjunct
        '््': '्',
        'गगाजल': 'गंगाजल',
        'हलत्र': 'हल',
        'कलत्र': 'कल',
        'फलत्र': 'फल',
        'बत्र': 'बल',
        'दित्र': 'दिल',
        'थमों': 'थम',
        'कछ': 'कुछ',
        'समनन्‍्दर': 'समंदर',
        'निकल्रेगा': 'निकलेगा',
        'गगाज': 'गंगाजल',
        'बल्ल': 'बल',
        'दिल्र': 'दिल',
        'च निकल्लेगा': 'चल निकलेगा',
    }
    for wrong, right in corrections.items():
        text = text.replace(wrong, right)

    # Strip non-Devanagari noise
    allowed_punct = '।,.\-!?'
    pattern = fr'[^\u0900-\u097F\s{allowed_punct}]'
    text = re.sub(pattern, '', text)

    return text.strip()

def clean_japanese(text):
    text = re.sub(r'[^\u3040-\u30FF\u4E00-\u9FFF\s。、ー!?]', '', text)
    return text.strip()

def clean_korean(text):
    text = re.sub(r'[^\uAC00-\uD7A3\s.,!?]', '', text)
    return text.strip()

def clean_chinese(text):
    text = re.sub(r'[^\u4E00-\u9FFF\s。，！？]', '', text)
    return text.strip()

def clean_arabic(text):
    text = re.sub(r'[^\u0600-\u06FF\s.,!?]', '', text)
    return text.strip()

def clean_russian(text):
    text = re.sub(r'[^\u0400-\u04FF\s.,!?]', '', text)
    return text.strip()

def clean_hebrew(text):
    text = re.sub(r'[^\u0590-\u05FF\s.,!?]', '', text)
    return text.strip()

def clean_thai(text):
    text = re.sub(r'[^\u0E00-\u0E7F\s.,!?]', '', text)
    return text.strip()

def clean_bengali(text):
    text = re.sub(r'[^\u0980-\u09FF\s.,!?]', '', text)
    return text.strip()

def clean_gujarati(text):
    text = re.sub(r'[^\u0A80-\u0AFF\s.,!?]', '', text)
    return text.strip()

def clean_telugu(text):
    text = re.sub(r'[^\u0C00-\u0C7F\s.,!?]', '', text)
    return text.strip()

def clean_tamil(text):
    text = re.sub(r'[^\u0B80-\u0BFF\s.,!?]', '', text)
    return text.strip()

def clean_kannada(text):
    # Common OCR cleanup
    corrections = {
        'ನ್‍': 'ನ್',
        '್್': '್',
        'ಲ್‌': 'ಲ್',
        'ಅಮೃತದ್': 'ಅಮೃತದ',
        'ಭ್ರಾಂತಿಯ': 'ಭ್ರಾಂತಿಯ',
        'ಮಜ್ಜೋ': 'ಮಜ್ಜೊ',
        'ಗಗಾಜ': 'ಗಂಗಾಜ'  # optional example if applicable
    }
    for wrong, right in corrections.items():
        text = text.replace(wrong, right)

    # Keep Kannada Unicode block + whitespace + punctuation
    text = re.sub(r'[^\u0C80-\u0CFF\s.,!?]', '', text)
    return text.strip()

def clean_malayalam(text):
    text = re.sub(r'[^\u0D00-\u0D7F\s.,!?]', '', text)
    return text.strip()

def clean_amharic(text):
    text = re.sub(r'[^\u1200-\u137F\s.,!?]', '', text)
    return text.strip()

def clean_greek(text):
    text = re.sub(r'[^\u0370-\u03FF\s.,!?]', '', text)
    return text.strip()

def clean_georgian(text):
    text = re.sub(r'[^\u10A0-\u10FF\s.,!?]', '', text)
    return text.strip()

def clean_armenian(text):
    text = re.sub(r'[^\u0530-\u058F\s.,!?]', '', text)
    return text.strip()
