"""
Accounts and sessions.
- Passwords: scrypt with a per-user salt.
- Names and mobile numbers: encrypted at rest; lookups use a keyed hash of the mobile.
- Staff sign up with a shared access code; patients are registered by their ASHA and
  activate their account with a one-time code the ASHA hands them.
"""

import hashlib
import hmac
import re
import secrets
from datetime import datetime, timedelta

from app.core.security import decrypt_pii, encrypt_pii, generate_pseudonym
from app.portal import config, db

ROLES = ('PATIENT', 'HEALTH_WORKER', 'DOCTOR', 'HEALTH_OFFICER')
STAFF_ROLES = ('HEALTH_WORKER', 'DOCTOR', 'HEALTH_OFFICER')


class AuthError(Exception):
    def __init__(self, message, status=400):
        super().__init__(message)
        self.status = status


# ================= HELPERS =================
def normalize_mobile(raw):
    digits = re.sub(r'\D', '', str(raw or ''))
    if len(digits) == 12 and digits.startswith('91'):
        digits = digits[2:]
    if not re.fullmatch(r'[6-9]\d{9}', digits):
        raise AuthError('Enter a valid 10-digit Indian mobile number.')
    return digits


def mobile_hash(mobile):
    return generate_pseudonym(f'mobile:{mobile}')


def hash_password(password):
    salt = secrets.token_bytes(16)
    digest = hashlib.scrypt(password.encode('utf-8'), salt=salt, n=2 ** 14, r=8, p=1, dklen=32)
    return f'scrypt${salt.hex()}${digest.hex()}'


def verify_password(password, stored):
    try:
        _, salt_hex, digest_hex = stored.split('$')
        digest = hashlib.scrypt(password.encode('utf-8'), salt=bytes.fromhex(salt_hex), n=2 ** 14, r=8, p=1, dklen=32)
        return hmac.compare_digest(digest.hex(), digest_hex)
    except (ValueError, AttributeError):
        return False


def check_password_strength(password):
    if len(password or '') < 6:
        raise AuthError('Password must be at least 6 characters.')


def decrypt(value):
    # decrypt_pii JSON-parses its output, so "9811111111" would come back as an int
    try:
        result = decrypt_pii(value)
    except ValueError:
        return ''
    return result if isinstance(result, str) else str(result)


def new_id(prefix):
    return f'{prefix}-{secrets.token_hex(4).upper()}'


def public_user(user):
    village = db.query_one('SELECT * FROM villages WHERE id = ?', (user['village_id'],)) if user.get('village_id') else None
    data = {
        'id': user['id'],
        'role': user['role'],
        'name': decrypt(user['name_enc']),
        'mobile_last4': decrypt(user['mobile_enc'])[-4:],
        'village': village,
        'facility': user.get('facility'),
    }
    if user['role'] == 'PATIENT':
        patient = db.query_one('SELECT pseudonym, language FROM patients WHERE user_id = ?', (user['id'],))
        if patient:
            data.update(patient)
    return data


# ================= VILLAGES =================
def get_or_create_village(data, actor_id):
    """data: {'id'} for an existing village, or {'name', 'district', 'block', 'state', 'lat', 'lon'} for a new one."""
    if data.get('id'):
        village = db.query_one('SELECT * FROM villages WHERE id = ?', (data['id'],))
        if not village:
            raise AuthError('Village not found.')
        return village
    name = (data.get('name') or '').strip()
    district = (data.get('district') or '').strip()
    if not name or not district:
        raise AuthError('Village name and district are required.')
    existing = db.query_one('SELECT * FROM villages WHERE lower(name) = lower(?) AND lower(district) = lower(?)', (name, district))
    if existing:
        return existing
    village_id = f"V-{hashlib.sha1(f'{name}|{district}'.lower().encode()).hexdigest()[:8].upper()}"
    lat = data.get('lat')
    lon = data.get('lon')
    db.execute('INSERT INTO villages (id, name, block, district, state, lat, lon, created_by, created_at) VALUES (?,?,?,?,?,?,?,?,?)',
               (village_id, name, (data.get('block') or '').strip(), district, (data.get('state') or '').strip(),
                float(lat) if lat not in (None, '') else None, float(lon) if lon not in (None, '') else None,
                actor_id, db.now()))
    db.audit(actor_id, 'SYSTEM', 'VILLAGE_ADDED', {'village_id': village_id, 'name': name, 'district': district})
    return db.query_one('SELECT * FROM villages WHERE id = ?', (village_id,))


# ================= SESSIONS =================
def create_session(user_id):
    token = secrets.token_urlsafe(32)
    expires = (datetime.now() + timedelta(days=config.SESSION_DAYS)).strftime('%Y-%m-%d %H:%M:%S')
    db.execute('INSERT INTO sessions (token_hash, user_id, expires_at) VALUES (?,?,?)',
               (hashlib.sha256(token.encode()).hexdigest(), user_id, expires))
    return token


