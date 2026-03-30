# api/auth.py
# Rubis POS — Authentication System (Secured)

from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
from pydantic import BaseModel, EmailStr, validator
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import redis
import os
import secrets
import re
import logging

load_dotenv()

router = APIRouter()
logger = logging.getLogger("rubis.auth")

# ─────────────────────────────────────────
# SECURITY CONFIG  (all values from .env — never hardcoded)
# ─────────────────────────────────────────
SECRET_KEY = os.getenv("JWT_SECRET_KEY")
REFRESH_SECRET_KEY = os.getenv("JWT_REFRESH_SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7
RESET_TOKEN_EXPIRE_MINUTES = 15
MAX_LOGIN_ATTEMPTS = 5
LOCKOUT_MINUTES = 15

if not SECRET_KEY or not REFRESH_SECRET_KEY:
    raise RuntimeError("JWT_SECRET_KEY and JWT_REFRESH_SECRET_KEY must be set in .env")

# Use pbkdf2_sha256 - no bcrypt issues
pwd_context = CryptContext(
    schemes=["pbkdf2_sha256"],
    deprecated="auto",
    pbkdf2_sha256__rounds=29000
)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

# ─────────────────────────────────────────
# REDIS  (for rate limiting + session tracking) - DISABLED FOR NOW
# ─────────────────────────────────────────
def get_redis():
    try:
        return redis.Redis(
            host=os.getenv("REDIS_HOST", "localhost"),
            port=int(os.getenv("REDIS_PORT", 6379)),
            password=os.getenv("REDIS_PASSWORD"),
            decode_responses=True,
            socket_connect_timeout=1
        )
    except:
        return None

# ─────────────────────────────────────────
# DATABASE
# ─────────────────────────────────────────
def get_engine():
    return create_engine(os.getenv("DB_URL"), pool_pre_ping=True)

# ─────────────────────────────────────────
# MODELS
# ─────────────────────────────────────────
class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str

    @validator("password")
    def password_strength(cls, v):
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r"[0-9]", v):
            raise ValueError("Password must contain at least one number")
        return v

    @validator("full_name")
    def sanitize_name(cls, v):
        if not re.match(r"^[a-zA-Z\s'\-]{2,80}$", v):
            raise ValueError("Full name contains invalid characters")
        return v.strip()

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
    expires_in: int

class RefreshRequest(BaseModel):
    refresh_token: str

class PasswordResetRequest(BaseModel):
    token: str
    new_password: str

    @validator("new_password")
    def password_strength(cls, v):
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r"[0-9]", v):
            raise ValueError("Password must contain at least one number")
        return v

# ─────────────────────────────────────────
# PASSWORD + TOKEN UTILITIES
# ─────────────────────────────────────────
def hash_password(password: str) -> str:
    """Hash a password using pbkdf2_sha256"""
    return pwd_context.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain, hashed)

def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "iat": datetime.utcnow(), "type": "access"})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def create_refresh_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "iat": datetime.utcnow(), "type": "refresh"})
    return jwt.encode(to_encode, REFRESH_SECRET_KEY, algorithm=ALGORITHM)

def create_secure_token() -> str:
    """Cryptographically secure token for email verification and password reset."""
    return secrets.token_urlsafe(48)

# ─────────────────────────────────────────
# USER UTILITIES
# ─────────────────────────────────────────
def get_user_by_email(email: str):
    engine = get_engine()
    with engine.connect() as conn:
        result = conn.execute(
            text("SELECT * FROM users WHERE email = :email"),
            {"email": email}
        ).fetchone()
        return result

def get_user_by_id(user_id: int):
    engine = get_engine()
    with engine.connect() as conn:
        result = conn.execute(
            text("SELECT * FROM users WHERE id = :id"),
            {"id": user_id}
        ).fetchone()
        return result

def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "access":
            raise credentials_exception
        email: str = payload.get("sub")
        if not email:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = get_user_by_email(email)
    if not user:
        raise credentials_exception
    if not user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email not verified"
        )
    return user

def require_admin(current_user=Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user

def require_role(*roles: str):
    """
    Dependency factory — require one of the given roles.
    Admin users are automatically allowed regardless of the role list.
    """
    def checker(current_user=Depends(get_current_user)):
        # Admin has full access, no need to check roles
        if current_user.role == "admin":
            return current_user
        if current_user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires one of roles: {', '.join(roles)}"
            )
        return current_user
    return checker

# ─────────────────────────────────────────
# LOGIN ATTEMPT TRACKING (Redis-backed) - DISABLED FOR NOW
# ─────────────────────────────────────────
def _attempts_key(email: str) -> str:
    return f"login_attempts:{email}"

def _lockout_key(email: str) -> str:
    return f"login_locked:{email}"

def check_login_attempts(email: str):
    # Rate limiting disabled - Redis not available
    pass

def record_failed_attempt(email: str):
    # Rate limiting disabled - Redis not available
    pass

def clear_login_attempts(email: str):
    # Rate limiting disabled - Redis not available
    pass

# ─────────────────────────────────────────
# AUTH LOGGING
# ─────────────────────────────────────────
def log_auth_event(email: str, action: str, status_val: str, ip: str = None):
    try:
        engine = get_engine()
        with engine.begin() as conn:
            conn.execute(text("""
                INSERT INTO auth_logs (email, action, ip_address, success, created_at)
                VALUES (:email, :action, :ip, :success, NOW())
            """), {"email": email, "action": action, "ip": ip, "success": status_val == "success"})
    except Exception as e:
        logger.error(f"Failed to write auth log: {e}")

