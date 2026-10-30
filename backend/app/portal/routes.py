"""
HTTP API for the four roles. handle() returns (status, payload) for /api/v1 routes,
or None so local_server.py can fall through to static files.

Access rules:
- PATIENT sees only their own data.
- HEALTH_WORKER sees patients, triage, referrals and signals of their own village.
- DOCTOR sees the escalation queue, patient trends (pseudonymised) and sends reports.
- HEALTH_OFFICER sees surveillance for all villages.
- DOCTOR and HEALTH_OFFICER can read the audit trail.
"""

import math
import re
import time
from datetime import datetime, timedelta

from app.core.security import encrypt_pii, generate_pseudonym
from app.portal import auth, db
from app.portal.auth import AuthError
from app.services import hospital_finder, patient_chat, triage_i18n
from app.services.chronic_care import chronic_care_engine
from app.services.langgraph_triage import orchestrator
from app.services.safety_gate import sanitize_zero_prescriptions
from app.services.surveillance_engine import surveillance_engine
from app.services.voice_checkin import VoiceCheckinParser

LEVEL_LABELS = {'EMERGENCY': 'Emergency', 'REFER': 'Refer', 'TREAT_LOCALLY': 'Treat locally', 'HOME_CARE': 'Home care'}
CONDITIONS = ('Hypertension', 'Diabetes', 'Pregnancy', 'Tuberculosis', 'Child under 5', 'Elderly (60+)')
SURVEILLANCE_DAYS = 30
BASELINE_MIN_DAYS = 7
CLUSTER_KM = 10
CORROBORATION_Z = 2.0
MIN_ABSOLUTE_EXCESS = 10


class ApiError(Exception):
    def __init__(self, status, message):
        super().__init__(message)
        self.status = status


# ================= SMALL HELPERS =================
def require(user, *roles):
    if not user:
        raise ApiError(401, 'Please log in again.')
    if roles and user['role'] not in roles:
        raise ApiError(403, 'You do not have access to this.')


def to_int(value, lo=None, hi=None, name='value'):
    if value in (None, ''):
        return None
    try:
        n = int(round(float(value)))
    except (TypeError, ValueError):
        raise ApiError(400, f'{name} must be a number.')
    if (lo is not None and n < lo) or (hi is not None and n > hi):
        raise ApiError(400, f'{name} must be between {lo} and {hi}.')
    return n


def to_float(value, lo=None, hi=None, name='value'):
    if value in (None, ''):
        return None
    try:
        n = float(value)
    except (TypeError, ValueError):
        raise ApiError(400, f'{name} must be a number.')
    if (lo is not None and n < lo) or (hi is not None and n > hi):
        raise ApiError(400, f'{name} must be between {lo} and {hi}.')
    return n


def lang_of(value):
    return value if value in triage_i18n.LANGUAGES else 'hi'


def village(village_id):
    return db.query_one('SELECT * FROM villages WHERE id = ?', (village_id,)) if village_id else None


def village_name(village_id):
    v = village(village_id)
    return v['name'] if v else ''


def actor(user):
    return user['id'], user['role']


def short_date(ts):
    try:
        return datetime.strptime(ts[:10], '%Y-%m-%d').strftime('%d %b')
    except (TypeError, ValueError):
        return ts


# ================= PATIENT RECORDS & CHRONIC RISK =================
def patient_row(patient_id):
    row = db.query_one('SELECT p.*, u.name_enc, u.mobile_enc, u.status FROM patients p JOIN users u ON u.id = p.user_id '
                       "WHERE p.user_id = ? AND u.status != 'ERASED'", (patient_id,))
    if not row:
        raise ApiError(404, 'Patient not found.')
    return row


def worker_patient(user, patient_id):
    row = patient_row(patient_id)
    if user['role'] == 'HEALTH_WORKER' and row['village_id'] != user['village_id']:
        raise ApiError(403, 'This patient is not in your village.')
    return row


def chronic_risk(patient_id, next_visit=None):
    since = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d %H:%M:%S')
    vitals = db.query('SELECT * FROM vitals WHERE patient_id = ? AND recorded_at >= ? ORDER BY recorded_at', (patient_id, since))
    doses = db.query('SELECT * FROM doses WHERE patient_id = ? AND date >= ? ORDER BY date', (patient_id, since[:10]))
    v_list = [{'recorded_at': datetime.strptime(v['recorded_at'], '%Y-%m-%d %H:%M:%S'), 'systolic_bp': v['systolic'],
               'diastolic_bp': v['diastolic'], 'blood_glucose': v['glucose'], 'pulse': v['pulse']} for v in vitals]
    a_list = [{'scheduled_time': datetime.strptime(d['date'], '%Y-%m-%d'), 'status': d['status']} for d in doses]
    visit_dt = datetime.strptime(next_visit, '%Y-%m-%d') if next_visit else None
    risk = chronic_care_engine.evaluate_patient_deterioration(v_list, a_list, visit_dt, datetime.now()).dict()
    if not vitals and not doses:
        risk.update(risk_level='NO_DATA', recommended_action='No readings yet. Record BP and sugar at the next visit.')
    recent = vitals[-14:]
    trend = {
        'days': [short_date(v['recorded_at']) for v in recent],
        'systolic': [v['systolic'] for v in recent],
        'diastolic': [v['diastolic'] for v in recent],
        'glucose': [v['glucose'] for v in recent],
        'pulse': [v['pulse'] for v in recent],
    }
    recent_doses = doses[-14:]
    dose_strip = {'days': [short_date(d['date']) for d in recent_doses], 'doses': [d['status'] for d in recent_doses]}
    latest = vitals[-1] if vitals else None
    return risk, trend, dose_strip, latest


def patient_summary(row, include_identity):
    risk, trend, doses, latest = chronic_risk(row['user_id'], row['next_visit'])
    data = {
        'id': row['user_id'],
        'pseudonym': row['pseudonym'],
        'age': row['age'],
        'gender': row['gender'],
        'village_id': row['village_id'],
        'village_name': village_name(row['village_id']),
        'conditions': db.loads(row['conditions'], []),
        'consent': db.loads(row['consent'], {}),
        'language': row['language'],
        'next_visit': row['next_visit'],
        'account_status': row['status'],
        'risk': risk,
        'trend': trend,
        'dose_strip': doses,
        'latest': latest,
    }
    if include_identity:
        data['name'] = auth.decrypt(row['name_enc'])
        data['mobile'] = auth.decrypt(row['mobile_enc'])
    return data


RISK_ORDER = {'CRITICAL': 0, 'HIGH': 1, 'MODERATE': 2, 'LOW': 3, 'NO_DATA': 4}


def chronic_summary_markdown(p):
    r = p['risk']
    lines = [
        f"# Chronic care deterioration - {p['pseudonym']}",
        '',
        f"**Patient:** {p['age']} yrs / {p['gender']} | **Village:** {p['village_name']} | **Conditions:** {', '.join(p['conditions']) or 'Not recorded'}",
        f"**Risk level:** {r['risk_level']}" + (f" | **Next visit:** {p['next_visit']}" if p['next_visit'] else ''),
        '',
        '## Readings (last 30 days)',
        f"- Average BP: {r.get('average_systolic') or '-'}/{r.get('average_diastolic') or '-'} mmHg (systolic slope {r.get('systolic_slope_per_week')} mmHg/week)",
        f"- Average sugar: {r.get('average_glucose') or '-'} mg/dL",
        f"- Medicine adherence: {r.get('adherence_rate_pct')}%",
    ]
    if p['latest']:
        lv = p['latest']
        lines.append(f"- Latest: BP {lv['systolic'] or '-'}/{lv['diastolic'] or '-'}, sugar {lv['glucose'] or '-'} ({lv['recorded_at']})")
    lines += ['', '## Flags raised'] + ([f"- {f.replace('_', ' ').title()}" for f in r['flags']] or ['- None'])
    lines += ['', '## Suggested action (for clinician review)', r['recommended_action'], '',
              '_Rule-based trend analysis. No diagnosis or prescription is made by the system._']
    return '\n'.join(lines)


