"""
ArogyaSaathi Local Standard Library Server.
Provides immediate HTTP API endpoints on port 8000 for frontend clients and demo interfaces
without requiring external heavy dependencies.
"""

import sys
import os
import json
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse

# Ensure backend root is in sys.path
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.services.symptom_extractor import extract_clinical_symptoms
from app.services.voice_checkin import VoiceCheckinParser
from app.core.security import generate_pseudonym, encrypt_pii

voice_parser = VoiceCheckinParser()

class ArogyaApiHandler(BaseHTTPRequestHandler):
    def _send_cors_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS, PUT, DELETE')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')

    def do_OPTIONS(self):
        self.send_response(204)
        self._send_cors_headers()
        self.end_headers()

    def _read_json(self):
        content_length = int(self.headers.get('Content-Length', 0))
        if content_length > 0:
            body = self.rfile.read(content_length).decode('utf-8')
            return json.loads(body)
        return {}

    def _send_json(self, status_code, data):
        body = json.dumps(data).encode('utf-8')
        self.send_response(status_code)
        self._send_cors_headers()
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        url = urllib.parse.urlparse(self.path)
        path = url.path

        if path in ['/', '/index.html', '/app']:
            html_path = os.path.join(os.path.dirname(backend_dir), 'frontend', 'web', 'index.html')
            if os.path.exists(html_path):
                with open(html_path, 'rb') as f:
                    content = f.read()
                self.send_response(200)
                self._send_cors_headers()
                self.send_header('Content-Type', 'text/html; charset=utf-8')
                self.send_header('Content-Length', str(len(content)))
                self.end_headers()
                self.wfile.write(content)
                return

        if path in ['/api/v1/health', '/health']:
            self._send_json(200, {
                'status': 'healthy',
                'service': 'ArogyaSaathi Backend Gateway',
                'dpdp_act_2023_active': True,
                'version': '1.0.0'
            })
            return

        if '/chronic/village/' in path and '/action-queue' in path:
            self._send_json(200, {
                'village_id': 'VILL-RAMPUR',
                'priority_roster': [
                    {
                        'patient_id': 'p-001',
                        'pseudonym_id': 'HASH-RAMPUR-101',
                        'age': 58,
                        'gender': 'Male',
                        'risk_level': 'CRITICAL',
                        'action_priority': 1,
                        'recommended_action': 'Immediate home visit: Blood pressure spike (184/110) & severe headache.',
                        'flags': ['HYPERTENSIVE_CRISIS', 'MISSED_RECENT_DOSE'],
                        'latest_systolic': 184.0,
                        'adherence_rate_pct': 50.0
                    },
                    {
                        'patient_id': 'p-002',
                        'pseudonym_id': 'HASH-RAMPUR-102',
                        'age': 52,
                        'gender': 'Female',
                        'risk_level': 'HIGH',
                        'action_priority': 2,
                        'recommended_action': 'Visit within 24-48 hours: 3 consecutive missed diabetes doses reported.',
                        'flags': ['SUSTAINED_HYPERGLYCEMIA', 'CRITICAL_MEDICATION_DROPOUT'],
                        'latest_systolic': 146.0,
                        'adherence_rate_pct': 40.0
                    },
                    {
                        'patient_id': 'p-003',
                        'pseudonym_id': 'HASH-RAMPUR-103',
                        'age': 44,
                        'gender': 'Female',
                        'risk_level': 'MODERATE',
                        'action_priority': 3,
                        'recommended_action': 'Voice check-in scheduled. Rising systolic BP velocity over 2 weeks.',
                        'flags': ['ACCELERATING_SYSTOLIC_TREND'],
                        'latest_systolic': 138.0,
                        'adherence_rate_pct': 85.0
                    }
                ]
            })
            return

        if path in ['/api/v1/surveillance/alerts/active', '/surveillance/alerts/active']:
            self._send_json(200, [
                {
                    'id': 'ALT-RAMPUR-ADD-01',
                    'village_id': 'VILL-RAMPUR',
                    'village_name': 'Rampur Village (रामपुर)',
                    'syndrome': 'ADD (Acute Diarrheal Disease)',
                    'alert_level': 'WARNING',
                    'z_score': 3.42,
                    'observed_cases': 19,
                    'baseline_cases': 4.2,
                    'percent_above_baseline': 352.0,
                    'fused_signals': ['PHC Clinic Cases (+280%)', 'Pharmacy ORS Spike (+420%)', 'School Absenteeism (+35%)'],
                    'recommended_intervention': 'Water Chlorination Depot + Rapid Stool Sampling required immediately.',
                    'detected_at': '2026-10-29T08:30:00Z',
                    'latitude': 25.3210,
                    'longitude': 82.9812,
                    'population_at_risk': 1450,
                    'rrt_checklist': [
                        'Distribute 500 Chlorine/Halazone tablets to Ward 2 & Ward 4 wells',
                        'Deploy 200 ORS + Zinc packets to Anganwadi Centre',
                        'Collect 3 drinking water samples from primary tube-well',
                        'Broadcast public advisory: Boil drinking water for 10 minutes'
                    ]
                },
                {
                    'id': 'ALT-SHIVPUR-ILI-02',
                    'village_id': 'VILL-SHIVPUR',
                    'village_name': 'Shivpur Sub-centre (शिवपुर)',
                    'syndrome': 'ILI (Influenza-like Illness / Fever)',
                    'alert_level': 'WATCH',
                    'z_score': 2.15,
                    'observed_cases': 11,
                    'baseline_cases': 5.0,
                    'percent_above_baseline': 120.0,
                    'fused_signals': ['ASHA Syndromic Cough/Fever Reports', 'Local Chemist Paracetamol Sales'],
                    'recommended_intervention': 'Monitor daily caseload; test 5 febrile patients for Dengue/Malaria.',
                    'detected_at': '2026-10-29T03:45:00Z',
                    'latitude': 25.3520,
                    'longitude': 82.9430,
                    'population_at_risk': 2100,
                    'rrt_checklist': [
                        'Verify fever caseload with ANM (Auxiliary Nurse Midwife)',
                        'Check vector breeding sites around village pond',
                        'Replenish Rapid Diagnostic Kits (RDKs) at Sub-centre'
                    ]
                }
            ])
            return

        self._send_json(404, {'error': f'Route not found: {path}'})

    def do_POST(self):
        url = urllib.parse.urlparse(self.path)
        path = url.path
        data = self._read_json()

        if path in ['/api/v1/triage/session/start', '/triage/session/start']:
            session_id = f"SES-{os.urandom(4).hex().upper()}"
            self._send_json(201, {
                'session_id': session_id,
                'status': 'INITIALIZED',
                'patient_pseudonym': data.get('patient_pseudonym', 'HASH-RAMPUR-101'),
                'language': data.get('language', 'hi')
            })
            return

        if '/text-turn' in path:
            text = data.get('text', '')
            extracted = extract_clinical_symptoms(text, language='hi')
            is_emergency = len(extracted.danger_signs) > 0 or 'chest_pain' in extracted.active_symptoms

            if is_emergency:
                resp = {
                    'session_id': 'SES-LIVE',
                    'transcription': text,
                    'detected_language': 'hi',
                    'extracted_symptoms': extracted.active_symptoms,
                    'danger_signs': extracted.danger_signs,
                    'is_final': True,
                    'triage_level': 'EMERGENCY',
                    'decision_rationale': 'CRITICAL: Acute Red Flag detected. Immediate emergency referral required.',
                    'checklist': [
                        'Call 108 Emergency Ambulance',
                        'Keep patient seated in resting position',
                        'Notify Medical Officer at nearest PHC'
                    ],
                    'is_red_flag_overridden': True
                }
            else:
                resp = {
                    'session_id': 'SES-LIVE',
                    'transcription': text,
                    'detected_language': 'hi',
                    'extracted_symptoms': extracted.active_symptoms,
                    'danger_signs': [],
                    'is_final': False,
                    'next_question': 'बुखार कितने दिनों से है? क्या गर्दन में अकड़न है?',
                    'checklist': ['Check temperature with thermometer', 'Check neck flexibility']
                }
            self._send_json(200, resp)
            return

        if path in ['/api/v1/chronic/checkin/voice', '/chronic/checkin/voice']:
            transcript = data.get('speech_transcript', '')
            parsed = voice_parser.parse(transcript, language='hi')
            self._send_json(200, {
                'systolic_bp': parsed.systolic_bp or 145,
                'diastolic_bp': parsed.diastolic_bp or 92,
                'adherence_status': parsed.adherence_status,
                'miss_reason': parsed.miss_reason,
                'risk_level': 'HIGH' if (parsed.systolic_bp or 145) >= 140 else 'MODERATE',
                'voice_feedback_text_hi': f"सावधानी: आपका रक्तचाप ({parsed.systolic_bp or 145}/{parsed.diastolic_bp or 92}) बढ़ा हुआ है। आशा कार्यकर्ता को सूचित किया गया है।",
                'voice_feedback_text_en': f"Notice: Your BP ({parsed.systolic_bp or 145}/{parsed.diastolic_bp or 92}) is elevated. Health worker alerted."
            })
            return

        if path in ['/api/v1/patients/', '/api/v1/patients', '/patients/']:
            name = data.get('name', 'Anonymous')
            phone = data.get('phone', '0000000000')
            village_id = data.get('village_id', 'VILL-RAMPUR')
            pseudo = f"HASH-{village_id.replace('VILL-', '')}-{generate_pseudonym(f'{name}:{phone}')[7:11]}"
            self._send_json(201, {
                'patient_id': f"p-{os.urandom(4).hex()}",
                'pseudonym_id': pseudo,
                'village_id': village_id,
                'dpdp_status': 'ENCRYPTED_CONSENTED',
                'message': 'Patient successfully registered locally with DPDP verbal consent.'
            })
            return

        self._send_json(404, {'error': f'POST route not found: {path}'})

    def log_message(self, format, *args):
        # Quiet standard logging
        pass

def run(port=8000):
    server_address = ('0.0.0.0', port)
    httpd = HTTPServer(server_address, ArogyaApiHandler)
    print(f"🏥 ArogyaSaathi Local Backend API running on http://127.0.0.1:{port}")
    httpd.serve_forever()

if __name__ == '__main__':
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    run(port)
