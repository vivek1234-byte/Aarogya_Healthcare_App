"""
Patient health assistant (Hindi, English, Bengali, Marathi, Telugu).
1. Every message first goes through the deterministic red-flag gate. A danger sign
   returns a fixed emergency reply and escalates to the doctor; the model is not called.
2. Otherwise Claude answers in the patient's language under strict rules: no diagnosis,
   no medicine names or doses, refer to the ASHA / PHC doctor / 108 when needed.
"""

import anthropic

from app.portal import config
from app.services.safety_gate import evaluate_safety_gate
from app.services.symptom_extractor import extract_clinical_symptoms

LANGUAGE_NAMES = {'hi': 'Hindi', 'en': 'English', 'bn': 'Bengali', 'mr': 'Marathi', 'te': 'Telugu'}

EMERGENCY_REPLY = {
    'en': 'This could be an emergency. Call 108 for an ambulance now. Do not wait. Your ASHA worker and the PHC doctor have been alerted.',
    'hi': 'यह आपातकाल हो सकता है। अभी 108 पर कॉल करके एम्बुलेंस बुलाएं। इंतज़ार न करें। आपकी आशा कार्यकर्ता और PHC डॉक्टर को सूचना भेज दी गई है।',
    'bn': 'এটি জরুরি অবস্থা হতে পারে। এখনই 108 নম্বরে ফোন করে অ্যাম্বুলেন্স ডাকুন। অপেক্ষা করবেন না। আপনার আশা কর্মী ও PHC ডাক্তারকে জানানো হয়েছে।',
    'mr': 'ही आपत्कालीन स्थिती असू शकते. आत्ताच 108 वर कॉल करून रुग्णवाहिका बोलवा. थांबू नका. तुमच्या आशा सेविका आणि PHC डॉक्टरांना कळवले आहे.',
    'te': 'ఇది అత్యవసర పరిస్థితి కావచ్చు. వెంటనే 108కి కాల్ చేసి అంబులెన్స్ పిలవండి. ఆలస్యం చేయకండి. మీ ఆశా కార్యకర్త మరియు PHC డాక్టర్‌కు సమాచారం పంపబడింది.',
}

UNAVAILABLE_REPLY = {
    'en': 'The assistant is not available right now. For any health problem, contact your ASHA worker. In an emergency call 108.',
    'hi': 'सहायक अभी उपलब्ध नहीं है। किसी भी स्वास्थ्य समस्या के लिए अपनी आशा कार्यकर्ता से संपर्क करें। आपातकाल में 108 पर कॉल करें।',
    'bn': 'সহকারী এখন উপলব্ধ নয়। যেকোনো স্বাস্থ্য সমস্যায় আপনার আশা কর্মীর সাথে যোগাযোগ করুন। জরুরি অবস্থায় 108 নম্বরে ফোন করুন।',
    'mr': 'सहाय्यक सध्या उपलब्ध नाही. कोणत्याही आरोग्य समस्येसाठी तुमच्या आशा सेविकेशी संपर्क साधा. आपत्कालीन स्थितीत 108 वर कॉल करा.',
    'te': 'సహాయకుడు ఇప్పుడు అందుబాటులో లేరు. ఏ ఆరోగ్య సమస్యకైనా మీ ఆశా కార్యకర్తను సంప్రదించండి. అత్యవసరమైతే 108కి కాల్ చేయండి.',
}

SYSTEM_PROMPT = """You are ArogyaSaathi, a health assistant for patients in rural India, many of whom have low literacy and use voice.
Patients may have hypertension or diabetes and are followed up by an ASHA worker and a PHC doctor.

Language: reply in the language the patient wrote in. If unclear, use the patient's selected language given below. Use the native script of that language (Devanagari for Hindi and Marathi, Bengali script, Telugu script), simple everyday words, and short sentences. Your reply may be read aloud, so avoid tables, markdown symbols and long lists; at most 3 short points.

Safety rules (always apply):
- Never diagnose. You may explain what a reading or symptom generally means and who should check it.
- Never name, suggest, change or dose any medicine, including home remedies taken as medicine. If asked, say only the doctor can decide medicines, and advise taking medicines exactly as the doctor prescribed.
- If the patient describes chest pain, breathing difficulty, fits, fainting, heavy bleeding, a very high or very low sugar or BP reading, or anything that sounds urgent, tell them to call 108 now and inform their ASHA worker.
- For any new or worsening problem, tell them to contact their ASHA worker or visit the PHC.
- Do not claim to be a doctor. Do not make up facts about the patient; use only the data given below.
- Encourage healthy habits relevant to BP and sugar: less salt, regular meals, walking, regular check-ins, taking medicines on time.
Keep each reply under 120 words."""


def red_flag_check(text, age):
    extracted = extract_clinical_symptoms(text)
    gate = evaluate_safety_gate(symptoms=extracted.symptoms, age=age or 30)
    if gate.is_triggered:
        return {'rule': gate.rule_code, 'condition': gate.condition_name, 'symptoms': extracted.symptoms}
    return None


def patient_context(profile, latest, reports):
    lines = [f"Selected language: {LANGUAGE_NAMES.get(profile.get('language'), 'Hindi')}"]
    if profile.get('age'):
        lines.append(f"Patient: {profile['age']} years, {profile.get('gender') or ''}")
    if profile.get('conditions'):
        lines.append(f"Known conditions (as recorded by the ASHA worker): {', '.join(profile['conditions'])}")
    if latest:
        parts = []
        if latest.get('systolic'):
            parts.append(f"BP {latest['systolic']}/{latest['diastolic']} mmHg")
        if latest.get('glucose'):
            parts.append(f"sugar {latest['glucose']} mg/dL")
        if latest.get('pulse'):
            parts.append(f"pulse {latest['pulse']}")
        if parts:
            lines.append(f"Latest reading ({latest['recorded_at']}): {', '.join(parts)}")
    if reports:
        lines.append('Recent doctor notes: ' + ' | '.join(f"{r['title']}: {r['summary'][:200]}" for r in reports[:2]))
    return '\n'.join(lines)


_client = None


def _get_client():
    global _client
    if _client is None:
        _client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY, timeout=60.0, max_retries=2)
    return _client


def ask_claude(history, context):
    """history: list of {'role': 'user'|'assistant', 'content': str}, ending with the new user message."""
    if not config.ANTHROPIC_API_KEY:
        return None, 'not_configured'
    try:
        response = _get_client().beta.messages.create(
            model=config.CHAT_MODEL,
            max_tokens=16000,
            output_config={'effort': 'low'},
            betas=['server-side-fallback-2026-07-01'],
            fallbacks='default',
            system=[
                {'type': 'text', 'text': SYSTEM_PROMPT},
                {'type': 'text', 'text': f'Patient data:\n{context}'},
            ],
            messages=history,
        )
    except anthropic.AuthenticationError:
        return None, 'auth_error'
    except anthropic.RateLimitError:
        return None, 'rate_limited'
    except anthropic.APIStatusError as e:
        return None, f'api_error_{e.status_code}'
    except anthropic.APIConnectionError:
        return None, 'connection_error'

    if response.stop_reason == 'refusal':
        return None, 'refusal'
    text = ''.join(block.text for block in response.content if block.type == 'text').strip()
    return (text or None), (None if text else 'empty')