def user_from_token(token):
    if not token:
        return None
    row = db.query_one('SELECT u.* FROM sessions s JOIN users u ON u.id = s.user_id '
                       'WHERE s.token_hash = ? AND s.expires_at > ? AND u.status = ?',
                       (hashlib.sha256(token.encode()).hexdigest(), db.now(), 'ACTIVE'))
    return row


def logout(token):
    db.execute('DELETE FROM sessions WHERE token_hash = ?', (hashlib.sha256(token.encode()).hexdigest(),))


# ================= LOGIN / SIGNUP / ACTIVATION =================
def login(role, mobile, password):
    if role not in ROLES:
        raise AuthError('Choose who you are logging in as.')
    mobile = normalize_mobile(mobile)
    user = db.query_one('SELECT * FROM users WHERE role = ? AND mobile_hash = ?', (role, mobile_hash(mobile)))
    if user and user['status'] == 'PENDING_ACTIVATION':
        raise AuthError('Account not activated yet. Use "First time? Activate account" with the code from your ASHA worker.', 403)
    if not user or user['status'] != 'ACTIVE' or not verify_password(password or '', user['password_hash'] or ''):
        raise AuthError('Wrong mobile number or password.', 401)
    db.audit(user['id'], role, 'LOGIN', {})
    return create_session(user['id']), user


def staff_signup(data):
    if not config.STAFF_SIGNUP_CODE:
        raise AuthError('Staff sign-up is disabled. Ask the administrator to set STAFF_SIGNUP_CODE on the server.', 403)
    if not hmac.compare_digest(str(data.get('access_code') or ''), config.STAFF_SIGNUP_CODE):
        raise AuthError('Wrong staff access code.', 403)
    role = data.get('role')
    if role not in STAFF_ROLES:
        raise AuthError('Choose a staff role.')
    name = (data.get('name') or '').strip()
    if len(name) < 2:
        raise AuthError('Enter your full name.')
    mobile = normalize_mobile(data.get('mobile'))
    password = data.get('password') or ''
    check_password_strength(password)
    if db.query_one('SELECT id FROM users WHERE role = ? AND mobile_hash = ?', (role, mobile_hash(mobile))):
        raise AuthError('An account with this mobile number already exists for this role. Please log in.', 409)

    user_id = new_id({'HEALTH_WORKER': 'ASHA', 'DOCTOR': 'DR', 'HEALTH_OFFICER': 'OFF'}[role])
    village_id = None
    if role == 'HEALTH_WORKER':
        village_id = get_or_create_village(data.get('village') or {}, user_id)['id']
    db.execute('INSERT INTO users (id, role, name_enc, mobile_enc, mobile_hash, password_hash, status, village_id, facility, created_by, created_at) '
               'VALUES (?,?,?,?,?,?,?,?,?,?,?)',
               (user_id, role, encrypt_pii(name), encrypt_pii(mobile), mobile_hash(mobile), hash_password(password),
                'ACTIVE', village_id, (data.get('facility') or '').strip() or None, 'SELF', db.now()))
    db.audit(user_id, role, 'STAFF_SIGNUP', {'role': role, 'village_id': village_id})
    user = db.query_one('SELECT * FROM users WHERE id = ?', (user_id,))
    return create_session(user_id), user


def issue_activation_code(user_id):
    code = f'{secrets.randbelow(10 ** 6):06d}'
    expires = (datetime.now() + timedelta(hours=config.ACTIVATION_HOURS)).strftime('%Y-%m-%d %H:%M:%S')
    db.execute('UPDATE users SET activation_hash = ?, activation_expires = ? WHERE id = ?',
               (hash_password(code), expires, user_id))
    return code


def activate_patient(mobile, code, password):
    mobile = normalize_mobile(mobile)
    check_password_strength(password)
    user = db.query_one('SELECT * FROM users WHERE role = ? AND mobile_hash = ?', ('PATIENT', mobile_hash(mobile)))
    if not user or not user['activation_hash']:
        raise AuthError('No pending activation for this number. Ask your ASHA worker to register you or give a new code.', 404)
    if user['activation_expires'] < db.now():
        raise AuthError('This code has expired. Ask your ASHA worker for a new one.', 403)
    if not verify_password(str(code or '').strip(), user['activation_hash']):
        raise AuthError('Wrong activation code.', 401)
    db.execute("UPDATE users SET password_hash = ?, status = 'ACTIVE', activation_hash = NULL, activation_expires = NULL WHERE id = ?",
               (hash_password(password), user['id']))
    db.audit(user['id'], 'PATIENT', 'ACCOUNT_ACTIVATED', {})
    user = db.query_one('SELECT * FROM users WHERE id = ?', (user['id'],))
    return create_session(user['id']), user
