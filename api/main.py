# main.py
# Rubis POS — Main Application (Secured)

import sys
import io

# Fix Windows console encoding (prevents UnicodeEncodeError with special chars)
if sys.stdout and hasattr(sys.stdout, 'buffer'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
if sys.stderr and hasattr(sys.stderr, 'buffer'):
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from fastapi import FastAPI, Depends, Request, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import HTMLResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from sqlalchemy import create_engine, text
from pydantic import BaseModel, validator
from dotenv import load_dotenv
from api.auth import get_current_user, require_admin, require_role, router as auth_router
import pandas as pd
import logging
import re
import os

load_dotenv()

# ─────────────────────────────────────────
# LOGGING
# ─────────────────────────────────────────
os.makedirs("logs", exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler("logs/app.log", encoding="utf-8"),  # force UTF-8 in log file
        logging.StreamHandler(stream=sys.stdout)                # use our UTF-8 stdout
    ]
)
logger = logging.getLogger("rubis.main")

# ─────────────────────────────────────────
# APP + RATE LIMITER
# ─────────────────────────────────────────
limiter = Limiter(key_func=get_remote_address, default_limits=["200/minute"])
app = FastAPI(
    title="Rubis Retail Intelligence System",
    version="1.0.0",
    docs_url="/docs" if os.getenv("ENV") != "production" else None,
    redoc_url=None,
)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.include_router(auth_router, prefix="/auth", tags=["Authentication"])

# ─────────────────────────────────────────
# CORS
# ─────────────────────────────────────────
ALLOWED_ORIGINS = [o.strip() for o in os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")
)

# ─────────────────────────────────────────
# SECURITY HEADERS
# ─────────────────────────────────────────
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline'; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data:; "
        "connect-src 'self'"
    )
    return response

# ─────────────────────────────────────────
# REQUEST LOGGING MIDDLEWARE
# FIX: replaced -> instead of special arrow char (Windows cp1252 safe)
# ─────────────────────────────────────────
@app.middleware("http")
async def log_requests(request: Request, call_next):
    response = await call_next(request)
    if response.status_code >= 400:
        logger.warning(
            "%s %s -> %s | IP: %s",
            request.method,
            request.url.path,
            response.status_code,
            request.client.host if request.client else "unknown"
        )
    return response

# ─────────────────────────────────────────
# DATABASE
# ─────────────────────────────────────────
# ─────────────────────────────────────────
# DATABASE + AUTO-CREATE TABLES
# ─────────────────────────────────────────
def get_engine():
    return create_engine(os.getenv("DB_URL"), pool_pre_ping=True)

