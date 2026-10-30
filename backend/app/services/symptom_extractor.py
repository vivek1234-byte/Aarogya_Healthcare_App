import re
from typing import List, Dict, Optional, Tuple
from app.core.base_schema import BaseModel
from app.services.triage_i18n import (
    DAY_WORDS, EXTRA_CLAUSE_DELIMITERS, NUMBER_WORDS, EXTRA_LEXICON, EXTRA_NEGATION_PATTERNS,
    normalize_digits, phrase_contains_negation,
)


class ExtractedClinicalInfo(BaseModel):
    symptoms: List[str]
    danger_signs: List[str]
    duration_days: Optional[int] = 1
    chief_complaint: str
    detected_language: str = "hi"
    confidence: float = 0.95


# Clinical Symptom Dictionary mapping Hindi vernacular & English terms to standardized clinical codes
SYMPTOM_LEXICON = {
    # 1. Acute Chest Pain / Coronary Syndrome
    "chest_pain": [
        "सीने में दर्द", "सीने में तेज दर्द", "छाती में दर्द", "छाती में तेज दर्द",
        "सीने में भारीपन", "छाती भारी", "chest pain", "pain in chest", "chest discomfort",
        "chest tightness", "severe chest pain"
    ],
    "sweating": [
        "पसीना आ रहा", "बहुत पसीना", "ठंडा पसीना", "पसीना छूट", "sweating", "cold sweat",
        "profuse sweating", "diaphoresis"
    ],
    "radiating_pain": [
        "बाएं हाथ में दर्द", "बाएं हाथ", "कंधे में दर्द", "जबड़े में दर्द", "पीठ में दर्द",
        "radiating to arm", "jaw pain", "shoulder pain", "radiate"
    ],
    "severe_breathlessness": [
        "सांस फूल रही", "सांस फूलना", "दम फूलना", "सांस लेने में दिक्कत", "दम घुट रहा",
        "breathlessness", "shortness of breath", "difficulty breathing", "dyspnea"
    ],

    # 2. Pediatric Danger Signs (IMNCI Under-5)
    "convulsions": [
        "झटके आ रहे", "झटके", "दौरे पड़ रहे", "दौरे", "मिर्गी", "कंपकंपी", "convulsions", "fits", "seizures"
    ],
    "cannot_drink_or_breastfeed": [
        "दूध नहीं पी पा रहा", "दूध नहीं पी रही", "पानी नहीं पी रहा", "पानी नहीं पी रही",
        "कुछ नहीं पी रहा", "दूध छोड़ दिया", "cannot drink", "unable to breastfeed", "not feeding"
    ],
    "vomiting_everything": [
        "सब उल्टी कर देता है", "जो खाता है उल्टी कर देता है", "लगातार उल्टी", "vomiting everything", "persistent vomiting"
    ],
    "abnormally_sleepy": [
        "सुस्त पड़ा है", "सुस्त पड़ी है", "सुस्त", "होश नहीं है", "उठ नहीं रहा", "उठ नहीं रही",
        "बेहोश", "lethargic", "unconscious", "abnormally sleepy", "unresponsive"
    ],
    "chest_indrawing": [
        "पसली चल रही", "छाती अंदर धंस रही", "गहरी सांस", "chest indrawing", "stridor"
    ],

    # 3. Fever & Related Signs
    "fever": [
        "बुखार", "तेज बुखार", "तापमान", "गर्म बदन", "fever", "high temperature", "pyrexia", "high fever"
    ],
    "stiff_neck": [
        "गर्दन में अकड़न", "गर्दन मुड़ नहीं रही", "गर्दन अकड़ गई", "stiff neck", "neck stiffness"
    ],
    "chills": [
        "ठंड लग रही", "कंपकंपी छूट रही", "जाड़ा लग रहा", "chills", "shivering"
    ],
    "rash": [
        "शरीर पर दाने", "लाल दाने", "चकत्ते", "daane", "skin rash", "petechiae", "red spots", "rash"
    ],

    # 4. Chronic / Other Symptoms
    "headache_severe": [
        "तेज सिरदर्द", "सिर फटा जा रहा", "severe headache", "headache"
    ],
    "dizziness": [
        "चक्कर आ रहा", "घूम रहा है", "dizziness", "vertigo"
    ],
    "cough": [
        "खांसी", "बलगम", "धसका", "cough", "coughing"
    ],
    "diarrhea": [
        "दस्त", "पतले दस्त", "लूज मोशन", "diarrhea", "loose stools"
    ]
}


