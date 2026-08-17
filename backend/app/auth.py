"""
JWT-based authentication for the single-admin panel: a login endpoint
that exchanges username/password (from .env) for a signed token, and a
FastAPI dependency that protects every other route.

The password lives in .env as plaintext (a file that only ever exists on
the admin's own server and is gitignored) and is hashed once at import
time purely so the comparison at request time is a bcrypt check, never a
cleartext compare or anything that ends up in a log line.
"""
import secrets
import time

import bcrypt
import jwt
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from . import config
from .schemas import LoginRequest, LoginResponse

router = APIRouter(prefix="/api/auth", tags=["auth"])
_bearer_scheme = HTTPBearer(auto_error=False)

_ADMIN_PASSWORD_HASH = bcrypt.hashpw(config.ADMIN_PASSWORD.encode("utf-8"), bcrypt.gensalt())


def _create_token(username: str) -> str:
    now = int(time.time())
    payload = {"sub": username, "iat": now, "exp": now + config.JWT_EXPIRE_MINUTES * 60}
    return jwt.encode(payload, config.JWT_SECRET, algorithm=config.JWT_ALGORITHM)


@router.post("/login", response_model=LoginResponse)
def login(payload: LoginRequest):
    username_ok = secrets.compare_digest(payload.username, config.ADMIN_USERNAME)
    password_ok = bcrypt.checkpw(payload.password.encode("utf-8"), _ADMIN_PASSWORD_HASH)
    if not (username_ok and password_ok):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid username or password")
    token = _create_token(payload.username)
    return LoginResponse(access_token=token, expires_in=config.JWT_EXPIRE_MINUTES * 60)


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(_bearer_scheme)) -> str:
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")
    try:
        payload = jwt.decode(credentials.credentials, config.JWT_SECRET, algorithms=[config.JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired, please log in again")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    return payload["sub"]