def reevaluate_chronic(patient_id, actor_id, actor_role):
    p = patient_summary(patient_row(patient_id), include_identity=False)
    level = p['risk']['risk_level']
    if level in ('HIGH', 'CRITICAL'):
        pending = db.query_one("SELECT id FROM escalations WHERE source = 'CHRONIC' AND patient_id = ? AND status = 'PENDING'", (patient_id,))
        if not pending:
            esc_id = create_escalation('CHRONIC', level, p['id'], p['pseudonym'], p['village_id'],
                                       f"Chronic care: {', '.join(p['conditions']) or 'BP / sugar'} deterioration",
                                       p['risk']['recommended_action'],
                                       {'summary_markdown': chronic_summary_markdown(p), 'flags': p['risk']['flags'],
                                        'trend': p['trend'], 'dose_strip': p['dose_strip'],
                                        'patient': {'age': p['age'], 'gender': p['gender'], 'village_name': p['village_name']},
                                        'citations': ['Rule-based BP / glucose / adherence trend thresholds']})
            db.audit('Chronic Care Agent', 'SYSTEM', 'ESCALATION_CREATED',
                     {'escalation_id': esc_id, 'patient': p['pseudonym'], 'level': level, 'flags': p['risk']['flags'],
                      'triggered_by': actor_id})
            return p, esc_id
    return p, None


def create_escalation(source, level, patient_id, pseudonym, village_id, title, rationale, details):
    esc_id = f"ESC-{datetime.now().strftime('%y%m%d')}-{auth.new_id('X')[2:]}"
    db.execute('INSERT INTO escalations (id, source, level, status, patient_id, pseudonym, village_id, title, rationale, details, created_at) '
               "VALUES (?,?,?,'PENDING',?,?,?,?,?,?,?)",
               (esc_id, source, level, patient_id, pseudonym, village_id, title, rationale, db.dumps(details), db.now()))
    return esc_id


def record_vitals(patient_id, data, source, user):
    systolic = to_int(data.get('systolic'), 60, 260, 'Systolic BP')
    diastolic = to_int(data.get('diastolic'), 30, 180, 'Diastolic BP')
    if (systolic is None) != (diastolic is None):
        raise ApiError(400, 'Enter both upper (systolic) and lower (diastolic) BP.')
    if systolic is not None and diastolic >= systolic:
        raise ApiError(400, 'Lower BP must be less than upper BP.')
    values = {
        'systolic': systolic, 'diastolic': diastolic,
        'glucose': to_float(data.get('glucose'), 20, 700, 'Sugar'),
        'pulse': to_int(data.get('pulse'), 30, 220, 'Pulse'),
        'spo2': to_int(data.get('spo2'), 50, 100, 'SpO2'),
        'weight_kg': to_float(data.get('weight_kg'), 1, 300, 'Weight'),
        'temperature_f': to_float(data.get('temperature_f'), 90, 110, 'Temperature'),
    }
    if all(v is None for v in values.values()):
        raise ApiError(400, 'Enter at least one reading.')
    context = data.get('glucose_context') if data.get('glucose_context') in ('FASTING', 'AFTER_MEAL', 'RANDOM') else 'FASTING'
    db.execute('INSERT INTO vitals (patient_id, recorded_at, systolic, diastolic, glucose, glucose_context, pulse, spo2, weight_kg, '
               'temperature_f, source, recorded_by) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)',
               (patient_id, db.now(), values['systolic'], values['diastolic'], values['glucose'], context, values['pulse'],
                values['spo2'], values['weight_kg'], values['temperature_f'], source, user['id']))
    db.audit(user['id'], user['role'], 'VITALS_RECORDED', {'patient_id': patient_id, 'source': source, **values})
    return values


def record_dose(patient_id, status, user, reason=None):
    if status not in ('TAKEN', 'MISSED'):
        raise ApiError(400, 'Dose status must be TAKEN or MISSED.')
    db.execute('INSERT INTO doses (patient_id, date, status, reason, recorded_by, created_at) VALUES (?,?,?,?,?,?) '
               'ON CONFLICT (patient_id, date) DO UPDATE SET status = excluded.status, reason = excluded.reason, '
               'recorded_by = excluded.recorded_by, created_at = excluded.created_at',
               (patient_id, db.today(), status, reason, user['id'], db.now()))
    db.audit(user['id'], user['role'], 'DOSE_RECORDED', {'patient_id': patient_id, 'status': status})


# ================= PATIENT (SELF) =================
def patient_dashboard(user):
    row = patient_row(user['id'])
    p = patient_summary(row, include_identity=True)
    reports = db.query('SELECT * FROM reports WHERE patient_id = ? ORDER BY created_at DESC LIMIT 20', (user['id'],))
    for r in reports:
        doctor = db.query_one('SELECT name_enc, facility FROM users WHERE id = ?', (r['doctor_id'],))
        r['doctor_name'] = auth.decrypt(doctor['name_enc']) if doctor else ''
        r['facility'] = doctor['facility'] if doctor else ''
    referrals = db.query('SELECT * FROM referrals WHERE patient_id = ? ORDER BY created_at DESC LIMIT 10', (user['id'],))
    for r in referrals:
        r['hospital'] = db.loads(r['hospital'], {})
    asha = db.query_one('SELECT name_enc, mobile_enc FROM users WHERE id = ?', (row['asha_id'],)) if row['asha_id'] else None
    today_dose = db.query_one('SELECT status FROM doses WHERE patient_id = ? AND date = ?', (user['id'], db.today()))
    history = db.query('SELECT * FROM vitals WHERE patient_id = ? ORDER BY recorded_at DESC LIMIT 50', (user['id'],))
    return {
        'patient': p,
        'reports': reports,
        'referrals': referrals,
        'asha': {'name': auth.decrypt(asha['name_enc']), 'mobile': auth.decrypt(asha['mobile_enc'])} if asha else None,
        'today_dose': today_dose['status'] if today_dose else None,
        'vitals_history': history,
    }


CHAT_HISTORY_TURNS = 20


