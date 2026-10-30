"""
Multilingual support for voice triage: Bengali, Marathi, Telugu and romanised Hindi
symptom phrases, negation words, and the guided questions in all five languages.
The safety gate stays deterministic: these phrases map to the same clinical codes.
"""

import re

LANGUAGES = ('hi', 'en', 'bn', 'mr', 'te')

# Additional phrases per clinical code (merged into SYMPTOM_LEXICON in symptom_extractor)
EXTRA_LEXICON = {
    'chest_pain': [
        'বুকে ব্যথা', 'বুকে ব্যাথা', 'বুক ব্যথা', 'বুকে চাপ',
        'छातीत दुखत', 'छातीत दुखणे', 'छातीत वेदना', 'छातीत कळ',
        'ఛాతీ నొప్పి', 'ఛాతిలో నొప్పి', 'ఛాతీలో నొప్పి', 'గుండె నొప్పి',
        'seene mein dard', 'seene me dard', 'sine me dard', 'chhati me dard', 'chati me dard', 'chhati mein dard',
    ],
    'sweating': [
        'ঘাম', 'घाम', 'చెమట', 'pasina', 'paseena',
    ],
    'radiating_pain': [
        'বাঁ হাতে ব্যথা', 'চোয়ালে ব্যথা', 'কাঁধে ব্যথা',
        'डाव्या हातात दुख', 'जबड्यात दुख', 'खांद्यात दुख',
        'ఎడమ చేతికి నొప్పి', 'ఎడమ చేయి నొప్పి', 'దవడ నొప్పి', 'భుజం నొప్పి',
        'baye haath me dard', 'baayen haath mein dard', 'jabde me dard',
    ],
    'severe_breathlessness': [
        'শ্বাসকষ্ট', 'শ্বাস নিতে কষ্ট', 'দম বন্ধ',
        'श्वास घ्यायला त्रास', 'दम लागत', 'धाप लागत',
        'ఊపిరి ఆడటం లేదు', 'ఊపిరి ఆడట్లేదు', 'శ్వాస తీసుకోవడం కష్టం', 'ఆయాసం',
        'saans phool', 'sans phool', 'saans lene me dikkat', 'dam ghut',
    ],
    'convulsions': [
        'খিঁচুনি', 'খিচুনি', 'झटके येत', 'आकडी', 'फिट येत', 'ఫిట్స్', 'ఫిట్లు', 'మూర్ఛ', 'jhatke', 'daure',
    ],
    'cannot_drink_or_breastfeed': [
        'দুধ খাচ্ছে না', 'বুকের দুধ খাচ্ছে না', 'কিছু খেতে পারছে না', 'জল খেতে পারছে না',
        'दूध पीत नाही', 'पाणी पीत नाही', 'काही पीत नाही',
        'పాలు తాగడం లేదు', 'పాలు తాగట్లేదు', 'నీళ్లు తాగడం లేదు',
        'doodh nahi pi', 'dudh nahi pi', 'pani nahi pi',
    ],
    'vomiting_everything': [
        'সব বমি করে দিচ্ছে', 'বারবার বমি', 'सतत उलट्या', 'सगळं उलटून', 'అన్నీ వాంతి', 'పదే పదే వాంతులు',
        'lagatar ulti', 'sab ulti',
    ],
    'abnormally_sleepy': [
        'অজ্ঞান', 'নেতিয়ে পড়েছে', 'সাড়া দিচ্ছে না', 'बेशुद्ध', 'प्रतिसाद देत नाही',
        'స్పృహ లేదు', 'స్పృహ కోల్పోయ', 'behosh',
    ],
    'chest_indrawing': [
        'পাঁজর ঢুকে যাচ্ছে', 'बरगड्या आत ओढल्या', 'పక్కటెముకలు లోపలికి',
    ],
    'fever': [
        'জ্বর', 'ताप', 'జ్వరం', 'bukhar', 'bukhaar',
    ],
    'stiff_neck': [
        'ঘাড় শক্ত', 'मान ताठ', 'మెడ బిగుసుకు', 'మెడ పట్టేసింది', 'gardan akad',
    ],
    'chills': [
        'কাঁপুনি', 'শীত করছে', 'थंडी वाजत', 'हुडहुडी', 'చలి', 'వణుకు', 'thand lag',
    ],
    'rash': [
        'ফুসকুড়ি', 'লাল দাগ', 'पुरळ', 'लाल चट्टे', 'దద్దుర్లు', 'ఎర్రటి మచ్చలు', 'chakatte',
    ],
    'headache_severe': [
        'মাথা ব্যথা', 'মাথাব্যথা', 'डोकेदुखी', 'डोकं दुखत', 'తలనొప్పి', 'sir dard', 'sar dard',
    ],
    'dizziness': [
        'মাথা ঘোরা', 'মাথা ঘুরছে', 'चक्कर', 'తల తిరుగు', 'కళ్ళు తిరుగు', 'chakkar',
    ],
    'cough': [
        'কাশি', 'खोकला', 'దగ్గు', 'khansi', 'khaansi',
    ],
    'diarrhea': [
        'পাতলা পায়খানা', 'ডায়রিয়া', 'পেট খারাপ', 'जुलाब', 'अतिसार', 'पातळ संडास', 'విరేచనాలు', 'dast', 'loose motion',
    ],
}