# Bengali, Marathi, Telugu and romanised Hindi phrases map to the same clinical codes
for _code, _phrases in EXTRA_LEXICON.items():
    SYMPTOM_LEXICON.setdefault(_code, []).extend(_phrases)


def check_negation(text: str, keyword: str) -> bool:
    """
    Checks if a clinical symptom is negated in Hindi ('नहीं', 'ना', 'कोई ... नहीं')
    or English ('no', 'not', 'without', 'denies') strictly within its local clause.
    """
    idx = text.find(keyword)
    if idx == -1:
        return False

    clause_delimiters = [',', ';', '।', '.', ' और ', ' तथा ', ' लेकिन ', ' किन्तु ', ' and ', ' but '] + EXTRA_CLAUSE_DELIMITERS
    
    # Left bound of the clause
    left_bound = 0
    for delim in clause_delimiters:
        d_pos = text.rfind(delim, 0, idx)
        if d_pos != -1 and d_pos + len(delim) > left_bound:
            left_bound = d_pos + len(delim)
            
    # Right bound of the clause
    right_bound = len(text)
    for delim in clause_delimiters:
        d_pos = text.find(delim, idx + len(keyword))
        if d_pos != -1 and d_pos < right_bound:
            right_bound = d_pos
            
    clause = text[left_bound:right_bound].strip()

    negation_patterns = [
        r'(^|\s)नहीं(\s|$|[.,!?।])',
        r'(^|\s)ना(\s|$|[.,!?।])',
        r'कोई\s+.*नहीं',
        r'\bno\b',
        r'\bnot\b',
        r'\bwithout\b',
        r'\bdenies\b',
        r'\bnever\b'
    ] + EXTRA_NEGATION_PATTERNS
    for pat in negation_patterns:
        if re.search(pat, clause):
            return True
    return False


def extract_duration_days(text: str) -> Optional[int]:
    """Extracts duration in days from vernacular phrases."""
    text_lower = normalize_digits(text.lower())

    match_digit = re.search(r'(\d+)\s*' + DAY_WORDS, text_lower)
    if match_digit:
        return int(match_digit.group(1))

    hindi_numbers = {
        "एक": 1, "दो": 2, "तीन": 3, "चार": 4, "पांच": 5, "छह": 6, "सात": 7, "हफ्ते": 7
    }
    hindi_numbers.update(NUMBER_WORDS)
    for word, val in hindi_numbers.items():
        if re.search(re.escape(word) + r'\s*' + DAY_WORDS, text_lower):
            return val

    if "आज से" in text_lower or "today" in text_lower:
        return 1
    if "कल से" in text_lower or "yesterday" in text_lower:
        return 2

    return 1 # Default 1 day