# ─────────────────────────────────────────
# AUTH ENDPOINTS
# ─────────────────────────────────────────
@router.post("/register", status_code=201)
def register(user: UserCreate, request: Request):
    existing = get_user_by_email(user.email)
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed = hash_password(user.password)
    verification_token = create_secure_token()
    engine = get_engine()

    with engine.begin() as conn:
        conn.execute(text("""
            INSERT INTO users (email, hashed_password, full_name, role,
                               is_verified, verification_token, created_at)
            VALUES (:email, :hashed_password, :full_name, 'viewer',
                    true, :verification_token, NOW())
        """), {
            "email": user.email,
            "hashed_password": hashed,
            "full_name": user.full_name,
            "verification_token": verification_token
        })

    log_auth_event(user.email, "register", "success", request.client.host)

    return {"message": "Registration successful. You can now log in."}

@router.post("/login", response_model=Token)
def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends()
):
    email = form_data.username.lower().strip()
    check_login_attempts(email)

    user = get_user_by_email(email)
    if not user or not verify_password(form_data.password, user.hashed_password):
        record_failed_attempt(email)
        log_auth_event(email, "login", "failed", request.client.host)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )

    if not user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Please verify your email before logging in"
        )

    clear_login_attempts(email)
    log_auth_event(email, "login", "success", request.client.host)

    access_token = create_access_token({"sub": user.email, "role": user.role, "user_id": user.id})
    refresh_token = create_refresh_token({"sub": user.email})

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60
    }

@router.post("/refresh", response_model=Token)
def refresh_token(data: RefreshRequest):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid refresh token"
    )
    try:
        payload = jwt.decode(data.refresh_token, REFRESH_SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "refresh":
            raise credentials_exception
        email: str = payload.get("sub")
        if not email:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = get_user_by_email(email)
    if not user:
        raise credentials_exception

    new_access = create_access_token({"sub": user.email, "role": user.role, "user_id": user.id})
    new_refresh = create_refresh_token({"sub": user.email})

    return {
        "access_token": new_access,
        "refresh_token": new_refresh,
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60
    }

@router.get("/verify/{token}")
def verify_email(token: str):
    if not re.match(r"^[a-zA-Z0-9_\-]{20,100}$", token):
        raise HTTPException(status_code=400, detail="Invalid token format")

    engine = get_engine()
    with engine.connect() as conn:
        user = conn.execute(
            text("SELECT * FROM users WHERE verification_token = :token"),
            {"token": token}
        ).fetchone()

    if not user:
        raise HTTPException(status_code=400, detail="Invalid or expired verification link")

    with engine.begin() as conn:
        conn.execute(text("""
            UPDATE users
            SET is_verified = true, verification_token = null
            WHERE id = :id
        """), {"id": user.id})

    return {"message": "Email verified successfully. You can now log in."}

@router.post("/forgot-password")
def forgot_password(email: str, request: Request):
    # Always return the same response regardless of whether email exists
    # This prevents email enumeration attacks
    user = get_user_by_email(email.lower().strip())
    if user:
        reset_token = create_secure_token()
        expires_at = datetime.utcnow() + timedelta(minutes=RESET_TOKEN_EXPIRE_MINUTES)
        engine = get_engine()
        with engine.begin() as conn:
            conn.execute(text("""
                UPDATE users
                SET reset_token = :token, reset_token_expires = :expires
                WHERE email = :email
            """), {"token": reset_token, "expires": expires_at, "email": user.email})

        log_auth_event(email, "password_reset_request", "success", request.client.host)

    return {"message": "If that email is registered, a reset link has been sent."}

@router.post("/reset-password")
def reset_password(data: PasswordResetRequest, request: Request):
    if not re.match(r"^[a-zA-Z0-9_\-]{20,100}$", data.token):
        raise HTTPException(status_code=400, detail="Invalid token format")

    engine = get_engine()
    with engine.connect() as conn:
        user = conn.execute(
            text("""
                SELECT * FROM users
                WHERE reset_token = :token
                  AND reset_token_expires > NOW()
            """),
            {"token": data.token}
        ).fetchone()

    if not user:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")

    hashed = hash_password(data.new_password)
    with engine.begin() as conn:
        conn.execute(text("""
            UPDATE users
            SET hashed_password = :hashed,
                reset_token = null,
                reset_token_expires = null
            WHERE id = :id
        """), {"hashed": hashed, "id": user.id})

    log_auth_event(user.email, "password_reset", "success", request.client.host)
    return {"message": "Password reset successfully. You can now log in."}

@router.get("/me")
def get_me(current_user=Depends(get_current_user)):
    return {
        "id": current_user.id,
        "email": current_user.email,
        "full_name": current_user.full_name,
        "role": current_user.role,
        "is_verified": current_user.is_verified,
        "branch": current_user.branch
    }

@router.post("/logout")
def logout(request: Request, current_user=Depends(get_current_user)):
    log_auth_event(current_user.email, "logout", "success", request.client.host)
    return {"message": "Logged out successfully"}




