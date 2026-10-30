"""
ArogyaSaathi Staff Portal API (Health Worker, Doctor, Health Officer).
In-memory demo state served by local_server.py. Every decision is written to a
hash-chained audit log so tampering with any earlier entry breaks verification.
"""

import hashlib
import json
import os
import random
import re
import time
import urllib.parse
from datetime import datetime, timedelta

from app.core.security import generate_pseudonym
from app.services.chronic_care import chronic_care_engine
from app.services.geo_clustering import VILLAGE_GEOMETRIES
from app.services.langgraph_triage import orchestrator
from app.services.surveillance_engine import surveillance_engine
from app.services.synthetic_cohort import SyntheticCohortBenchmark
from app.services.synthetic_outbreak import SyntheticOutbreakBenchmark
from app.services.voice_checkin import VoiceCheckinParser

# Simulated "today" inside the 30-day chronic cohort and 60-day surveillance stream
COHORT_TODAY = 21
SURVEILLANCE_TODAY = 30

# ================= AUDIT TRAIL (tamper-evident hash chain) =================
AUDIT_LOG = []


def _hash_entry(entry):
    payload = json.dumps({k: entry[k] for k in ('seq', 'ts', 'actor', 'role', 'event', 'details', 'prev_hash')},
                         sort_keys=True, default=str)
    return hashlib.sha256(payload.encode('utf-8')).hexdigest()


def audit(actor, role, event, details):
    prev_hash = AUDIT_LOG[-1]['hash'] if AUDIT_LOG else '0' * 64
    entry = {
        'seq': len(AUDIT_LOG) + 1,
        'ts': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'actor': actor,
        'role': role,
        'event': event,
        'details': json.loads(json.dumps(details, default=str)),
        'prev_hash': prev_hash,
    }
    entry['hash'] = _hash_entry(entry)
    AUDIT_LOG.append(entry)
    return entry


def verify_audit_chain():
    prev = '0' * 64
    for entry in AUDIT_LOG:
        if entry['prev_hash'] != prev or _hash_entry(entry) != entry['hash']:
            return False, entry['seq']
        prev = entry['hash']
    return True, None


# ================= VILLAGES =================
def village_name(village_id):
    geo = VILLAGE_GEOMETRIES.get(village_id)
    return geo['name'] if geo else village_id


# ================= CHRONIC CARE ROSTER =================
ROSTER_SEED = [
    # name, age, gender, village, condition, deteriorating, deterioration_start_day
    ('Ramesh Kumar', 58, 'M', 'VILL-UP-RAMPUR-01', 'Hypertension + Diabetes', True, 10),
    ('Sunita Devi', 52, 'F', 'VILL-UP-RAMPUR-01', 'Hypertension', True, 14),
    ('Mohan Lal', 64, 'M', 'VILL-UP-SHIVPUR-02', 'Diabetes', False, 0),
    ('Kamla Bai', 61, 'F', 'VILL-UP-KALYANPUR-03', 'Hypertension', False, 0),
    ('Rajendra Singh', 49, 'M', 'VILL-UP-SITAPUR-04', 'Hypertension + Diabetes', False, 0),
    ('Geeta Yadav', 55, 'F', 'VILL-UP-BHARATPUR-05', 'Diabetes', True, 16),
]

ROSTER = {}


def _evaluate_patient(p):
    risk = chronic_care_engine.evaluate_patient_deterioration(
        p['_vitals'], p['_adherence'], p['_next_visit'], p['_today'])
    p['risk'] = risk.dict()
    recent = p['_vitals'][-14:]
    recent_adh = p['_adherence'][-14:]
    p['trend'] = {
        'days': [v['recorded_at'].strftime('%d %b') for v in recent],
        'systolic': [v.get('systolic_bp') for v in recent],
        'diastolic': [v.get('diastolic_bp') for v in recent],
        'glucose': [v.get('blood_glucose') for v in recent],
        'doses': [a['status'] for a in recent_adh],
    }
    last = p['_vitals'][-1]
    p['latest'] = {
        'bp': f"{last.get('systolic_bp')}/{last.get('diastolic_bp')}",
        'glucose': last.get('blood_glucose'),
        'date': last['recorded_at'].strftime('%d %b'),
    }
    p['next_visit'] = p['_next_visit'].strftime('%d %b %Y')
    p['days_to_visit'] = (p['_next_visit'] - p['_today']).days


