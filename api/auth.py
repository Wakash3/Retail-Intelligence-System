# api/auth.py
# Rubis POS — Authentication System

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
from pydantic import BaseModel, EmailStr
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import os
import secrets

load_dotenv()

router = APIRouter()

# ─────────────────────────────────────────
# SECURITY CONFIG
# ─────────────────────────────────────────
SECRET_KEY = os.getenv('JWT_SECRET_KEY')
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7
RESET_TOKEN_EXPIRE_MINUTES = 15
MAX_LOGIN_ATTEMPTS = 5

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

def get_engine():
    return create_engine(os.getenv('DB_URL'))

# ─────────────────────────────────────────
# MODELS
# ─────────────────────────────────────────
class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    role: str = "viewer"

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str
    expires_in: int

class PasswordReset(BaseModel):
    token: str
    new_password: str

# ─────────────────────────────────────────
# PASSWORD UTILITIES
# ─────────────────────────────────────────
def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire, "iat": datetime.utcnow()})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def create_reset_token() -> str:
    return secrets.token_urlsafe(32)

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

def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = get_user_by_email(email)
    if user is None:
        raise credentials_exception
    return user

def require_admin(current_user=Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user

# ─────────────────────────────────────────
# LOGIN ATTEMPT TRACKING
# ─────────────────────────────────────────
login_attempts = {}

def check_login_attempts(email: str):
    attempts = login_attempts.get(email, {"count": 0, "locked_until": None})
    if attempts["locked_until"] and datetime.utcnow() < attempts["locked_until"]:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Account locked. Try again after {attempts['locked_until'].strftime('%H:%M:%S')}"
        )

def record_failed_attempt(email: str):
    attempts = login_attempts.get(email, {"count": 0, "locked_until": None})
    attempts["count"] += 1
    if attempts["count"] >= MAX_LOGIN_ATTEMPTS:
        attempts["locked_until"] = datetime.utcnow() + timedelta(minutes=15)
        attempts["count"] = 0
    login_attempts[email] = attempts

def clear_login_attempts(email: str):
    login_attempts.pop(email, None)

# ─────────────────────────────────────────
# AUTH ENDPOINTS
# ─────────────────────────────────────────
@router.post("/register", status_code=201)
def register(user: UserCreate):
    existing = get_user_by_email(user.email)
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed = hash_password(user.password)
    verification_token = create_reset_token()
    engine = get_engine()

    with engine.begin() as conn:
        conn.execute(text("""
            INSERT INTO users (email, password_hash, full_name, role,
                             is_verified, verification_token, created_at)
            VALUES (:email, :password_hash, :full_name, :role,
                    false, :verification_token, NOW())
        """), {
            "email": user.email,
            "password_hash": hashed,
            "full_name": user.full_name,
            "role": user.role,
            "verification_token": verification_token
        })

    return {
        "message": "Registration successful. Please verify your email.",
        "verification_token": verification_token
    }

@router.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    check_login_attempts(form_data.username)
    user = get_user_by_email(form_data.username)

    if not user or not verify_password(form_data.password, user.password_hash):
        record_failed_attempt(form_data.username)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )

    if not user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Please verify your email before logging in"
        )

    clear_login_attempts(form_data.username)
    access_token = create_access_token(data={"sub": user.email, "role": user.role})

    # Log login attempt
    engine = get_engine()
    with engine.begin() as conn:
        conn.execute(text("""
            INSERT INTO auth_logs (email, action, status, created_at)
            VALUES (:email, 'login', 'success', NOW())
        """), {"email": user.email})

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60
    }

@router.get("/verify/{token}")
def verify_email(token: str):
    engine = get_engine()
    with engine.connect() as conn:
        user = conn.execute(
            text("SELECT * FROM users WHERE verification_token = :token"),
            {"token": token}
        ).fetchone()

    if not user:
        raise HTTPException(status_code=400, detail="Invalid verification token")

    with engine.begin() as conn:
        conn.execute(text("""
            UPDATE users SET is_verified = true,
            verification_token = null WHERE id = :id
        """), {"id": user.id})

    return {"message": "Email verified successfully. You can now log in."}

@router.post("/forgot-password")
def forgot_password(email: str):
    user = get_user_by_email(email)
    if not user:
        return {"message": "If that email exists, a reset link has been sent."}

    reset_token = create_reset_token()
    expires_at = datetime.utcnow() + timedelta(minutes=RESET_TOKEN_EXPIRE_MINUTES)
    engine = get_engine()

    with engine.begin() as conn:
        conn.execute(text("""
            UPDATE users SET reset_token = :token,
            reset_token_expires = :expires WHERE email = :email
        """), {"token": reset_token, "expires": expires_at, "email": email})

    return {
        "message": "Reset link sent.",
        "reset_token": reset_token,
        "expires_in_minutes": RESET_TOKEN_EXPIRE_MINUTES
    }

@router.post("/reset-password")
def reset_password(data: PasswordReset):
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
            UPDATE users SET password_hash = :hashed,
            reset_token = null, reset_token_expires = null
            WHERE id = :id
        """), {"hashed": hashed, "id": user.id})

    return {"message": "Password reset successfully."}

@router.get("/me")
def get_me(current_user=Depends(get_current_user)):
    return {
        "email": current_user.email,
        "full_name": current_user.full_name,
        "role": current_user.role,
        "is_verified": current_user.is_verified
    }