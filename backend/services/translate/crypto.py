"""
AES-256-GCM 加密/解密用户 API Key
"""
import os
import hashlib
import base64
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

ENCRYPTION_SECRET = os.getenv("ENCRYPTION_SECRET", "chemvigil-encryption-secret-change-in-production")


def _derive_key() -> bytes:
    return hashlib.sha256(ENCRYPTION_SECRET.encode()).digest()


def encrypt_secret(value: str) -> str:
    key = _derive_key()
    aesgcm = AESGCM(key)
    nonce = os.urandom(12)
    ct = aesgcm.encrypt(nonce, value.encode(), None)
    return base64.b64encode(nonce + ct).decode()


def decrypt_secret(payload: str) -> str:
    key = _derive_key()
    raw = base64.b64decode(payload)
    nonce, ct = raw[:12], raw[12:]
    aesgcm = AESGCM(key)
    return aesgcm.decrypt(nonce, ct, None).decode()
