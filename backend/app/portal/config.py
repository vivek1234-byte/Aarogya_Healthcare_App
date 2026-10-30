"""
Runtime configuration for the portal server.
Values come from environment variables, falling back to backend/.env.
"""

import os

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _load_dotenv():
    path = os.path.join(BACKEND_DIR, '.env')
    if not os.path.exists(path):
        return
    with open(path, 'r', encoding='utf-8') as f:
        for raw in f:
            line = raw.strip()
            if not line or line.startswith('#') or '=' not in line:
                continue
            key, value = line.split('=', 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            os.environ.setdefault(key, value)


_load_dotenv()

DB_PATH = os.environ.get('AROGYA_DB_PATH', os.path.join(BACKEND_DIR, 'storage_data', 'arogya.db'))
PORTS = [int(p) for p in os.environ.get('PORT', '8000,8080').split(',') if p.strip()]
# '::' = all interfaces (phone over Wi-Fi / USB). On a server behind Caddy use 127.0.0.1.
HOST = os.environ.get('HOST', '::')

# Staff (ASHA / doctor / officer) self-signup requires this code so the public cannot create staff accounts
STAFF_SIGNUP_CODE = os.environ.get('STAFF_SIGNUP_CODE', '')

SESSION_DAYS = int(os.environ.get('SESSION_DAYS', '30'))
ACTIVATION_HOURS = int(os.environ.get('ACTIVATION_HOURS', '72'))

ANTHROPIC_API_KEY = os.environ.get('ANTHROPIC_API_KEY', '')
CHAT_MODEL = os.environ.get('AROGYA_CHAT_MODEL', 'claude-opus-5-5')

# Contact for OpenStreetMap services (their usage policy asks for an identifying User-Agent)
OSM_USER_AGENT = os.environ.get('OSM_USER_AGENT', 'ArogyaSaathi/1.0 (frontline health worker referral tool)')
