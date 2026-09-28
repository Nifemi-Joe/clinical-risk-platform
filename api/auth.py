"""
Authentication: password hashing (bcrypt via passlib) + JWT access tokens
(python-jose). This is a real, working auth implementation, not a stub -
passwords are genuinely hashed and never stored in plaintext, tokens are
genuinely signed and verified.

ONE THING THAT IS a placeholder, clearly marked: SECRET_KEY below. In any
real deployment this MUST come from an environment variable, never be
committed, and be rotated - it's hardcoded here only so the app runs
out-of-the-box for local development / this portfolio demo. See
docker/docker-compose.yml for how to inject it as an env var instead.
"""
from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone

import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from api.db import Role, User, get_db

# SECURITY NOTE: hardcoded default for local/demo use only - override with
# the SECRET_KEY environment variable in any real deployment.
SECRET_KEY = os.environ.get("SECRET_KEY", "eec5f5a15018539de6a64d49bf71e5877411003c386823683934e895566f69e3")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 8  # 8-hour session

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def hash_password(password: str) -> str:
    """Uses the bcrypt library directly rather than via passlib -
    passlib's CryptContext runs an internal self-test with a long dummy
    password that raises ValueError against bcrypt>=4.1 (which correctly
    rejects inputs over its 72-byte limit instead of silently truncating,
    as older bcrypt versions did). Direct bcrypt avoids that self-test
    entirely and is the simpler, better-maintained path in 2026 anyway.
    bcrypt's own 72-byte limit still applies to the real password - long
    passphrases are truncated at 72 bytes by bcrypt itself, a known and
    accepted bcrypt characteristic, not a bug in this code."""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))


def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "purpose": "access"})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


PASSWORD_RESET_EXPIRE_MINUTES = 30


def create_password_reset_token(user_id: int) -> str:
    """Short-lived, purpose-scoped token - deliberately NOT a general access
    token with a long expiry, so a leaked reset link can't be replayed as a
    session token. The 'purpose' claim is checked on use (see
    verify_password_reset_token) so an access token can't be misused here
    either, and vice versa."""
    expire = datetime.now(timezone.utc) + timedelta(minutes=PASSWORD_RESET_EXPIRE_MINUTES)
    payload = {"sub": str(user_id), "exp": expire, "purpose": "password_reset"}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def verify_password_reset_token(token: str) -> int:
    """Returns the user id if valid, raises HTTPException otherwise."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        raise HTTPException(status_code=400, detail="Invalid or expired reset link")
    if payload.get("purpose") != "password_reset":
        raise HTTPException(status_code=400, detail="Invalid or expired reset link")
    return int(payload["sub"])


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None or payload.get("purpose") != "access":
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = db.query(User).filter(User.id == int(user_id)).first()
    if user is None or not user.is_active:
        raise credentials_exception
    return user


def require_role(*allowed_roles: Role):
    """FastAPI dependency factory: `Depends(require_role(Role.doctor))`
    raises 403 if the authenticated user's role isn't in allowed_roles."""

    def checker(user: User = Depends(get_current_user)) -> User:
        if user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires role: {', '.join(r.value for r in allowed_roles)}",
            )
        return user

    return checker