def init_db():
    """Create all required tables if they don't exist."""
    engine = get_engine()
    with engine.connect() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                email VARCHAR(255) UNIQUE NOT NULL,
                hashed_password TEXT NOT NULL,
                full_name VARCHAR(255),
                role VARCHAR(50) DEFAULT 'viewer',
                branch VARCHAR(100),
                is_verified BOOLEAN DEFAULT FALSE,
                is_active BOOLEAN DEFAULT TRUE,
                verification_token TEXT,
                reset_token TEXT,
                reset_token_expires TIMESTAMP,
                failed_login_attempts INTEGER DEFAULT 0,
                locked_until TIMESTAMP,
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW()
            )
        """))
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS auth_logs (
                id SERIAL PRIMARY KEY,
                email VARCHAR(255),
                action VARCHAR(100) NOT NULL,
                ip_address VARCHAR(45),
                user_agent TEXT,
                success BOOLEAN DEFAULT TRUE,
                details TEXT,
                created_at TIMESTAMP DEFAULT NOW()
            )
        """))
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS refresh_tokens (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                token TEXT UNIQUE NOT NULL,
                expires_at TIMESTAMP NOT NULL,
                created_at TIMESTAMP DEFAULT NOW()
            )
        """))
        conn.commit()
    logger.info("Database tables verified/created successfully")

# Run on startup
@app.on_event("startup")
def on_startup():
    init_db()
SAFE_BRANCH_PATTERN = re.compile(r"^[a-zA-Z0-9\s&\-]{1,60}$")

def validate_branch(branch: str) -> str:
    if not SAFE_BRANCH_PATTERN.match(branch):
        from fastapi import HTTPException
        raise HTTPException(status_code=422, detail="Invalid branch name")
    return branch

def validate_limit(limit: int) -> int:
    if limit < 1 or limit > 500:
        return 20
    return limit

# ─────────────────────────────────────────
# STATIC AUTH PAGE
# ─────────────────────────────────────────
@app.get("/login", response_class=HTMLResponse, include_in_schema=False)
def login_page():
    template_path = os.path.join("api", "templates", "auth.html")
    if not os.path.exists(template_path):
        return HTMLResponse("<h1>Template not found</h1>", status_code=404)
    with open(template_path, "r", encoding="utf-8") as f:
        return f.read()

# ─────────────────────────────────────────
# HEALTH CHECK
# ─────────────────────────────────────────
@app.get("/")
def health_check():
    return {"status": "ok", "system": "Rubis Retail Intelligence"}

# ─────────────────────────────────────────
# SUMMARY
# ─────────────────────────────────────────
@app.get("/summary")
@limiter.limit("60/minute")
def get_summary(request: Request, current_user=Depends(get_current_user)):
    engine = get_engine()
    with engine.connect() as conn:
        total_rows = conn.execute(text("SELECT COUNT(*) FROM pos_sales")).scalar()
        total_branches = conn.execute(text("SELECT COUNT(DISTINCT branch) FROM pos_sales")).scalar()
        total_revenue = conn.execute(text("SELECT ROUND(SUM(net_sale)::NUMERIC, 2) FROM pos_sales")).scalar()
        total_products = conn.execute(text("SELECT COUNT(DISTINCT sku_code) FROM pos_sales")).scalar()
        last_load = conn.execute(text("SELECT MAX(loaded_at) FROM pos_sales")).scalar()
    return {
        "total_rows": total_rows,
        "total_branches": total_branches,
        "total_net_revenue": float(total_revenue or 0),
        "total_unique_products": total_products,
        "last_pipeline_run": str(last_load)
    }

# ─────────────────────────────────────────
# BRANCH PERFORMANCE
# Admins see all branches; branch managers see only their branch
# ─────────────────────────────────────────
@app.get("/branches")
@limiter.limit("60/minute")
def get_branch_performance(request: Request, current_user=Depends(get_current_user)):
    engine = get_engine()
    if current_user.role == "admin":
        df = pd.read_sql("SELECT * FROM vw_branch_performance", engine)
    else:
        assigned = current_user.branch if hasattr(current_user, "branch") else None
        if not assigned:
            return []
        df = pd.read_sql(
            "SELECT * FROM vw_branch_performance WHERE branch = %(branch)s",
            engine,
            params={"branch": assigned}
        )
    return df.to_dict(orient="records")

# ─────────────────────────────────────────
# DEPARTMENTS
# ─────────────────────────────────────────
@app.get("/departments")
@limiter.limit("60/minute")
def get_department_performance(request: Request, current_user=Depends(get_current_user)):
    engine = get_engine()
    df = pd.read_sql("SELECT * FROM vw_department_performance", engine)
    return df.to_dict(orient="records")

# ─────────────────────────────────────────
# PRODUCTS
# ─────────────────────────────────────────
@app.get("/products/top")
@limiter.limit("60/minute")
def get_top_products(
    request: Request,
    limit: int = Query(default=20, ge=1, le=500),
    current_user=Depends(get_current_user)
):
    engine = get_engine()
    df = pd.read_sql(
        "SELECT * FROM vw_top_products LIMIT %(limit)s",
        engine,
        params={"limit": limit}
    )
    return df.to_dict(orient="records")

@app.get("/products/low-margin")
@limiter.limit("60/minute")
def get_low_margin_products(request: Request, current_user=Depends(get_current_user)):
    engine = get_engine()
    df = pd.read_sql("SELECT * FROM vw_low_margin_products", engine)
    return df.to_dict(orient="records")

@app.get("/products/high-value")
@limiter.limit("60/minute")
def get_high_value_products(request: Request, current_user=Depends(get_current_user)):
    engine = get_engine()
    df = pd.read_sql("SELECT * FROM vw_high_value_products", engine)
    return df.to_dict(orient="records")

# ─────────────────────────────────────────
# BRANCH x DEPARTMENT
# ─────────────────────────────────────────
@app.get("/branch-department")
@limiter.limit("30/minute")
def get_branch_department(request: Request, current_user=Depends(get_current_user)):
    engine = get_engine()
    df = pd.read_sql("SELECT * FROM vw_branch_department", engine)
    df = df.fillna(0)
    return df.to_dict(orient="records")

# ─────────────────────────────────────────
# ANOMALIES  (admin/analyst only)
# ─────────────────────────────────────────
@app.get("/anomalies")
@limiter.limit("30/minute")
def get_anomalies(
    request: Request,
    current_user=Depends(require_role("admin", "analyst"))
):
    engine = get_engine()
    df = pd.read_sql("""
        SELECT * FROM pos_sales
        WHERE margin_pct < 10
          AND margin_pct IS NOT NULL
          AND net_sale > 0
        ORDER BY margin_pct ASC
        LIMIT 500
    """, engine)
    return df.to_dict(orient="records")

@app.get("/anomalies/critical")
@limiter.limit("20/minute")
def get_critical_anomalies(
    request: Request,
    current_user=Depends(require_role("admin", "analyst"))
):
    engine = get_engine()
    df = pd.read_sql("""
        WITH dept_avg AS (
            SELECT department,
                   AVG(margin_pct)    AS dept_avg,
                   STDDEV(margin_pct) AS dept_std
            FROM pos_sales
            WHERE margin_pct IS NOT NULL
            GROUP BY department
        )
        SELECT
            p.sku_code, p.product_name, p.branch, p.department,
            p.margin_pct,
            d.dept_avg AS dept_avg_margin,
            ROUND(((p.margin_pct - d.dept_avg) / NULLIF(d.dept_std, 0))::NUMERIC, 2) AS z_score,
            ROUND(((p.margin_pct - d.dept_avg) * p.net_sale / 100)::NUMERIC, 2) AS revenue_impact
        FROM pos_sales p
        JOIN dept_avg d ON p.department = d.department
        WHERE ((p.margin_pct - d.dept_avg) / NULLIF(d.dept_std, 0)) < -2
        ORDER BY z_score ASC
        LIMIT 200
    """, engine)
    return df.to_dict(orient="records")

# ─────────────────────────────────────────
# STOCKOUT
# ─────────────────────────────────────────
@app.get("/stockout/critical")
@limiter.limit("20/minute")
def get_critical_stockout(request: Request, current_user=Depends(get_current_user)):
    engine = get_engine()
    df = pd.read_sql("""
        WITH dept_avg AS (
            SELECT department,
                   AVG(quantity)    AS dept_avg_qty,
                   STDDEV(quantity) AS dept_std_qty
            FROM pos_sales
            WHERE quantity > 0
            GROUP BY department
        )
        SELECT
            p.sku_code, p.product_name, p.branch, p.department,
            p.quantity, p.net_sale,
            ROUND(((p.quantity - d.dept_avg_qty) / NULLIF(d.dept_std_qty, 0))::NUMERIC, 2) AS velocity_score
        FROM pos_sales p
        JOIN dept_avg d ON p.department = d.department
        WHERE ((p.quantity - d.dept_avg_qty) / NULLIF(d.dept_std_qty, 0)) > 2
        ORDER BY velocity_score DESC
        LIMIT 50
    """, engine)
    return df.to_dict(orient="records")

# ─────────────────────────────────────────
# FORECAST
# ─────────────────────────────────────────
@app.get("/forecast")
@limiter.limit("20/minute")
def get_revenue_forecast(request: Request, current_user=Depends(get_current_user)):
    engine = get_engine()
    df = pd.read_sql("""
        SELECT
            branch,
            ROUND(SUM(net_sale)::NUMERIC, 2)            AS current_revenue,
            ROUND(SUM(net_sale)::NUMERIC * 1.05, 2)     AS month1_target,
            ROUND(SUM(net_sale)::NUMERIC * 1.1025, 2)   AS month2_target,
            ROUND(SUM(net_sale)::NUMERIC * 1.157625, 2) AS month3_target,
            ROUND(AVG(margin_pct)::NUMERIC, 2)          AS avg_margin
        FROM pos_sales
        WHERE net_sale IS NOT NULL
        GROUP BY branch
        ORDER BY current_revenue DESC
    """, engine)
    return df.to_dict(orient="records")