def patient_chat_reply(user, data):
    message = (data.get('message') or '').strip()
    if not message:
        raise ApiError(400, 'Type or say your question.')
    if len(message) > 2000:
        raise ApiError(400, 'Message is too long.')
    lang = lang_of(data.get('language'))
    row = patient_row(user['id'])

    db.execute('INSERT INTO chat_messages (patient_id, role, content, language, created_at) VALUES (?,?,?,?,?)',
               (user['id'], 'user', message, lang, db.now()))
    db.audit(user['id'], 'PATIENT', 'CHAT_INPUT', {'language': lang, 'text': message})

    flag = patient_chat.red_flag_check(message, row['age'])
    if flag:
        reply = patient_chat.EMERGENCY_REPLY[lang]
        esc_id = create_escalation('CHAT', 'EMERGENCY', user['id'], row['pseudonym'], row['village_id'],
                                   f"Patient chat red flag: {flag['condition']}",
                                   'Danger sign described by the patient in the assistant chat. Patient told to call 108.',
                                   {'summary_markdown': f"# Red flag from patient chat\n\n**Patient said:** {message}\n\n"
                                                        f"**Rule fired:** {flag['rule']} ({flag['condition']})\n\n"
                                                        f"**Symptoms recognised:** {', '.join(flag['symptoms'])}\n\n"
                                                        '_Patient was told to call 108 immediately. Please contact the patient and the ASHA worker._',
                                    'flags': flag['symptoms'], 'transcripts': [message],
                                    'patient': {'age': row['age'], 'gender': row['gender'], 'village_name': village_name(row['village_id'])},
                                    'citations': [f"Rule Code: {flag['rule']}"]})
        db.audit('Safety Gate', 'SYSTEM', 'RED_FLAG_RULE_FIRED', {'source': 'CHAT', 'patient': row['pseudonym'], 'rule': flag['rule'],
                                                                  'escalation_id': esc_id})
        db.execute('INSERT INTO chat_messages (patient_id, role, content, language, flagged, created_at) VALUES (?,?,?,?,1,?)',
                   (user['id'], 'assistant', reply, lang, db.now()))
        return {'reply': reply, 'emergency': True, 'escalation_id': esc_id}

    history = db.query('SELECT role, content FROM chat_messages WHERE patient_id = ? ORDER BY id DESC LIMIT ?',
                       (user['id'], CHAT_HISTORY_TURNS * 2))[::-1]
    while history and history[0]['role'] != 'user':
        history.pop(0)
    _, _, _, latest = chronic_risk(user['id'], row['next_visit'])
    reports = db.query('SELECT title, summary FROM reports WHERE patient_id = ? ORDER BY created_at DESC LIMIT 2', (user['id'],))
    context = patient_chat.patient_context(
        {'age': row['age'], 'gender': row['gender'], 'conditions': db.loads(row['conditions'], []), 'language': lang},
        latest, reports)
    reply, error = patient_chat.ask_claude([{'role': h['role'], 'content': h['content']} for h in history], context)
    if error:
        db.audit('Patient Assistant', 'SYSTEM', 'CHAT_UNAVAILABLE', {'patient': row['pseudonym'], 'reason': error})
        reply = patient_chat.UNAVAILABLE_REPLY[lang]
    else:
        reply, redacted = sanitize_zero_prescriptions(reply)
        if redacted:
            reply = {
                'en': 'Only your doctor can decide medicines. Please take your medicines exactly as the doctor prescribed and ask your ASHA worker if you have doubts.',
                'hi': 'दवाइयों का फ़ैसला केवल डॉक्टर कर सकते हैं। दवा बिल्कुल वैसे ही लें जैसे डॉक्टर ने बताई है, और कोई शंका हो तो अपनी आशा कार्यकर्ता से पूछें।',
            }.get(lang, patient_chat.UNAVAILABLE_REPLY[lang])
        db.audit('Patient Assistant', 'SYSTEM', 'CHAT_REPLY', {'patient': row['pseudonym'], 'language': lang, 'redacted': redacted})
    db.execute('INSERT INTO chat_messages (patient_id, role, content, language, created_at) VALUES (?,?,?,?,?)',
               (user['id'], 'assistant', reply, lang, db.now()))
    return {'reply': reply, 'emergency': False, 'unavailable': bool(error)}


# ================= HEALTH WORKER =================
def register_patient(user, data):
    consent = data.get('consent') or {}
    if not consent.get('data_use'):
        raise ApiError(403, 'Patient must give voice consent for data use to register.')
    name = (data.get('name') or '').strip()
    if len(name) < 2:
        raise ApiError(400, 'Enter the patient\'s full name.')
    mobile = auth.normalize_mobile(data.get('mobile'))
    age = to_int(data.get('age'), 0, 120, 'Age')
    if age is None:
        raise ApiError(400, 'Enter the patient\'s age.')
    gender = data.get('gender') if data.get('gender') in ('F', 'M', 'O') else 'F'
    conditions = [c for c in (data.get('conditions') or []) if c in CONDITIONS]
    if db.query_one("SELECT id FROM users WHERE role = 'PATIENT' AND mobile_hash = ?", (auth.mobile_hash(mobile),)):
        raise ApiError(409, 'A patient with this mobile number is already registered.')

    v = village(user['village_id'])
    user_id = auth.new_id('PAT')
    short = re.sub(r'[^A-Z]', '', (v['name'] if v else 'VIL').upper())[:6] or 'VIL'
    pseudonym = f"HASH-{short}-{generate_pseudonym(f'{mobile}:{user_id}')[:4]}"
    db.execute('INSERT INTO users (id, role, name_enc, mobile_enc, mobile_hash, status, village_id, created_by, created_at) '
               "VALUES (?, 'PATIENT', ?, ?, ?, 'PENDING_ACTIVATION', ?, ?, ?)",
               (user_id, encrypt_pii(name), encrypt_pii(mobile), auth.mobile_hash(mobile), user['village_id'], user['id'], db.now()))
    db.execute('INSERT INTO patients (user_id, pseudonym, age, gender, village_id, conditions, consent, language, asha_id, next_visit, created_at) '
               'VALUES (?,?,?,?,?,?,?,?,?,?,?)',
               (user_id, pseudonym, age, gender, user['village_id'], db.dumps(conditions),
                db.dumps({'data_use': True, 'sharing': bool(consent.get('sharing')),
                          'deletion_rights_explained': bool(consent.get('deletion_rights_explained')),
                          'recorded_at': db.now(), 'recorded_by': user['id']}),
                lang_of(data.get('language')), user['id'], data.get('next_visit') or None, db.now()))
    code = auth.issue_activation_code(user_id)
    db.audit(user['id'], 'HEALTH_WORKER', 'PATIENT_REGISTERED',
             {'patient': pseudonym, 'village_id': user['village_id'], 'conditions': conditions,
              'consent': {k: bool(consent.get(k)) for k in ('data_use', 'sharing', 'deletion_rights_explained')}})
    return {'id': user_id, 'pseudonym': pseudonym, 'activation_code': code,
            'activation_hours': auth.config.ACTIVATION_HOURS,
            'message': 'Registered. Give the patient this activation code to set their own password in the app.'}


def worker_checkin(user, patient_id, data):
    row = worker_patient(user, patient_id)
    transcript = (data.get('transcript') or '').strip()
    lang = lang_of(data.get('language'))
    parsed = VoiceCheckinParser.parse_checkin_speech(transcript, lang) if transcript else None
    values = {
        'systolic': data.get('systolic') or (parsed and parsed.systolic_bp),
        'diastolic': data.get('diastolic') or (parsed and parsed.diastolic_bp),
        'glucose': data.get('glucose') or (parsed and parsed.blood_glucose),
        'pulse': data.get('pulse'),
        'weight_kg': data.get('weight_kg'),
    }
    dose = data.get('dose_status') or (parsed and parsed.adherence_status)
    saved = None
    if any(v not in (None, '') for v in values.values()):
        saved = record_vitals(row['user_id'], values, 'ASHA', user)
    if dose in ('TAKEN', 'MISSED'):
        record_dose(row['user_id'], dose, user)
    if not saved and dose not in ('TAKEN', 'MISSED'):
        raise ApiError(400, 'No reading understood. Type the numbers or choose Taken / Missed.')
    if data.get('next_visit'):
        db.execute('UPDATE patients SET next_visit = ? WHERE user_id = ?', (data['next_visit'], row['user_id']))
    p, esc_id = reevaluate_chronic(row['user_id'], *actor(user))
    return {'patient': p, 'escalation_id': esc_id, 'parsed_from_voice': parsed.dict() if parsed else None}


# ================= TRIAGE =================
def _triage_payload(state, enc, lang):
    pending = None
    if not state.is_final and state.asked_questions:
        pending = state.asked_questions[-1]
    uncertain = None
    if state.is_final and not state.symptoms:
        uncertain = 'No recognised symptoms were extracted. Confirm the complaint and repeat triage, or consult the PHC doctor.'
    elif state.is_final and state.triage_level == 'HOME_CARE' and state.symptoms:
        uncertain = 'Symptoms present but no protocol matched. Observe closely and re-triage if anything changes.'
    return {
        'session_id': state.session_id,
        'patient': {'id': enc['patient_id'], 'pseudonym': enc['pseudonym'], 'age': enc['age'], 'gender': enc['gender'],
                    'village_name': village_name(enc['village_id'])},
        'language': lang,
        'transcripts': state.all_transcripts,
        'symptoms': state.symptoms,
        'danger_signs': state.danger_signs,
        'is_final': state.is_final,
        'triage_level': state.triage_level,
        'triage_label': LEVEL_LABELS.get(state.triage_level),
        'decision_rationale': state.decision_rationale,
        'pending_question': pending,
        'next_question': triage_i18n.question_text(pending, lang) if pending else None,
        'next_question_en': triage_i18n.question_text(pending, 'en') if pending and lang != 'en' else None,
        'quick_answers': triage_i18n.QUICK_ANSWERS.get(pending, []),
        'checklist': state.checklist,
        'protocol_citations': state.protocol_citations,
        'is_red_flag_overridden': state.is_red_flag_overridden,
        'uncertain': bool(uncertain),
        'uncertainty_reason': uncertain,
        'summary_markdown': enc.get('summary_md'),
        'escalation_id': enc.get('escalation_id'),
    }