# Negation words that must be in the same clause as a symptom to discard it
EXTRA_NEGATION_PATTERNS = [
    r'(^|\s)না(\s|$|[.,!?।])', r'নেই', r'নাই',     # Bengali
    r'नाही',                                        # Marathi
    r'లేదు', r'లేవు', r'కాదు',                      # Telugu
    r'\bnahi\b', r'\bnahin\b', r'\bnhi\b',          # Romanised Hindi
]

EXTRA_CLAUSE_DELIMITERS = [' এবং ', ' কিন্তু ', ' आणि ', ' पण ', ' మరియు ', ' కానీ ', ' aur ', ' lekin ']

NEGATION_WORDS = ('नहीं', 'ना ', 'না', 'নেই', 'नाही', 'లేదు', 'లేవు', 'nahi', 'not', 'cannot', 'unable')

DAY_WORDS = r'(दिन|days?|day|रोज़|দিন|दिवस|దినాలు|రోజులు|రోజు|din)'

NUMBER_WORDS = {
    'one': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5, 'six': 6, 'seven': 7,
    'ek': 1, 'do': 2, 'teen': 3, 'char': 4, 'paanch': 5,
    'এক': 1, 'দুই': 2, 'তিন': 3, 'চার': 4, 'পাঁচ': 5, 'ছয়': 6, 'সাত': 7,
    'दोन': 2, 'पाच': 5, 'सहा': 6,
    'ఒక': 1, 'రెండు': 2, 'మూడు': 3, 'నాలుగు': 4, 'ఐదు': 5, 'ఆరు': 6, 'ఏడు': 7,
}

_DIGIT_MAP = str.maketrans('०१२३४५६७८९০১২৩৪৫৬৭৮৯౦౧౨౩౪౫౬౭౮౯', '0123456789' * 3)


def normalize_digits(text):
    return text.translate(_DIGIT_MAP)


def phrase_contains_negation(phrase):
    return any(word in phrase for word in NEGATION_WORDS)


# ================= GUIDED QUESTIONS =================
QUESTIONS = {
    'Q_CHEST_RADIATION': {
        'en': 'Does the chest pain spread to the left arm, jaw or shoulder? Is there cold sweating?',
        'hi': 'क्या सीने का दर्द बाएं हाथ, गर्दन या जबड़े में जा रहा है, या पसीना आ रहा है?',
        'bn': 'বুকের ব্যথা কি বাঁ হাত, চোয়াল বা কাঁধে ছড়াচ্ছে? ঠান্ডা ঘাম হচ্ছে কি?',
        'mr': 'छातीतील दुखणे डाव्या हातात, जबड्यात किंवा खांद्यात जात आहे का? थंड घाम येत आहे का?',
        'te': 'ఛాతీ నొప్పి ఎడమ చేతికి, దవడకు లేదా భుజానికి వ్యాపిస్తుందా? చల్లని చెమటలు పడుతున్నాయా?',
    },
    'Q_CHILD_DANGER': {
        'en': 'Is the child able to drink or breastfeed? Have there been convulsions or non-stop vomiting?',
        'hi': 'क्या बच्चा मां का दूध या पानी पी पा रहा है? क्या झटके या लगातार उल्टी हुई है?',
        'bn': 'শিশু কি বুকের দুধ বা জল খেতে পারছে? খিঁচুনি বা বারবার বমি হয়েছে কি?',
        'mr': 'बाळ दूध किंवा पाणी पिऊ शकत आहे का? झटके किंवा सतत उलट्या झाल्या का?',
        'te': 'బిడ్డ పాలు లేదా నీళ్లు తాగగలుగుతోందా? ఫిట్స్ లేదా ఆగకుండా వాంతులు వచ్చాయా?',
    },
    'Q_FEVER_DANGER': {
        'en': 'How many days has the fever lasted? Is there any neck stiffness or skin rash?',
        'hi': 'बुखार कितने दिनों से है? क्या गर्दन में अकड़न है या शरीर पर लाल दाने हैं?',
        'bn': 'জ্বর কত দিন ধরে? ঘাড় শক্ত হয়ে গেছে বা গায়ে ফুসকুড়ি আছে কি?',
        'mr': 'ताप किती दिवसांपासून आहे? मान ताठ झाली आहे का किंवा अंगावर पुरळ आहे का?',
        'te': 'జ్వరం ఎన్ని రోజులుగా ఉంది? మెడ బిగుసుకుపోయిందా లేదా ఒంటిపై దద్దుర్లు ఉన్నాయా?',
    },
}