def _public_patient(p):
    return {k: v for k, v in p.items() if not k.startswith('_')}


def _seed_roster():
    random.seed(11)
    for i, (name, age, gender, village, condition, det, start) in enumerate(ROSTER_SEED, start=1):
        pid = f'PAT-{i:03d}'
        vitals, adherence, base, visit = SyntheticCohortBenchmark.generate_patient_history(
            pid, is_deteriorating=det, deterioration_start_day=start or 14, total_days=30)
        # Shift the synthetic calendar so the cohort's "today" is the real date
        shift = datetime.now().replace(hour=9, minute=0, second=0, microsecond=0) - (base + timedelta(days=COHORT_TODAY))
        base, visit = base + shift, visit + shift
        for v in vitals:
            v['recorded_at'] += shift
        for a in adherence:
            a['scheduled_time'] += shift
        if 'Hypertension' not in condition:
            for v in vitals:
                v['blood_glucose'] = round(v['blood_glucose'] + (45 if det else 30), 1)
        p = {
            'id': pid,
            'name': name,
            'pseudonym': f"HASH-{village.split('-')[2]}-{generate_pseudonym(f'{name}:{pid}')[7:11]}",
            'age': age,
            'gender': gender,
            'village_id': village,
            'village_name': village_name(village),
            'condition': condition,
            'consent': {'data_use': True, 'sharing': True, 'deletion_rights_explained': True},
            '_vitals': vitals[:COHORT_TODAY],
            '_adherence': adherence[:COHORT_TODAY],
            '_next_visit': visit,
            '_today': base + timedelta(days=COHORT_TODAY),
        }
        _evaluate_patient(p)
        ROSTER[pid] = p


# ================= ESCALATIONS (doctor queue) =================
ESCALATIONS = []


def _create_escalation(source, level, patient, title, rationale, details):
    esc = {
        'id': f"ESC-{len(ESCALATIONS) + 1:04d}",
        'created_at': datetime.now().strftime('%d %b %Y, %I:%M %p'),
        'source': source,                 # TRIAGE | CHRONIC
        'level': level,                   # EMERGENCY | REFER | CRITICAL | HIGH
        'status': 'PENDING',
        'patient': patient,
        'title': title,
        'rationale': rationale,
        'review': None,
        **details,
    }
    ESCALATIONS.insert(0, esc)
    return esc


def _chronic_escalation_summary(p):
    r = p['risk']
    lines = [
        f"# Chronic Care Deterioration Summary - {p['pseudonym']}",
        '',
        f"**Patient:** {p['age']} yrs / {p['gender']} | **Village:** {p['village_name']} | **Condition:** {p['condition']}",
        f"**Risk level:** {r['risk_level']} | **Next scheduled visit:** {p['next_visit']} ({p['days_to_visit']} days away)",
        '',
        '## Trend (last 14 days)',
        f"- Average BP: {r['average_systolic']}/{r['average_diastolic']} mmHg (systolic slope {r['systolic_slope_per_week']} mmHg/week)",
        f"- Average fasting glucose: {r['average_glucose']} mg/dL",
        f"- Medication adherence: {r['adherence_rate_pct']}%",
        '',
        '## Flags raised',
    ]
    lines += [f"- {f.replace('_', ' ').title()}" for f in r['flags']] or ['- None']
    lines += ['', '## Recommended action (for clinician review)', r['recommended_action'], '',
              '_Generated by rule-based trend analysis. No diagnosis or prescription is made by the system._']
    return '\n'.join(lines)