def _read_summary(url):
    if not url:
        return None
    import urllib.parse
    try:
        with open(urllib.parse.unquote(url.replace('file://', '')), 'r', encoding='utf-8') as f:
            return f.read()
    except OSError:
        return None


def start_triage(user, data):
    consent = data.get('consent') or {}
    if not consent.get('data_use'):
        raise ApiError(403, 'Take the patient\'s voice consent before triage.')
    lang = lang_of(data.get('language'))
    vitals = {}
    for key, lo, hi in (('temperature_f', 90, 110), ('spo2', 50, 100), ('systolic_bp', 60, 260), ('pulse', 30, 220)):
        val = to_float(data.get('vitals', {}).get(key), lo, hi, key)
        if val is not None:
            vitals[key] = val

    if data.get('patient_id'):
        row = worker_patient(user, data['patient_id'])
        patient_id, pseudonym, age, gender = row['user_id'], row['pseudonym'], row['age'], row['gender']
    else:
        walk = data.get('walkin') or {}
        age = to_int(walk.get('age'), 0, 120, 'Age')
        if age is None:
            raise ApiError(400, 'Enter the patient\'s age.')
        gender = walk.get('gender') if walk.get('gender') in ('F', 'M', 'O') else 'F'
        patient_id = None
        pseudonym = f"WALKIN-{auth.new_id('W')[2:]}"

    state = orchestrator.start_session(patient_id=patient_id or pseudonym, patient_pseudonym=pseudonym, age=age, gender=gender,
                                       village_id=user['village_id'], language=lang, vitals=vitals)
    db.execute('INSERT INTO encounters (id, patient_id, pseudonym, age, gender, village_id, worker_id, language, vitals, created_at) '
               'VALUES (?,?,?,?,?,?,?,?,?,?)',
               (state.session_id, patient_id, pseudonym, age, gender, user['village_id'], user['id'], lang, db.dumps(vitals), db.now()))
    db.audit(user['id'], 'HEALTH_WORKER', 'TRIAGE_STARTED', {'session_id': state.session_id, 'patient': pseudonym, 'language': lang,
                                                             'vitals': vitals})
    enc = db.query_one('SELECT * FROM encounters WHERE id = ?', (state.session_id,))
    return _triage_payload(state, enc, lang)


def triage_turn(user, session_id, data):
    enc = db.query_one('SELECT * FROM encounters WHERE id = ?', (session_id,))
    if not enc or enc['worker_id'] != user['id']:
        raise ApiError(404, 'Triage session not found.')
    state = orchestrator.get_session(session_id)
    if not state:
        raise ApiError(410, 'This triage session expired (server restarted). Please start again.')
    if state.is_final:
        raise ApiError(409, 'Triage is already complete for this session.')
    text = (data.get('text') or '').strip()
    if not text:
        raise ApiError(400, 'Say or type what the patient reports.')
    lang = enc['language']

    # A bare "yes"/"haan" cannot be mapped safely onto a compound question
    if state.asked_questions and triage_i18n.is_bare_yes_no(text):
        payload = _triage_payload(state, enc, lang)
        payload['needs_words'] = triage_i18n.ANSWER_IN_WORDS.get(lang, triage_i18n.ANSWER_IN_WORDS['en'])
        return payload

    db.audit(user['id'], 'HEALTH_WORKER', 'TRIAGE_INPUT', {'session_id': session_id, 'language': lang, 'text': text})
    started = time.time()
    state = orchestrator.process_turn(session_id, text)
    if state.is_red_flag_overridden:
        db.audit('Safety Gate', 'SYSTEM', 'RED_FLAG_RULE_FIRED',
                 {'session_id': session_id, 'rule': state.protocol_citations[-1] if state.protocol_citations else None,
                  'danger_signs': state.danger_signs})
    db.audit('Triage Agent', 'SYSTEM', 'TRIAGE_DECISION' if state.is_final else 'TRIAGE_QUESTION',
             {'session_id': session_id, 'symptoms': state.symptoms, 'triage_level': state.triage_level,
              'question': None if state.is_final else (state.asked_questions[-1] if state.asked_questions else None)})

    summary_md = _read_summary(state.doctor_summary_url) if state.is_final else None
    payload_enc = dict(enc, summary_md=summary_md)
    db.execute('UPDATE encounters SET transcripts = ?, symptoms = ?, danger_signs = ?, triage_level = ?, rationale = ?, checklist = ?, '
               'citations = ?, red_flag = ?, summary_md = ?, is_final = ?, finalised_at = ? WHERE id = ?',
               (db.dumps(state.all_transcripts), db.dumps(state.symptoms), db.dumps(state.danger_signs), state.triage_level,
                state.decision_rationale, db.dumps(state.checklist), db.dumps(state.protocol_citations),
                int(state.is_red_flag_overridden), summary_md, int(state.is_final), db.now() if state.is_final else None, session_id))

    if state.is_final and state.triage_level in ('EMERGENCY', 'REFER'):
        esc_id = create_escalation(
            'TRIAGE', state.triage_level, enc['patient_id'], enc['pseudonym'], enc['village_id'],
            f"Voice triage: {', '.join(s.replace('_', ' ') for s in state.symptoms) or 'complaint'}",
            state.decision_rationale,
            {'summary_markdown': summary_md, 'flags': state.danger_signs, 'citations': state.protocol_citations,
             'transcripts': state.all_transcripts, 'encounter_id': session_id,
             'patient': {'age': enc['age'], 'gender': enc['gender'], 'village_name': village_name(enc['village_id'])},
             'summary_seconds': round(time.time() - started, 2)})
        payload_enc['escalation_id'] = esc_id
        db.audit('Referral Generator', 'SYSTEM', 'ESCALATION_CREATED', {'escalation_id': esc_id, 'session_id': session_id,
                                                                         'level': state.triage_level})
    if state.is_final:
        evaluate_surveillance()
    return _triage_payload(state, payload_enc, lang)