# Tap-to-answer options per question: each sends canonical text the extractor understands
QUICK_ANSWERS = {
    'Q_CHEST_RADIATION': [
        {'label': 'Pain spreads to arm / jaw · दर्द हाथ/जबड़े तक', 'text': 'pain radiating to arm and jaw'},
        {'label': 'Cold sweating · ठंडा पसीना', 'text': 'cold sweat'},
        {'label': 'Breathlessness · सांस फूल रही', 'text': 'shortness of breath'},
        {'label': 'None of these · इनमें से कुछ नहीं', 'text': 'none of these signs'},
    ],
    'Q_CHILD_DANGER': [
        {'label': 'Cannot drink / breastfeed · दूध नहीं पी रहा', 'text': 'cannot drink, unable to breastfeed'},
        {'label': 'Convulsions · झटके', 'text': 'convulsions'},
        {'label': 'Vomits everything · सब उल्टी', 'text': 'vomiting everything'},
        {'label': 'Very sleepy / unconscious · बेहोश', 'text': 'abnormally sleepy'},
        {'label': 'None of these · इनमें से कुछ नहीं', 'text': 'none of these signs'},
    ],
    'Q_FEVER_DANGER': [
        {'label': 'Fever 1–2 days · 1–2 दिन', 'text': 'fever since 2 days'},
        {'label': 'Fever 3+ days · 3+ दिन', 'text': 'fever since 3 days'},
        {'label': 'Stiff neck · गर्दन अकड़न', 'text': 'stiff neck'},
        {'label': 'Skin rash · लाल दाने', 'text': 'skin rash'},
        {'label': 'No stiff neck or rash · कुछ नहीं', 'text': 'none of these signs'},
    ],
}

# A bare yes/no cannot be mapped safely onto a compound question
_BARE_REPLY = re.compile(
    r'^\s*(yes|yeah|yep|no|nope|haan|han|ha|hanji|nahi|nahin|हाँ|हां|हा|जी|नहीं|ना|হ্যাঁ|হাঁ|না|होय|हो|नाही|అవును|ఔను|హా|లేదు|కాదు)'
    r'(\s+(ji|जी|hai|है))?\s*[.!।]?\s*$', re.IGNORECASE)


def is_bare_yes_no(text):
    return bool(_BARE_REPLY.match(text or ''))


ANSWER_IN_WORDS = {
    'en': 'Please tap an answer below or say the symptom in words (for example "pain goes to the left arm").',
    'hi': 'कृपया नीचे जवाब चुनें या लक्षण शब्दों में बताएं (जैसे "दर्द बाएं हाथ में जा रहा है")।',
    'bn': 'নিচে একটি উত্তর বেছে নিন বা লক্ষণটি কথায় বলুন (যেমন "ব্যথা বাঁ হাতে যাচ্ছে")।',
    'mr': 'कृपया खालील उत्तर निवडा किंवा लक्षण शब्दांत सांगा (उदा. "दुखणे डाव्या हातात जात आहे").',
    'te': 'దయచేసి క్రింద ఒక సమాధానం ఎంచుకోండి లేదా లక్షణాన్ని మాటల్లో చెప్పండి (ఉదా. "నొప్పి ఎడమ చేతికి వెళ్తోంది").',
}


def question_text(code, lang):
    texts = QUESTIONS.get(code, {})
    return texts.get(lang) or texts.get('en')
