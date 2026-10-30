import hashlib
import hmac
import os
import uuid

from datetime import datetime, timedelta, timezone

import jwt

from dotenv import load_dotenv
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from database import get_database
from models import User, Role, TokenSession


load_dotenv()

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")

if not JWT_SECRET_KEY or len(JWT_SECRET_KEY) < 32:
    raise RuntimeError(
        "Set JWT_SECRET_KEY to a random secret of at least 32 characters"
        )

JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_MINUTES = int(
    os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "15")
)
REFRESH_TOKEN_DAYS = int(
    os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7")
)

security = HTTPBearer(auto_error=False)


def hash_password(password: str) -> str:
    salt = os.urandom(16).hex()

    password_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        600000
    ).hex()

    return f"{salt}${password_hash}"


def verify_password(password: str, stored_hash: str) -> bool:
    try:
        salt, expected_hash = stored_hash.split("$", 1)

        actual_hash = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt.encode("utf-8"),
            600000
        ).hex()

        return hmac.compare_digest(actual_hash, expected_hash)

    except (ValueError, TypeError):
        return False


def create_token(
    user_id: int,
    session_id: str,
    token_type: str,
    expires_delta: timedelta
):
    now = datetime.now(timezone.utc)

    payload = {
        "sub": str(user_id),
        "sid": session_id,
        "jti": str(uuid.uuid4()),
        "type": token_type,
        "iat": now,
        "exp": now + expires_delta
    }

    return jwt.encode(
        payload,
        JWT_SECRET_KEY,
        algorithm=JWT_ALGORITHM
    ), payload


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_database)
):
    unauthorized = HTTPException(
        status_code=401,
        detail="Invalid, expired, or logged-out access token",
        headers={"WWW-Authenticate": "Bearer"}
    )

    if credentials is None:
        raise unauthorized

    try:
        payload = jwt.decode(
            credentials.credentials,
            JWT_SECRET_KEY,
            algorithms=[JWT_ALGORITHM]
        )

        if payload.get("type") != "access":
            raise unauthorized

        user_id = int(payload["sub"])
        session_id = payload["sid"]

    except (jwt.InvalidTokenError, KeyError, ValueError, TypeError):
        raise unauthorized

    session = db.query(TokenSession).filter(
        TokenSession.session_id == session_id,
        TokenSession.user_id == user_id,
        TokenSession.revoked.is_(False)
    ).first()

    if session is None:
        raise unauthorized

    if session.expires_at <= datetime.now(timezone.utc).replace(tzinfo=None):
        raise unauthorized

    user = db.query(User).filter(
        User.user_id == user_id,
        User.is_active.is_(True)
    ).first()

    if user is None:
        raise unauthorized

    role = db.query(Role).filter(
        Role.role_id == user.role_id
    ).first()

    if role is None:
        raise unauthorized

    user.role_name = role.role_name
    user.session_id = session_id

    return user


def require_roles(*allowed_roles):
    def role_checker(user=Depends(get_current_user)):
        if user.role_name not in allowed_roles:
            raise HTTPException(
                status_code=403,
                detail="You do not have permission to access this resource"
            )

        return user

    return role_checker