def _escalate_chronic(p, actor='Chronic Care Agent', role='SYSTEM'):
    if p['risk']['risk_level'] not in ('HIGH', 'CRITICAL'):
        return None
    for e in ESCALATIONS:
        if e['source'] == 'CHRONIC' and e['patient']['id'] == p['id'] and e['status'] == 'PENDING':
            return None
    esc = _create_escalation(
        'CHRONIC', p['risk']['risk_level'],
        {'id': p['id'], 'pseudonym': p['pseudonym'], 'age': p['age'], 'gender': p['gender'],
         'village_name': p['village_name']},
        f"{p['condition']}: deterioration flagged {p['days_to_visit']} days before visit",
        p['risk']['recommended_action'],
        {'summary_markdown': _chronic_escalation_summary(p), 'flags': p['risk']['flags'],
         'trend': p['trend'], 'citations': ['JNC-8 / RSSDI chronic care thresholds (rule-based)']})
    audit(actor, role, 'ESCALATION_CREATED', {'escalation_id': esc['id'], 'patient': p['pseudonym'],
                                              'level': esc['level'], 'flags': p['risk']['flags']})
    return esc


# ================= SURVEILLANCE =================
SURVEILLANCE = {}


def _seed_surveillance():
    streams = SyntheticOutbreakBenchmark.generate_block_60day_stream(outbreak_start_day=25)
    benchmark = SyntheticOutbreakBenchmark.run_objective_o4_benchmark(outbreak_injection_day=25)
    base_date = datetime.now() - timedelta(days=SURVEILLANCE_TODAY - 1)
    day_labels = [(base_date + timedelta(days=d)).strftime('%d %b') for d in range(SURVEILLANCE_TODAY)]

    villages = []
    for vid, geo in VILLAGE_GEOMETRIES.items():
        s = streams[vid]
        day = SURVEILLANCE_TODAY
        evaluation = surveillance_engine.evaluate_village_day(
            village_id=vid,
            eval_date=base_date + timedelta(days=day - 1),
            current_signals={k: s[k][day - 1] for k in s},
            historical_signals={k: s[k][max(0, day - 15):day - 1] for k in s},
            syndrome='ACUTE_DIARRHEAL_OUTBREAK')
        villages.append({
            'id': vid,
            'name': geo['name'],
            'block': geo['block'],
            'district': geo['district'],
            'center': geo['center'],
            'polygon': geo['polygon_coords'],
            'risk_level': evaluation.risk_level,
            'z_score': round(evaluation.z_score, 2),
            'streams': {
                'clinic_visits': s['ACUTE_DIARRHEA'][:SURVEILLANCE_TODAY],
                'pharmacy_ors_sales': s['PHARMACY_ORS_SALES'][:SURVEILLANCE_TODAY],
                'school_absenteeism': s['SCHOOL_ABSENTEEISM'][:SURVEILLANCE_TODAY],
            },
        })

    alert = benchmark.get('first_outbreak_alert')
    alerts = []
    if alert:
        detected_day = benchmark['arogyasaathi_detected_day']
        alerts.append({
            'id': alert['alert_id'],
            'syndrome': alert['syndrome'],
            'detected_on': day_labels[detected_day - 1] if detected_day else None,
            'baseline_would_detect_on': day_labels[benchmark['conventional_baseline_detected_day'] - 1]
            if benchmark['conventional_baseline_detected_day'] else None,
            'affected_villages': alert['affected_villages'],
            'affected_village_names': [village_name(v) for v in alert['affected_villages']],
            'z_score': round(alert['z_score'], 2),
            'confidence': alert['confidence'],
            'observed_cases': alert['observed_cases'],
            'baseline_expected_cases': alert['baseline_expected_cases'],
            'recommended_interventions': alert['recommended_interventions'],
            'status': 'ACTIVE',
            'acknowledged_by': None,
        })

    SURVEILLANCE.update({
        'day_labels': day_labels,
        'villages': villages,
        'alerts': alerts,
        'benchmark': {k: v for k, v in benchmark.items() if k != 'first_outbreak_alert'},
    })
    for a in alerts:
        audit('Syndromic Surveillance Agent', 'SYSTEM', 'OUTBREAK_ALERT_RAISED',
              {'alert_id': a['id'], 'villages': a['affected_village_names'], 'z_score': a['z_score']})