# ================= REFERRALS TO GOVERNMENT FACILITIES =================
def create_referral(user, data):
    hospital = data.get('hospital') or {}
    name = (hospital.get('name') or '').strip()
    if not name:
        raise ApiError(400, 'Choose a hospital or enter its name.')
    clean_hospital = {
        'name': name[:200],
        'level': (hospital.get('level') or 'Government facility')[:80],
        'address': (hospital.get('address') or '')[:300],
        'phone': re.sub(r'[^\d+\-\s]', '', hospital.get('phone') or '')[:30],
        'lat': to_float(hospital.get('lat'), -90, 90, 'Latitude'),
        'lon': to_float(hospital.get('lon'), -180, 180, 'Longitude'),
        'distance_km': to_float(hospital.get('distance_km'), 0, 1000, 'Distance'),
        'source': hospital.get('source') or 'Entered by health worker',
        'osm_id': hospital.get('id'),
    }
    urgency = data.get('urgency') if data.get('urgency') in ('EMERGENCY', 'SAME_DAY', 'WITHIN_WEEK') else 'SAME_DAY'
    patient_id, pseudonym = None, None
    if data.get('patient_id'):
        row = worker_patient(user, data['patient_id'])
        patient_id, pseudonym = row['user_id'], row['pseudonym']
    elif data.get('encounter_id'):
        enc = db.query_one('SELECT * FROM encounters WHERE id = ? AND worker_id = ?', (data['encounter_id'], user['id']))
        if not enc:
            raise ApiError(404, 'Triage session not found.')
        patient_id, pseudonym = enc['patient_id'], enc['pseudonym']
    else:
        raise ApiError(400, 'Choose the patient to refer.')
    ref_id = f"REF-{datetime.now().strftime('%y%m%d')}-{auth.new_id('X')[2:]}"
    db.execute('INSERT INTO referrals (id, patient_id, pseudonym, worker_id, village_id, encounter_id, hospital, reason, urgency, status, created_at) '
               "VALUES (?,?,?,?,?,?,?,?,?,'REFERRED',?)",
               (ref_id, patient_id, pseudonym, user['id'], user['village_id'], data.get('encounter_id'), db.dumps(clean_hospital),
                (data.get('reason') or '').strip()[:500], urgency, db.now()))
    if data.get('encounter_id'):
        esc = db.query_one('SELECT id, details FROM escalations WHERE details LIKE ?', (f'%"{data["encounter_id"]}"%',))
        if esc:
            details = db.loads(esc['details'], {})
            details['referral'] = {'id': ref_id, 'hospital': clean_hospital, 'urgency': urgency}
            db.execute('UPDATE escalations SET details = ? WHERE id = ?', (db.dumps(details), esc['id']))
    db.audit(user['id'], 'HEALTH_WORKER', 'REFERRAL_CREATED', {'referral_id': ref_id, 'patient': pseudonym,
                                                               'hospital': clean_hospital['name'], 'urgency': urgency})
    return {'id': ref_id, 'hospital': clean_hospital, 'urgency': urgency, 'pseudonym': pseudonym}


# ================= SURVEILLANCE =================
SYNDROMES = {
    'ACUTE_DIARRHOEAL_DISEASE': {
        'label': 'Acute diarrhoeal disease',
        'clinic_symptoms': {'diarrhea', 'vomiting_everything'},
        'clinic_stream': 'ACUTE_DIARRHEA',
        'pharmacy_field': 'pharmacy_ors_sales',
        'pharmacy_stream': 'PHARMACY_ORS_SALES',
        'interventions': [
            'Send the Rapid Response Team to inspect drinking water sources and sanitation',
            'ASHAs to distribute ORS and zinc door to door',
            'Chlorinate community water tanks and tube wells; collect water samples',
            'Inform the Medical Officer at the block PHC',
        ],
    },
    'ACUTE_FEBRILE_ILLNESS': {
        'label': 'Acute febrile illness (fever)',
        'clinic_symptoms': {'fever'},
        'clinic_stream': 'CLINIC_FEVER',
        'pharmacy_field': 'pharmacy_fever_sales',
        'pharmacy_stream': 'PHARMACY_FEVER_SALES',
        'interventions': [
            'House-to-house fever survey by ASHAs',
            'Test febrile patients with malaria / dengue rapid diagnostic kits',
            'Search for and remove mosquito breeding sites',
            'Inform the Medical Officer at the block PHC',
        ],
    },
}


def _daily_series(village_id, start, days):
    dates = [(start + timedelta(days=i)).strftime('%Y-%m-%d') for i in range(days)]
    encounters = db.query('SELECT substr(created_at, 1, 10) AS d, symptoms FROM encounters WHERE village_id = ? AND is_final = 1 AND created_at >= ?',
                          (village_id, dates[0]))
    signals = {s['date']: s for s in db.query('SELECT * FROM signals WHERE village_id = ? AND date >= ?', (village_id, dates[0]))}
    v = village(village_id)
    active_from = (v['created_at'] or dates[0])[:10] if v else dates[0]
    series = {'dates': dates}
    for key, syn in SYNDROMES.items():
        clinic = []
        for d in dates:
            if d < active_from:
                clinic.append(None)
                continue
            clinic.append(sum(1 for e in encounters if e['d'] == d and syn['clinic_symptoms'] & set(db.loads(e['symptoms'], []))))
        series[f'clinic_{key}'] = clinic
    series['pharmacy_ors_sales'] = [signals[d]['pharmacy_ors_sales'] if d in signals else None for d in dates]
    series['pharmacy_fever_sales'] = [signals[d]['pharmacy_fever_sales'] if d in signals else None for d in dates]
    series['school_absent'] = [signals[d]['school_absent'] if d in signals else None for d in dates]
    series['reported_today'] = dates[-1] in signals
    return series


def _evaluate(series, syndrome_key):
    syn = SYNDROMES[syndrome_key]
    streams = {
        syn['clinic_stream']: series[f'clinic_{syndrome_key}'],
        syn['pharmacy_stream']: series[syn['pharmacy_field']],
        'SCHOOL_ABSENTEEISM': series['school_absent'],
    }
    current, history = {}, {}
    for name, values in streams.items():
        today_val = values[-1]
        past = [v for v in values[:-1] if v is not None][-14:]
        if today_val is None or len(past) < BASELINE_MIN_DAYS:
            continue
        current[name] = today_val
        history[name] = past
    if not current:
        return None
    result = surveillance_engine.evaluate_village_day(village_id='-', eval_date=datetime.now(), current_signals=current,
                                                       historical_signals=history, syndrome=syndrome_key)
    risk = result.risk_level
    # Real village counts are sparse (0 cases for weeks, then 2), which inflates z-scores.
    # Only raise WARNING/OUTBREAK when the rise is corroborated by a second signal or is large in absolute terms.
    rising_streams = [k for k, z in result.contributing_streams.items() if z >= CORROBORATION_Z]
    corroborated = len(rising_streams) >= 2 or (result.observed_cases - result.expected_baseline) >= MIN_ABSOLUTE_EXCESS
    if risk in ('WARNING', 'OUTBREAK') and not corroborated:
        risk = 'WATCH'
    return {'risk_level': risk, 'z_score': result.z_score, 'confidence': result.confidence,
            'observed': result.observed_cases, 'expected': result.expected_baseline,
            'rising_streams': rising_streams, 'corroborated': corroborated,
            'streams': {k: round(v, 2) for k, v in result.contributing_streams.items()}}


def _clusters(flagged):
    """Group flagged villages that are within CLUSTER_KM of each other (single-linkage)."""
    groups = []
    for v in flagged:
        joined = None
        for g in groups:
            if any(v['lat'] is not None and o['lat'] is not None and
                   hospital_finder.distance_km(v['lat'], v['lon'], o['lat'], o['lon']) <= CLUSTER_KM for o in g):
                if joined is None:
                    g.append(v)
                    joined = g
                else:
                    joined.extend(g)
                    g.clear()
        if joined is None:
            groups.append([v])
    return [g for g in groups if g]


