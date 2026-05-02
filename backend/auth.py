import hashlib
import hmac
import base64
import json
import time
import os

SECRET_KEY = os.getenv("SECRET_KEY", "taskflow-secret-key-2024-amity")


def hash_password(password: str) -> str:
    salt = os.urandom(16).hex()
    hashed = hashlib.sha256(f"{salt}{password}".encode()).hexdigest()
    return f"{salt}:{hashed}"


def verify_password(password: str, stored: str) -> bool:
    try:
        salt, hashed = stored.split(":")
        return hashlib.sha256(f"{salt}{password}".encode()).hexdigest() == hashed
    except:
        return False


def create_token(user_id: int, email: str) -> str:
    header = base64.urlsafe_b64encode(json.dumps({"alg": "HS256", "typ": "JWT"}).encode()).decode().rstrip("=")
    payload = base64.urlsafe_b64encode(json.dumps({
        "sub": user_id,
        "email": email,
        "exp": int(time.time()) + 86400 * 7  # 7 days
    }).encode()).decode().rstrip("=")
    sig_input = f"{header}.{payload}"
    sig = hmac.new(SECRET_KEY.encode(), sig_input.encode(), hashlib.sha256).hexdigest()
    return f"{header}.{payload}.{sig}"


def decode_token(token: str) -> dict:
    try:
        parts = token.split(".")
        if len(parts) != 3:
            return None
        payload_b64 = parts[1]
        padding = 4 - len(payload_b64) % 4
        if padding != 4:
            payload_b64 += "=" * padding
        payload = json.loads(base64.urlsafe_b64decode(payload_b64))
        if payload.get("exp", 0) < time.time():
            return None
        return payload
    except:
        return None