# ================= TRIAGE =================
TRIAGE_PATIENTS = {}   # session_id -> patient info
LEVEL_LABELS = {
    'EMERGENCY': 'Emergency',
    'REFER': 'Refer',
    'TREAT_LOCALLY': 'Treat locally',
    'HOME_CARE': 'Home care',
}


def _read_summary(url):
    if not url:
        return None
    path = urllib.parse.unquote(url.replace('file://', ''))
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    except OSError:
        return None


def _triage_response(state, info):
    lang = state.language
    uncertain, reason = False, None
    if state.is_final and not state.symptoms:
        uncertain, reason = True, 'No recognised symptoms were extracted. Confirm the complaint and repeat triage or consult the PHC doctor.'
    elif state.is_final and state.triage_level == 'HOME_CARE' and state.symptoms:
        uncertain, reason = True, 'Symptoms present but no protocol matched. Observe closely and re-triage if anything changes.'
    return {
        'session_id': state.session_id,
        'patient': info,
        'language': lang,
        'transcripts': state.all_transcripts,
        'symptoms': state.symptoms,
        'danger_signs': state.danger_signs,
        'is_final': state.is_final,
        'triage_level': state.triage_level,
        'triage_label': LEVEL_LABELS.get(state.triage_level),
        'decision_rationale': state.decision_rationale,
        'next_question': None if state.is_final else (state.next_question_hi if lang == 'hi' else state.next_question_en),
        'next_question_en': state.next_question_en,
        'checklist': state.checklist,
        'protocol_citations': state.protocol_citations,
        'is_red_flag_overridden': state.is_red_flag_overridden,
        'uncertain': uncertain,
        'uncertainty_reason': reason,
        'summary_markdown': _read_summary(state.doctor_summary_url),
        'escalation_id': info.get('escalation_id'),
    }


def start_triage(data):
    consent = data.get('consent') or {}
    if not consent.get('data_use'):
        return 403, {'error': 'Consent for data use is required before triage (consent middleware).'}
    name = (data.get('name') or 'Unnamed patient').strip()
    village = data.get('village_id') or 'VILL-UP-RAMPUR-01'
    age = int(data.get('age') or 30)
    gender = data.get('gender') or 'F'
    pseudonym = data.get('pseudonym') or f"HASH-{village.split('-')[2]}-{generate_pseudonym(f'{name}:{age}')[7:11]}"
    vitals = {k: v for k, v in (data.get('vitals') or {}).items() if v not in (None, '')}
    state = orchestrator.start_session(
        patient_id=data.get('patient_id') or pseudonym, patient_pseudonym=pseudonym, age=age,
        gender=gender, village_id=village, language=data.get('language', 'hi'), vitals=vitals)
    info = {'pseudonym': pseudonym, 'age': age, 'gender': gender, 'village_id': village,
            'village_name': village_name(village), 'escalation_id': None}
    TRIAGE_PATIENTS[state.session_id] = info
    audit(data.get('worker_id', 'ASHA-RAMPUR-7821'), 'HEALTH_WORKER', 'TRIAGE_STARTED',
          {'session_id': state.session_id, 'patient': pseudonym, 'language': state.language, 'vitals': vitals})
    return 201, _triage_response(state, info)