def evaluate_surveillance():
    start = datetime.now() - timedelta(days=SURVEILLANCE_DAYS - 1)
    villages = db.query('SELECT * FROM villages ORDER BY name')
    out = []
    flagged = {k: [] for k in SYNDROMES}
    for v in villages:
        series = _daily_series(v['id'], start, SURVEILLANCE_DAYS)
        evaluations = {k: _evaluate(series, k) for k in SYNDROMES}
        reported = zip(series['pharmacy_ors_sales'], series['pharmacy_fever_sales'], series['school_absent'])
        baseline_days = sum(1 for day in list(reported)[:-1] if any(x is not None for x in day))
        entry = {**v, 'series': series, 'evaluations': evaluations, 'baseline_days': baseline_days,
                 'risk_level': 'NO_BASELINE'}
        levels = [e['risk_level'] for e in evaluations.values() if e]
        if levels:
            entry['risk_level'] = min(levels, key=lambda l: {'OUTBREAK': 0, 'WARNING': 1, 'WATCH': 2, 'NORMAL': 3}[l])
        for k, e in evaluations.items():
            if e and e['risk_level'] in ('WARNING', 'OUTBREAK'):
                flagged[k].append({'id': v['id'], 'name': v['name'], 'lat': v['lat'], 'lon': v['lon'], **e})
        out.append(entry)

    today = db.today()
    for syndrome_key, items in flagged.items():
        for group in _clusters(items):
            ids = sorted(g['id'] for g in group)
            alert_id = f"ALT-{today.replace('-', '')}-{syndrome_key[:4]}-{generate_pseudonym('|'.join(ids))[:6].upper()}"
            details = {
                'label': SYNDROMES[syndrome_key]['label'],
                'villages': [{'id': g['id'], 'name': g['name'], 'z_score': g['z_score'], 'risk_level': g['risk_level']} for g in group],
                'z_score': round(sum(g['z_score'] for g in group) / len(group), 2),
                'confidence': max(g['confidence'] for g in group),
                'observed': sum(g['observed'] for g in group),
                'expected': sum(g['expected'] for g in group),
                'interventions': SYNDROMES[syndrome_key]['interventions'],
            }
            existing = db.query_one('SELECT id FROM alerts WHERE id = ?', (alert_id,))
            if existing:
                db.execute('UPDATE alerts SET details = ? WHERE id = ?', (db.dumps(details), alert_id))
            else:
                db.execute("INSERT INTO alerts (id, date, syndrome, village_ids, details, status, created_at) VALUES (?,?,?,?,?,'ACTIVE',?)",
                           (alert_id, today, syndrome_key, db.dumps(ids), db.dumps(details), db.now()))
                db.audit('Syndromic Surveillance Agent', 'SYSTEM', 'OUTBREAK_ALERT_RAISED',
                         {'alert_id': alert_id, 'syndrome': syndrome_key, 'villages': [g['name'] for g in group],
                          'z_score': details['z_score']})
    return out


def surveillance_block():
    villages = evaluate_surveillance()
    since = (datetime.now() - timedelta(days=14)).strftime('%Y-%m-%d')
    alerts = db.query("SELECT * FROM alerts WHERE date >= ? AND status != 'DELETED' ORDER BY created_at DESC", (since,))
    for a in alerts:
        a['details'] = db.loads(a['details'], {})
        a['village_ids'] = db.loads(a['village_ids'], [])
        if a['ack_by']:
            officer = db.query_one('SELECT name_enc FROM users WHERE id = ?', (a['ack_by'],))
            a['ack_by_name'] = auth.decrypt(officer['name_enc']) if officer else a['ack_by']
    reporting = sum(1 for v in villages if v['series']['reported_today'])
    return {'villages': villages, 'alerts': alerts, 'reporting_today': reporting,
            'baseline_min_days': BASELINE_MIN_DAYS, 'syndromes': {k: v['label'] for k, v in SYNDROMES.items()}}


# ================= DELETION / ERASURE =================
def erase_patient(patient_id, user):
    """Wipes a patient's identity and all health data. The audit log keeps only the pseudonym."""
    row = patient_row(patient_id)
    if user['role'] == 'HEALTH_WORKER' and row['village_id'] != user['village_id']:
        raise ApiError(403, 'This patient is not in your village.')
    with db.transaction() as conn:
        for table in ('vitals', 'doses', 'chat_messages', 'reports', 'referrals', 'encounters', 'escalations'):
            conn.execute(f'DELETE FROM {table} WHERE patient_id = ?', (patient_id,))
        conn.execute('DELETE FROM sessions WHERE user_id = ?', (patient_id,))
        conn.execute('DELETE FROM patients WHERE user_id = ?', (patient_id,))
        conn.execute("UPDATE users SET status = 'ERASED', name_enc = ?, mobile_enc = ?, mobile_hash = ?, password_hash = NULL, "
                     'activation_hash = NULL, activation_expires = NULL WHERE id = ?',
                     (encrypt_pii(''), encrypt_pii(''), f'ERASED-{patient_id}', patient_id))
    db.audit(user['id'], user['role'], 'PATIENT_RECORD_ERASED', {'patient': row['pseudonym'], 'village_id': row['village_id']})
    return {'ok': True}


def remove_asha(asha_id, user, own_account=False):
    """Closes an ASHA account (she left the job). Her patients move to another ASHA of the village, if there is one."""
    asha = db.query_one("SELECT * FROM users WHERE id = ? AND role = 'HEALTH_WORKER' AND status != 'ERASED'", (asha_id,))
    if not asha:
        raise ApiError(404, 'ASHA account not found.')
    successor = db.query_one("SELECT id FROM users WHERE role = 'HEALTH_WORKER' AND status = 'ACTIVE' AND village_id = ? AND id != ? "
                             'ORDER BY created_at LIMIT 1', (asha['village_id'], asha_id))
    new_owner = successor['id'] if successor else None
    patients = db.query_one('SELECT count(*) AS n FROM patients WHERE asha_id = ?', (asha_id,))['n']
    with db.transaction() as conn:
        conn.execute('UPDATE patients SET asha_id = ? WHERE asha_id = ?', (new_owner, asha_id))
        conn.execute('DELETE FROM sessions WHERE user_id = ?', (asha_id,))
        conn.execute("UPDATE users SET status = 'ERASED', name_enc = ?, mobile_enc = ?, mobile_hash = ?, password_hash = NULL WHERE id = ?",
                     (encrypt_pii(''), encrypt_pii(''), f'ERASED-{asha_id}', asha_id))
    db.audit(user['id'], user['role'], 'ASHA_ACCOUNT_REMOVED',
             {'asha': asha_id, 'village_id': asha['village_id'], 'own_account': own_account, 'patients': patients,
              'patients_moved_to': new_owner})
    return {'ok': True, 'patients': patients, 'moved_to_another_asha': bool(new_owner)}


# ================= ROUTER =================
def _bearer(headers):
    value = headers.get('Authorization') or ''
    return value[7:].strip() if value.startswith('Bearer ') else None


def handle(method, path, query, body, headers):
    if not path.startswith('/api/v1/'):
        return None
    try:
        result = _dispatch(method, path, query, body or {}, headers)
        if result is None:
            return 404, {'error': f'Route not found: {method} {path}'}
        return result if isinstance(result, tuple) else (200, result)
    except (ApiError, AuthError) as e:
        return e.status, {'error': str(e)}