def extract_clinical_symptoms(transcript: str, language: str = "hi") -> ExtractedClinicalInfo:
    """
    Parses unstructured multilingual speech transcription into standardized clinical symptom codes.
    Applies clause-level clinical negation detection to discard symptoms explicitly denied.
    """
    cleaned_text = normalize_digits(transcript.strip().lower())
    identified_symptoms: List[str] = []
    danger_signs: List[str] = []

    red_flag_codes = {
        "convulsions", "cannot_drink_or_breastfeed", "abnormally_sleepy",
        "chest_indrawing", "stiff_neck", "radiating_pain", "severe_breathlessness"
    }

    # 1. Primary Lexicon matching
    for symptom_code, synonyms in SYMPTOM_LEXICON.items():
        for syn in synonyms:
            if syn in cleaned_text:
                # Phrases that themselves contain a negation word ("ఊపిరి ఆడటం లేదు") are positive findings
                if symptom_code != "cannot_drink_or_breastfeed" and not phrase_contains_negation(syn) \
                        and check_negation(cleaned_text, syn):
                    continue

                if symptom_code not in identified_symptoms:
                    identified_symptoms.append(symptom_code)
                    if symptom_code in red_flag_codes:
                        danger_signs.append(symptom_code)
                break

    # 2. Flexible semantic component checks with negation awareness
    # Chest pain
    if "chest_pain" not in identified_symptoms:
        if ("सीने" in cleaned_text or "छाती" in cleaned_text or "chest" in cleaned_text) and \
           ("दर्द" in cleaned_text or "pain" in cleaned_text or "भारी" in cleaned_text):
            if not (check_negation(cleaned_text, "दर्द") or check_negation(cleaned_text, "pain")):
                identified_symptoms.append("chest_pain")

    # Sweating
    if "sweating" not in identified_symptoms:
        if ("पसीना" in cleaned_text or "sweat" in cleaned_text) and \
                not (check_negation(cleaned_text, "पसीना") or check_negation(cleaned_text, "sweat")):
            identified_symptoms.append("sweating")

    # Radiating arm/jaw pain
    if "radiating_pain" not in identified_symptoms:
        if ("हाथ" in cleaned_text or "arm" in cleaned_text or "जबड़े" in cleaned_text or "jaw" in cleaned_text) and \
           ("दर्द" in cleaned_text or "pain" in cleaned_text):
            if not (check_negation(cleaned_text, "दर्द") or check_negation(cleaned_text, "pain")):
                identified_symptoms.append("radiating_pain")
                danger_signs.append("radiating_pain")

    # Stiff neck
    if "stiff_neck" not in identified_symptoms:
        if ("गर्दन" in cleaned_text or "neck" in cleaned_text) and \
           ("अकड़" in cleaned_text or "stiff" in cleaned_text or "दर्द" in cleaned_text):
            if not (check_negation(cleaned_text, "अकड़") or check_negation(cleaned_text, "stiff") or check_negation(cleaned_text, "गर्दन")):
                identified_symptoms.append("stiff_neck")
                danger_signs.append("stiff_neck")

    # Inability to feed (Child under-5)
    if "cannot_drink_or_breastfeed" not in identified_symptoms:
        if ("दूध" in cleaned_text or "breastfeed" in cleaned_text or "पानी" in cleaned_text) and \
           ("नहीं" in cleaned_text or "cannot" in cleaned_text or "unable" in cleaned_text):
            identified_symptoms.append("cannot_drink_or_breastfeed")
            danger_signs.append("cannot_drink_or_breastfeed")

    # Convulsions
    if "convulsions" not in identified_symptoms:
        if ("झटके" in cleaned_text or "दौरे" in cleaned_text or "convulsion" in cleaned_text or "seizure" in cleaned_text) and \
           not (check_negation(cleaned_text, "झटके") or check_negation(cleaned_text, "convulsion")):
            identified_symptoms.append("convulsions")
            danger_signs.append("convulsions")

    # Severe breathlessness
    if "severe_breathlessness" not in identified_symptoms:
        if ("सांस" in cleaned_text or "breath" in cleaned_text) and \
           ("फूल" in cleaned_text or "दिक्कत" in cleaned_text or "short" in cleaned_text or "घुट" in cleaned_text):
            if not check_negation(cleaned_text, "सांस"):
                identified_symptoms.append("severe_breathlessness")
                danger_signs.append("severe_breathlessness")

    # Cluster danger flag: chest_pain + sweating
    if "chest_pain" in identified_symptoms and "sweating" in identified_symptoms:
        if "chest_pain_sweating_cluster" not in danger_signs:
            danger_signs.append("chest_pain_sweating_cluster")

    duration = extract_duration_days(cleaned_text)
    chief_complaint = transcript if len(transcript) <= 120 else transcript[:117] + "..."

    return ExtractedClinicalInfo(
        symptoms=identified_symptoms,
        danger_signs=danger_signs,
        duration_days=duration,
        chief_complaint=chief_complaint,
        detected_language=language,
        confidence=0.95 if identified_symptoms else 0.70
    )