def triage_turn(session_id, data):
    state = orchestrator.get_session(session_id)
    info = TRIAGE_PATIENTS.get(session_id)
    if not state or not info:
        return 404, {'error': f'Triage session {session_id} not found'}
    if state.is_final:
        return 409, {'error': 'Triage already finalised for this session.'}
    text = (data.get('text') or '').strip()
    if not text:
        return 400, {'error': 'Empty input'}
    actor = data.get('worker_id', 'ASHA-RAMPUR-7821')
    audit(actor, 'HEALTH_WORKER', 'TRIAGE_INPUT', {'session_id': session_id, 'text': text})

    started = time.time()
    state = orchestrator.process_turn(session_id, text)

    if state.is_red_flag_overridden:
        audit('Safety Gate', 'SYSTEM', 'RED_FLAG_RULE_FIRED',
              {'session_id': session_id, 'rule': state.protocol_citations[-1] if state.protocol_citations else None,
               'danger_signs': state.danger_signs})
    audit('Triage Agent', 'SYSTEM', 'TRIAGE_DECISION' if state.is_final else 'TRIAGE_QUESTION',
          {'session_id': session_id, 'symptoms': state.symptoms, 'triage_level': state.triage_level,
           'next_question': None if state.is_final else state.next_question_en})

    if state.is_final and state.triage_level in ('EMERGENCY', 'REFER'):
        resp = _triage_response(state, info)
        esc = _create_escalation(
            'TRIAGE', state.triage_level,
            {'id': info['pseudonym'], 'pseudonym': info['pseudonym'], 'age': info['age'],
             'gender': info['gender'], 'village_name': info['village_name']},
            f"Voice triage: {', '.join(s.replace('_', ' ') for s in state.symptoms) or 'complaint'}",
            state.decision_rationale,
            {'summary_markdown': resp['summary_markdown'], 'flags': state.danger_signs,
             'citations': state.protocol_citations, 'transcripts': state.all_transcripts,
             'summary_seconds': round(time.time() - started, 2)})
        info['escalation_id'] = esc['id']
        audit('Referral Generator', 'SYSTEM', 'ESCALATION_CREATED',
              {'escalation_id': esc['id'], 'session_id': session_id, 'level': esc['level']})
    return 200, _triage_response(state, info)


# ================= ROUTER =================
def _json(status, data):
    return status, json.loads(json.dumps(data, default=str))


