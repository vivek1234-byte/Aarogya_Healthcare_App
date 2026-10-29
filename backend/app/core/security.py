import json
import hmac
import hashlib
from datetime import datetime, timedelta
from typing import Any, Dict, Optional, Union
from passlib.context import CryptContext
import jwt
from cryptography.fernet import Fernet
from app.core.config import settings

# Password hashing configuration using bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Fernet cipher instance for AES-128-CBC / HMAC-SHA256 PII encryption
_fernet = Fernet(settings.PII_ENCRYPTION_KEY.encode())


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain-text password against a bcrypt hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password securely using bcrypt."""
    return pwd_context.hash(password)


def create_access_token(
    subject: Union[str, Any],
    role: str,
    village_id: Optional[str] = None,
    expires_delta: Optional[timedelta] = None
) -> str:
    """Generate a signed JWT token with user identity and role-based claims."""
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode = {
        "sub": str(subject),
        "role": role,
        "village_id": village_id,
        "exp": expire,
        "iat": datetime.utcnow()
    }
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    """Decode and validate a JWT access token."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except jwt.PyJWTError:
        return None


# ----------------------------------------------------------------------
# DPDP Compliance & Security Helpers
# ----------------------------------------------------------------------

def encrypt_pii(pii_data: Union[Dict[str, Any], str]) -> str:
    """
    Encrypt Personally Identifiable Information (Name, Phone, Address, ABHA ID)
    at rest using AES-128/256 symmetric encryption.
    """
    if isinstance(pii_data, dict):
        serialized = json.dumps(pii_data, ensure_ascii=False)
    else:
        serialized = str(pii_data)
    
    encrypted_bytes = _fernet.encrypt(serialized.encode("utf-8"))
    return encrypted_bytes.decode("utf-8")


def decrypt_pii(encrypted_data: str) -> Union[Dict[str, Any], str]:
    """
    Decrypt encrypted PII for authorized healthcare workers and PHC doctors.
    """
    try:
        decrypted_bytes = _fernet.decrypt(encrypted_data.encode("utf-8"))
        decrypted_str = decrypted_bytes.decode("utf-8")
        try:
            return json.loads(decrypted_str)
        except json.JSONDecodeError:
            return decrypted_str
    except Exception as e:
        raise ValueError(f"Failed to decrypt PII: {str(e)}")


def generate_pseudonym(unique_identifier: str) -> str:
    """
    Deterministic pseudonymization (HMAC-SHA256) of patient ID / phone number.
    Ensures safe analytics and syndromic surveillance without exposing patient PII.
    """
    key = settings.PSEUDONYM_SALT.encode("utf-8")
    msg = unique_identifier.strip().encode("utf-8")
    return hmac.new(key, msg, hashlib.sha256).hexdigest()


def compute_audit_hash(previous_hash: str, entry_dict: Dict[str, Any]) -> str:
    """
    Computes a cryptographic SHA-256 hash chaining the previous audit entry
    to ensure an immutable, tamper-evident audit ledger.
    """
    normalized_data = json.dumps(entry_dict, sort_keys=True, default=str)
    combined = f"{previous_hash}|{normalized_data}".encode("utf-8")
    return hashlib.sha256(combined).hexdigest()