def _dispatch(method, path, query, body, headers):
    token = _bearer(headers)

    # ---------- public ----------
    if method == 'GET' and path == '/api/v1/health':
        return {'status': 'healthy', 'service': 'ArogyaSaathi', 'chat_configured': bool(patient_chat.config.ANTHROPIC_API_KEY),
                'staff_signup_enabled': bool(auth.config.STAFF_SIGNUP_CODE)}
    if method == 'GET' and path == '/api/v1/public/villages':
        return db.query('SELECT id, name, block, district, state FROM villages ORDER BY district, name')
    if method == 'POST' and path == '/api/v1/auth/login':
        token, user = auth.login(body.get('role'), body.get('mobile'), body.get('password'))
        return {'token': token, 'user': auth.public_user(user)}
    if method == 'POST' and path == '/api/v1/auth/signup':
        token, user = auth.staff_signup(body)
        return 201, {'token': token, 'user': auth.public_user(user)}
    if method == 'POST' and path == '/api/v1/auth/activate':
        token, user = auth.activate_patient(body.get('mobile'), body.get('code'), body.get('password'))
        return {'token': token, 'user': auth.public_user(user)}

    user = auth.user_from_token(token)
    require(user)

    if method == 'GET' and path == '/api/v1/auth/me':
        return auth.public_user(user)
    if method == 'POST' and path == '/api/v1/auth/logout':
        auth.logout(token)
        return {'ok': True}

    # ---------- patient ----------
    if path.startswith('/api/v1/me/'):
        require(user, 'PATIENT')
        if method == 'GET' and path == '/api/v1/me/dashboard':
            return patient_dashboard(user)
        if method == 'POST' and path == '/api/v1/me/vitals':
            record_vitals(user['id'], body, 'SELF', user)
            p, esc_id = reevaluate_chronic(user['id'], *actor(user))
            return {'patient': p, 'alerted_health_team': bool(esc_id)}
        if method == 'POST' and path == '/api/v1/me/dose':
            record_dose(user['id'], body.get('status'), user)
            p, esc_id = reevaluate_chronic(user['id'], *actor(user))
            return {'patient': p, 'alerted_health_team': bool(esc_id)}
        if method == 'POST' and path == '/api/v1/me/language':
            db.execute('UPDATE patients SET language = ? WHERE user_id = ?', (lang_of(body.get('language')), user['id']))
            return {'ok': True}
        if method == 'GET' and path == '/api/v1/me/chat':
            return db.query('SELECT role, content, language, flagged, created_at FROM chat_messages WHERE patient_id = ? '
                            'ORDER BY id DESC LIMIT 40', (user['id'],))[::-1]
        if method == 'POST' and path == '/api/v1/me/chat':
            return patient_chat_reply(user, body)
        m = re.fullmatch(r'/api/v1/me/reports/([A-Z0-9-]+)/read', path)
        if method == 'POST' and m:
            db.execute('UPDATE reports SET read_at = ? WHERE id = ? AND patient_id = ? AND read_at IS NULL', (db.now(), m.group(1), user['id']))
            return {'ok': True}
        return None

    # ---------- health worker ----------
    if path.startswith('/api/v1/worker/') or path.startswith('/api/v1/triage/') or path in (
            '/api/v1/hospitals', '/api/v1/referrals', '/api/v1/signals'):
        require(user, 'HEALTH_WORKER')
        if method == 'GET' and path == '/api/v1/worker/patients':
            rows = db.query("SELECT p.*, u.name_enc, u.mobile_enc, u.status FROM patients p JOIN users u ON u.id = p.user_id "
                            "WHERE p.village_id = ? AND u.status != 'ERASED' ORDER BY p.created_at DESC", (user['village_id'],))
            patients = [patient_summary(r, include_identity=True) for r in rows]
            patients.sort(key=lambda p: (RISK_ORDER.get(p['risk']['risk_level'], 9), -(p['risk'].get('systolic_slope_per_week') or 0)))
            return {'patients': patients, 'conditions': CONDITIONS, 'village': village(user['village_id'])}
        if method == 'POST' and path == '/api/v1/worker/patients':
            return 201, register_patient(user, body)
        m = re.fullmatch(r'/api/v1/worker/patients/([A-Z0-9-]+)/delete', path)
        if method == 'POST' and m:
            return erase_patient(m.group(1), user)
        m = re.fullmatch(r'/api/v1/worker/referrals/([A-Z0-9-]+)/delete', path)
        if method == 'POST' and m:
            ref = db.query_one('SELECT id, pseudonym FROM referrals WHERE id = ? AND village_id = ?', (m.group(1), user['village_id']))
            if not ref:
                raise ApiError(404, 'Referral not found.')
            db.execute('DELETE FROM referrals WHERE id = ?', (ref['id'],))
            db.audit(user['id'], 'HEALTH_WORKER', 'REFERRAL_DELETED', {'referral_id': ref['id'], 'patient': ref['pseudonym']})
            return {'ok': True}
        m = re.fullmatch(r'/api/v1/worker/signals/(\d+)/delete', path)
        if method == 'POST' and m:
            sig = db.query_one('SELECT id, date FROM signals WHERE id = ? AND village_id = ?', (int(m.group(1)), user['village_id']))
            if not sig:
                raise ApiError(404, 'Report not found.')
            db.execute('DELETE FROM signals WHERE id = ?', (sig['id'],))
            db.audit(user['id'], 'HEALTH_WORKER', 'DAILY_REPORT_DELETED', {'village_id': user['village_id'], 'date': sig['date']})
            return {'ok': True}
        if method == 'POST' and path == '/api/v1/worker/account/delete':
            if not auth.verify_password(str(body.get('password') or ''), user['password_hash'] or ''):
                raise ApiError(403, 'Wrong password. Your account was not deleted.')
            auth.logout(token)
            return remove_asha(user['id'], user, own_account=True)
        m = re.fullmatch(r'/api/v1/worker/patients/([A-Z0-9-]+)/(checkin|activation-code)', path)
        if method == 'POST' and m:
            if m.group(2) == 'checkin':
                return worker_checkin(user, m.group(1), body)
            row = worker_patient(user, m.group(1))
            if row['status'] == 'ACTIVE':
                raise ApiError(409, 'This patient has already activated their account.')
            code = auth.issue_activation_code(row['user_id'])
            db.audit(user['id'], 'HEALTH_WORKER', 'ACTIVATION_CODE_ISSUED', {'patient': row['pseudonym']})
            return {'activation_code': code, 'activation_hours': auth.config.ACTIVATION_HOURS}
        if method == 'GET' and path == '/api/v1/worker/referrals':
            rows = db.query('SELECT * FROM referrals WHERE village_id = ? ORDER BY created_at DESC LIMIT 50', (user['village_id'],))
            for r in rows:
                r['hospital'] = db.loads(r['hospital'], {})
            return rows
        if method == 'GET' and path == '/api/v1/worker/signals':
            since = (datetime.now() - timedelta(days=14)).strftime('%Y-%m-%d')
            return db.query('SELECT * FROM signals WHERE village_id = ? AND date >= ? ORDER BY date DESC', (user['village_id'], since))
        if method == 'POST' and path == '/api/v1/triage/sessions':
            return 201, start_triage(user, body)
        m = re.fullmatch(r'/api/v1/triage/sessions/([A-Z0-9-]+)/turn', path)
        if method == 'POST' and m:
            return triage_turn(user, m.group(1), body)
        if method == 'GET' and path == '/api/v1/hospitals':
            lat = to_float(query.get('lat'), -90, 90, 'Latitude')
            lon = to_float(query.get('lon'), -180, 180, 'Longitude')
            if lat is None or lon is None:
                v = village(user['village_id'])
                lat, lon = (v['lat'], v['lon']) if v else (None, None)
            if lat is None or lon is None:
                raise ApiError(400, 'Location needed. Allow location access, or add GPS to your village.')
            try:
                return hospital_finder.find_government_facilities(lat, lon, to_int(query.get('radius'), 5, 60, 'Radius') or 25)
            except Exception:
                raise ApiError(502, 'Could not reach the map service. Check internet, or enter the hospital manually.')
        if method == 'POST' and path == '/api/v1/referrals':
            return 201, create_referral(user, body)
        if method == 'POST' and path == '/api/v1/signals':
            date = body.get('date') or db.today()
            if not re.fullmatch(r'\d{4}-\d{2}-\d{2}', date) or date > db.today():
                raise ApiError(400, 'Choose a valid date (not in the future).')
            vals = {k: to_int(body.get(k), 0, 100000, k.replace('_', ' ')) for k in
                    ('pharmacy_ors_sales', 'pharmacy_fever_sales', 'school_absent', 'school_enrolled')}
            if all(v is None for v in vals.values()):
                raise ApiError(400, 'Enter at least one count.')
            if vals['school_absent'] is not None and vals['school_enrolled'] and vals['school_absent'] > vals['school_enrolled']:
                raise ApiError(400, 'Students absent cannot be more than students enrolled.')
            db.execute('INSERT INTO signals (village_id, date, pharmacy_ors_sales, pharmacy_fever_sales, school_absent, school_enrolled, reported_by, created_at) '
                       'VALUES (?,?,?,?,?,?,?,?) ON CONFLICT (village_id, date) DO UPDATE SET pharmacy_ors_sales = excluded.pharmacy_ors_sales, '
                       'pharmacy_fever_sales = excluded.pharmacy_fever_sales, school_absent = excluded.school_absent, '
                       'school_enrolled = excluded.school_enrolled, reported_by = excluded.reported_by, created_at = excluded.created_at',
                       (user['village_id'], date, vals['pharmacy_ors_sales'], vals['pharmacy_fever_sales'], vals['school_absent'],
                        vals['school_enrolled'], user['id'], db.now()))
            db.audit(user['id'], 'HEALTH_WORKER', 'SIGNALS_REPORTED', {'village_id': user['village_id'], 'date': date, **vals})
            evaluate_surveillance()
            return {'ok': True}
        return None

    # ---------- doctor ----------
    if path.startswith('/api/v1/escalations') or path.startswith('/api/v1/doctor/'):
        require(user, 'DOCTOR')
        if method == 'GET' and path == '/api/v1/escalations':
            rows = db.query('SELECT * FROM escalations ORDER BY created_at DESC LIMIT 200')
            for r in rows:
                r['details'] = db.loads(r['details'], {})
                r['review'] = db.loads(r['review'])
                r['village_name'] = village_name(r['village_id'])
                named = db.query_one('SELECT name_enc FROM users WHERE id = ?', (r['patient_id'],)) if r['patient_id'] else None
                r['patient_name'] = auth.decrypt(named['name_enc']) if named else ''
            return rows
        m = re.fullmatch(r'/api/v1/escalations/([A-Z0-9-]+)/review', path)
        if method == 'POST' and m:
            esc = db.query_one('SELECT * FROM escalations WHERE id = ?', (m.group(1),))
            if not esc:
                raise ApiError(404, 'Escalation not found.')
            if esc['status'] == 'REVIEWED':
                raise ApiError(409, 'Already reviewed.')
            decision = 'OVERRIDE' if body.get('decision') == 'OVERRIDE' else 'AGREE'
            final_level = body.get('final_level') if decision == 'OVERRIDE' else esc['level']
            review = {'decision': decision, 'final_level': final_level, 'note': (body.get('note') or '').strip()[:1000],
                      'reviewer': user['id'], 'reviewer_name': auth.decrypt(user['name_enc']), 'reviewed_at': db.now(),
                      'label_for_training': {'system_level': esc['level'], 'clinician_level': final_level,
                                             'agreement': decision == 'AGREE'}}
            db.execute("UPDATE escalations SET status = 'REVIEWED', review = ? WHERE id = ?", (db.dumps(review), esc['id']))
            db.audit(user['id'], 'DOCTOR', 'HUMAN_OVERRIDE' if decision == 'OVERRIDE' else 'CLINICIAN_REVIEW',
                     {'escalation_id': esc['id'], 'system_level': esc['level'], 'final_level': final_level, 'note': review['note']})
            return {'ok': True}
        m = re.fullmatch(r'/api/v1/doctor/patients/([A-Z0-9-]+)/delete', path)
        if method == 'POST' and m:
            return erase_patient(m.group(1), user)
        m = re.fullmatch(r'/api/v1/escalations/([A-Z0-9-]+)/delete', path)
        if method == 'POST' and m:
            esc = db.query_one('SELECT id, status, pseudonym FROM escalations WHERE id = ?', (m.group(1),))
            if not esc:
                raise ApiError(404, 'Escalation not found.')
            if esc['status'] != 'REVIEWED':
                raise ApiError(409, 'Review this case first. Pending cases cannot be deleted.')
            db.execute('DELETE FROM escalations WHERE id = ?', (esc['id'],))
            db.audit(user['id'], 'DOCTOR', 'ESCALATION_DELETED', {'escalation_id': esc['id'], 'patient': esc['pseudonym']})
            return {'ok': True}
        if method == 'GET' and path == '/api/v1/doctor/patients':
            rows = db.query("SELECT p.*, u.name_enc, u.mobile_enc, u.status FROM patients p JOIN users u ON u.id = p.user_id "
                            "WHERE u.status != 'ERASED'")
            patients = [patient_summary(r, include_identity=False) | {'name': auth.decrypt(r['name_enc'])} for r in rows]
            patients.sort(key=lambda p: RISK_ORDER.get(p['risk']['risk_level'], 9))
            return patients
        if method == 'POST' and path == '/api/v1/doctor/reports':
            row = patient_row(body.get('patient_id'))
            title = (body.get('title') or '').strip()
            summary = (body.get('summary') or '').strip()
            if not title or not summary:
                raise ApiError(400, 'Enter a title and your note for the patient.')
            rep_id = f"RPT-{auth.new_id('X')[2:]}"
            db.execute('INSERT INTO reports (id, patient_id, doctor_id, title, category, status, summary, created_at) VALUES (?,?,?,?,?,?,?,?)',
                       (rep_id, row['user_id'], user['id'], title[:200], (body.get('category') or 'Advice')[:60],
                        (body.get('status') or '')[:60], summary[:4000], db.now()))
            db.audit(user['id'], 'DOCTOR', 'REPORT_SENT', {'report_id': rep_id, 'patient': row['pseudonym'], 'title': title})
            return 201, {'id': rep_id}
        return None

    # ---------- officer ----------
    if path.startswith('/api/v1/officer/'):
        require(user, 'HEALTH_OFFICER')
        if method == 'GET' and path == '/api/v1/officer/staff':
            rows = db.query("SELECT * FROM users WHERE role = 'HEALTH_WORKER' AND status != 'ERASED' ORDER BY created_at")
            return [{'id': r['id'], 'name': auth.decrypt(r['name_enc']), 'mobile_last4': auth.decrypt(r['mobile_enc'])[-4:],
                     'village_name': village_name(r['village_id']), 'created_at': r['created_at'],
                     'patients': db.query_one('SELECT count(*) AS n FROM patients WHERE village_id = ?', (r['village_id'],))['n']}
                    for r in rows]
        m = re.fullmatch(r'/api/v1/officer/staff/([A-Z0-9-]+)/delete', path)
        if method == 'POST' and m:
            return remove_asha(m.group(1), user)
        return None
    if path.startswith('/api/v1/surveillance/'):
        require(user, 'HEALTH_OFFICER')
        if method == 'GET' and path == '/api/v1/surveillance/block':
            return surveillance_block()
        m = re.fullmatch(r'/api/v1/surveillance/alerts/([A-Za-z0-9-]+)/delete', path)
        if method == 'POST' and m:
            alert = db.query_one("SELECT id FROM alerts WHERE id = ? AND status != 'DELETED'", (m.group(1),))
            if not alert:
                raise ApiError(404, 'Alert not found.')
            db.execute("UPDATE alerts SET status = 'DELETED' WHERE id = ?", (alert['id'],))
            db.audit(user['id'], 'HEALTH_OFFICER', 'OUTBREAK_ALERT_DELETED', {'alert_id': alert['id']})
            return {'ok': True}
        m = re.fullmatch(r'/api/v1/surveillance/alerts/([A-Za-z0-9-]+)/ack', path)
        if method == 'POST' and m:
            alert = db.query_one('SELECT * FROM alerts WHERE id = ?', (m.group(1),))
            if not alert:
                raise ApiError(404, 'Alert not found.')
            note = (body.get('note') or '').strip()[:1000]
            db.execute("UPDATE alerts SET status = 'ACKNOWLEDGED', ack_by = ?, ack_note = ?, ack_at = ? WHERE id = ?",
                       (user['id'], note, db.now(), alert['id']))
            db.audit(user['id'], 'HEALTH_OFFICER', 'OUTBREAK_ALERT_ACKNOWLEDGED', {'alert_id': alert['id'], 'note': note})
            return {'ok': True}
        return None

    # ---------- shared ----------
    if method == 'GET' and path == '/api/v1/audit':
        require(user, 'DOCTOR', 'HEALTH_OFFICER')
        ok, broken_at = db.verify_audit_chain()
        entries = db.query('SELECT * FROM audit_log ORDER BY seq DESC LIMIT 300')
        for e in entries:
            e['details'] = db.loads(e['details'], {})
        return {'chain_valid': ok, 'broken_at_seq': broken_at, 'entries': entries}
    if method == 'GET' and path == '/api/v1/villages':
        return db.query('SELECT * FROM villages ORDER BY name')
    return None