def handle(method, path, data):
    """Returns (status, payload) for staff routes, or None if the path is not a staff route."""
    if method == 'GET':
        if path == '/api/v1/villages':
            return _json(200, [{'id': k, 'name': v['name'], 'block': v['block']} for k, v in VILLAGE_GEOMETRIES.items()])
        if path == '/api/v1/worker/roster':
            patients = sorted(ROSTER.values(), key=lambda p: (p['risk']['action_priority'], -p['risk']['systolic_slope_per_week']))
            return _json(200, [_public_patient(p) for p in patients])
        if path == '/api/v1/escalations':
            return _json(200, ESCALATIONS)
        if path == '/api/v1/surveillance/block':
            return _json(200, SURVEILLANCE)
        if path == '/api/v1/audit':
            ok, broken_at = verify_audit_chain()
            return _json(200, {'chain_valid': ok, 'broken_at_seq': broken_at, 'entries': list(reversed(AUDIT_LOG))})
        return None

    if method != 'POST':
        return None

    if path == '/api/v1/worker/register':
        consent = data.get('consent') or {}
        if not consent.get('data_use'):
            return _json(403, {'error': 'Patient must give voice consent for data use to register.'})
        name = (data.get('name') or '').strip()
        phone = (data.get('phone') or '').strip()
        village = data.get('village_id') or 'VILL-UP-RAMPUR-01'
        pseudonym = f"HASH-{village.split('-')[2]}-{generate_pseudonym(f'{name}:{phone}')[7:11]}"
        audit(data.get('worker_id', 'ASHA-RAMPUR-7821'), 'HEALTH_WORKER', 'PATIENT_REGISTERED',
              {'patient': pseudonym, 'village': village, 'consent': consent, 'channel': data.get('channel', 'HEALTH_WORKER')})
        return _json(201, {'pseudonym': pseudonym, 'village_id': village, 'village_name': village_name(village),
                           'consent': consent, 'message': 'Registered. Name and phone are stored encrypted; only the pseudonym is shown.'})

    if path == '/api/v1/triage/sessions':
        return _json(*start_triage(data))

    m = re.fullmatch(r'/api/v1/triage/sessions/([A-Z0-9-]+)/turn', path)
    if m:
        return _json(*triage_turn(m.group(1), data))

    m = re.fullmatch(r'/api/v1/worker/roster/([A-Z0-9-]+)/checkin', path)
    if m:
        p = ROSTER.get(m.group(1))
        if not p:
            return _json(404, {'error': 'Patient not found'})
        transcript = (data.get('transcript') or '').strip()
        parsed = VoiceCheckinParser.parse_checkin_speech(transcript, data.get('language', 'hi')) if transcript else None
        sys_bp = data.get('systolic') or (parsed and parsed.systolic_bp)
        dia_bp = data.get('diastolic') or (parsed and parsed.diastolic_bp)
        glucose = data.get('glucose') or (parsed and parsed.blood_glucose)
        dose = data.get('dose_status') or (parsed and parsed.adherence_status) or 'TAKEN'
        last = p['_vitals'][-1]
        day = p['_today']
        p['_vitals'].append({
            'recorded_at': day,
            'systolic_bp': int(sys_bp) if sys_bp else last.get('systolic_bp'),
            'diastolic_bp': int(dia_bp) if dia_bp else last.get('diastolic_bp'),
            'blood_glucose': float(glucose) if glucose else last.get('blood_glucose'),
            'glucose_context': 'FASTING',
        })
        p['_adherence'].append({'scheduled_time': day, 'status': dose, 'reason_for_miss': None,
                                'medication_name': 'As prescribed by PHC'})
        p['_today'] = day + timedelta(days=1)
        _evaluate_patient(p)
        audit(data.get('worker_id', 'ASHA-RAMPUR-7821'), 'HEALTH_WORKER', 'CHRONIC_CHECKIN',
              {'patient': p['pseudonym'], 'transcript': transcript, 'bp': p['latest']['bp'],
               'glucose': p['latest']['glucose'], 'dose': dose, 'risk': p['risk']['risk_level']})
        esc = _escalate_chronic(p)
        return _json(200, {'patient': _public_patient(p), 'escalation_id': esc['id'] if esc else None,
                           'parsed_from_voice': parsed.dict() if parsed else None})

    m = re.fullmatch(r'/api/v1/escalations/(ESC-\d+)/review', path)
    if m:
        esc = next((e for e in ESCALATIONS if e['id'] == m.group(1)), None)
        if not esc:
            return _json(404, {'error': 'Escalation not found'})
        decision = data.get('decision', 'AGREE')
        final_level = data.get('final_level') or esc['level']
        esc['status'] = 'REVIEWED'
        esc['review'] = {
            'decision': decision,
            'final_level': final_level,
            'note': data.get('note', ''),
            'reviewer': data.get('reviewer', 'DR-VERMA-PHC-402'),
            'reviewed_at': datetime.now().strftime('%d %b %Y, %I:%M %p'),
            'label_for_training': {'system_level': esc['level'], 'clinician_level': final_level,
                                   'agreement': decision == 'AGREE'},
        }
        audit(esc['review']['reviewer'], 'DOCTOR', 'HUMAN_OVERRIDE' if decision == 'OVERRIDE' else 'CLINICIAN_REVIEW',
              {'escalation_id': esc['id'], 'system_level': esc['level'], 'final_level': final_level,
               'note': esc['review']['note']})
        return _json(200, esc)

    m = re.fullmatch(r'/api/v1/surveillance/alerts/([A-Za-z0-9-]+)/ack', path)
    if m:
        alert = next((a for a in SURVEILLANCE['alerts'] if a['id'] == m.group(1)), None)
        if not alert:
            return _json(404, {'error': 'Alert not found'})
        alert['status'] = 'ACKNOWLEDGED'
        alert['acknowledged_by'] = data.get('officer', 'OFFICER-DIST-881')
        alert['response_note'] = data.get('note', '')
        audit(alert['acknowledged_by'], 'HEALTH_OFFICER', 'OUTBREAK_ALERT_ACKNOWLEDGED',
              {'alert_id': alert['id'], 'note': alert['response_note']})
        return _json(200, alert)

    return None


def init():
    _seed_roster()
    for p in sorted(ROSTER.values(), key=lambda x: -x['risk']['action_priority']):
        _escalate_chronic(p)
    _seed_surveillance()


init()
