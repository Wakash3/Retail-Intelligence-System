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
from api.chat import router as chat_router
from apscheduler.schedulers.background import BackgroundScheduler
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
        logging.FileHandler("logs/app.log", encoding="utf-8"),
        logging.StreamHandler(stream=sys.stdout)
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
    docs_url="/docs",
    redoc_url="/redoc",
)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.include_router(auth_router, prefix="/auth", tags=["Authentication"])
app.include_router(chat_router, prefix="/api", tags=["Chat"])

# ─────────────────────────────────────────
# CORS — includes Next.js (3000, 3001) and Streamlit (8501)
# ─────────────────────────────────────────
ALLOWED_ORIGINS = [o.strip() for o in os.getenv(
    "ALLOWED_ORIGINS",
    "http://localhost:3000,http://127.0.0.1:3000,"
    "http://localhost:3001,http://127.0.0.1:3001,"
    "http://localhost:8501,http://127.0.0.1:8501"
).split(",")]

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
    return response

# ─────────────────────────────────────────
# REQUEST LOGGING MIDDLEWARE
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
# DATABASE + AUTO-CREATE TABLES
# ─────────────────────────────────────────
def get_engine():
    db_url = os.getenv("DB_URL")
    if not db_url:
        logger.error("DB_URL is not set in your .env file!")
        raise RuntimeError("DB_URL environment variable is missing. Check your .env file.")
    return create_engine(db_url, pool_pre_ping=True)

def init_db():
    """Create all required tables if they don't exist."""
    engine = get_engine()
    with engine.connect() as conn:
        # Users table
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

        # Auth logs table
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

        # Refresh tokens table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS refresh_tokens (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                token TEXT UNIQUE NOT NULL,
                expires_at TIMESTAMP NOT NULL,
                created_at TIMESTAMP DEFAULT NOW()
            )
        """))

        # Indexes
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_auth_logs_email ON auth_logs(email)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_auth_logs_created ON auth_logs(created_at)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_refresh_tokens_token ON refresh_tokens(token)"))

        conn.commit()
    logger.info("Database tables verified/created successfully")

# ─────────────────────────────────────────
# ALERT FUNCTIONS
# ─────────────────────────────────────────
def run_all_alerts():
    """Run all alert checks and return results"""
    results = {"margin": False, "stockout": False, "revenue": False}

    try:
        from alerts import check_margin_alerts, check_stockout_alerts, check_revenue_targets

        logger.info("Running margin alerts...")
        results["margin"] = check_margin_alerts()

        logger.info("Running stockout alerts...")
        results["stockout"] = check_stockout_alerts()

        logger.info("Running revenue target alerts...")
        results["revenue"] = check_revenue_targets()

        logger.info(f"Alert run complete: {results}")
        return results

    except Exception as e:
        logger.error(f"Error running alerts: {e}")
        return {"error": str(e)}

# ─────────────────────────────────────────
# STARTUP — DB init + Alert scheduler
# ─────────────────────────────────────────
scheduler = None

@app.on_event("startup")
def on_startup():
    global scheduler
    init_db()

    interval = int(os.getenv("ALERT_CHECK_INTERVAL_MINUTES", "60"))
    scheduler = BackgroundScheduler()
    scheduler.add_job(run_all_alerts, "interval", minutes=interval)
    scheduler.start()
    logger.info("Alert scheduler started — checking every %d minutes", interval)

@app.on_event("shutdown")
def shutdown_event():
    global scheduler
    if scheduler:
        scheduler.shutdown()
        logger.info("Alert scheduler shut down")

# ─────────────────────────────────────────
# VALIDATION HELPERS
# ─────────────────────────────────────────
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
    return {
        "status": "ok",
        "system": "Rubis Retail Intelligence",
        "message": "API is running"
    }

# ─────────────────────────────────────────
# DEBUG ENDPOINT - Check user role
# ─────────────────────────────────────────
@app.get("/debug/my-role", tags=["Debug"])
def debug_my_role(current_user=Depends(get_current_user)):
    return {
        "email": current_user.email,
        "role": current_user.role,
        "user_id": current_user.id,
        "is_active": current_user.is_active,
        "branch": current_user.branch if hasattr(current_user, "branch") else None
    }

# ─────────────────────────────────────────
# ALERTS — Manual trigger endpoint
# ─────────────────────────────────────────
@app.get("/alerts/run", tags=["Alerts"])
@limiter.limit("5/minute")
def trigger_alerts_manually(
    request: Request,
    current_user=Depends(require_role("admin", "analyst"))
):
    """Manually trigger all alert checks. Restricted to admin and analyst roles."""
    result = run_all_alerts()
    return result

# ─────────────────────────────────────────
# ALERTS — Test endpoint
# ─────────────────────────────────────────
@app.post("/alerts/test", tags=["Alerts"])
def test_alerts(current_user=Depends(require_admin)):
    """Send test alerts to verify system (admin only)"""
    try:
        from alerts import send_alert

        test_message = """
        🔶 Rubis Intelligence Test Alert 🔶

        This is a test alert to verify the alert system is working correctly.

        Test Details:
        - Time: {time}
        - User: {user}
        - System: Rubis Intelligence

        If you received this, the alert system is functioning properly.
        """.format(
            time=__import__('datetime').datetime.now(),
            user=current_user.email
        )

        send_alert("TEST ALERT - System Test", test_message)

        return {
            "message": "Test alert sent successfully",
            "status": "success",
            "details": "Email alert sent to configured recipients"
        }
    except Exception as e:
        logger.error(f"Test alert failed: {e}")
        return {"error": str(e), "status": "failed"}

# ─────────────────────────────────────────
# SUMMARY
# ─────────────────────────────────────────
@app.get("/summary")
@limiter.limit("60/minute")
def get_summary(request: Request, current_user=Depends(get_current_user)):
    engine = get_engine()
    with engine.connect() as conn:
        total_rows     = conn.execute(text("SELECT COUNT(*) FROM pos_sales")).scalar()
        total_branches = conn.execute(text("SELECT COUNT(DISTINCT branch) FROM pos_sales")).scalar()
        total_revenue  = conn.execute(text("SELECT ROUND(SUM(net_sale)::NUMERIC, 2) FROM pos_sales")).scalar()
        total_products = conn.execute(text("SELECT COUNT(DISTINCT sku_code) FROM pos_sales")).scalar()
        last_load      = conn.execute(text("SELECT MAX(loaded_at) FROM pos_sales")).scalar()
    return {
        "total_rows": total_rows,
        "total_branches": total_branches,
        "total_net_revenue": float(total_revenue or 0),
        "total_unique_products": total_products,
        "last_pipeline_run": str(last_load)
    }

# ─────────────────────────────────────────
# BRANCH PERFORMANCE
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
# ANOMALIES (admin/analyst only)
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
            ROUND(((p.margin_pct - d.dept_avg) * p.net_sale / 100)::NUMERIC, 2)      AS revenue_impact
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

# ─────────────────────────────────────────
# SCORECARD
# ─────────────────────────────────────────
@app.get("/scorecard", tags=["Scorecard"])
@limiter.limit("30/minute")
def get_branch_scorecard(request: Request, current_user=Depends(get_current_user)):
    engine = get_engine()
    df = pd.read_sql("""
        SELECT
            branch,
            ROUND(SUM(net_sale)::NUMERIC, 2)                          AS total_revenue,
            ROUND(AVG(margin_pct)::NUMERIC, 2)                        AS avg_margin,
            COUNT(DISTINCT sku_code)                                   AS product_variety,
            ROUND(SUM(net_contribution)::NUMERIC, 2)                   AS total_contribution,
            COUNT(CASE WHEN margin_pct < 5 THEN 1 END)                 AS low_margin_count,
            ROUND(SUM(net_sale) * 100.0 /
                NULLIF(SUM(SUM(net_sale)) OVER (), 0), 2)              AS revenue_share_pct
        FROM pos_sales
        WHERE net_sale IS NOT NULL
        GROUP BY branch
        ORDER BY total_revenue DESC
    """, engine)

    if df.empty:
        return []

    def normalise(series, invert=False):
        mn, mx = series.min(), series.max()
        if mx == mn:
            return pd.Series([50.0] * len(series), index=series.index)
        scaled = (series - mn) / (mx - mn) * 100
        return (100 - scaled) if invert else scaled

    df["score_revenue"]  = normalise(df["total_revenue"]).round(1)
    df["score_margin"]   = normalise(df["avg_margin"]).round(1)
    df["score_variety"]  = normalise(df["product_variety"]).round(1)
    df["score_stockout"] = normalise(df["low_margin_count"], invert=True).round(1)

    df["composite_score"] = (
        df["score_revenue"]  * 0.35 +
        df["score_margin"]   * 0.30 +
        df["score_variety"]  * 0.15 +
        df["score_stockout"] * 0.20
    ).round(1)

    # Sort by total revenue (highest to lowest)
    df = df.sort_values("total_revenue", ascending=False).reset_index(drop=True)
    df["rank"] = df.index + 1

    return df.to_dict(orient="records")

# ─────────────────────────────────────────
# RECOMMENDATIONS
# ─────────────────────────────────────────
@app.get("/recommendations/{branch}", tags=["Recommendations"])
@limiter.limit("20/minute")
def get_recommendations_for_branch(
    request: Request,
    branch: str,
    limit: int = Query(default=5, ge=1, le=20),
    current_user=Depends(get_current_user)
):
    branch = validate_branch(branch)
    engine = get_engine()

    df = pd.read_sql("""
        SELECT branch, product_name, sku_code,
               SUM(quantity)  AS total_qty,
               SUM(net_sale)  AS total_revenue
        FROM pos_sales
        GROUP BY branch, product_name, sku_code
    """, engine)

    if df.empty:
        return []

    # Auto-detect top branch by revenue
    top_branch = (
        df.groupby("branch")["total_revenue"]
        .sum()
        .idxmax()
    )

    # Products the top branch sells
    top_products = df[df["branch"] == top_branch][
        ["product_name", "sku_code", "total_qty", "total_revenue"]
    ].copy()

    # Products the target branch already sells
    branch_skus = set(df[df["branch"] == branch]["sku_code"].tolist())

    # Missing = top branch sells but target branch doesn't
    missing = top_products[~top_products["sku_code"].isin(branch_skus)]
    missing = missing.sort_values("total_revenue", ascending=False).head(limit)

    return {
        "branch": branch,
        "benchmark_branch": top_branch,
        "recommendations": missing.rename(columns={
            "total_qty":     "qty_at_benchmark",
            "total_revenue": "revenue_at_benchmark"
        }).to_dict(orient="records")
    }

# ─────────────────────────────────────────
# DATA QUALITY
# ─────────────────────────────────────────
@app.get("/data-quality", tags=["Data Quality"])
@limiter.limit("20/minute")
def get_data_quality(
    request: Request,
    current_user=Depends(require_role("admin", "analyst"))
):
    engine = get_engine()

    with engine.connect() as conn:
        total = conn.execute(
            text("SELECT COUNT(*) FROM pos_sales")
        ).scalar() or 1

        results = conn.execute(text("""
            SELECT
                COUNT(*)                                                         AS total_rows,
                COUNT(*) FILTER (WHERE branch IS NULL)                           AS null_branch,
                COUNT(*) FILTER (WHERE product_name IS NULL)                     AS null_product,
                COUNT(*) FILTER (WHERE net_sale IS NULL OR net_sale = 0)         AS null_revenue,
                COUNT(*) FILTER (WHERE margin_pct IS NULL)                       AS null_margin,
                COUNT(*) FILTER (WHERE cost_ex_vat IS NULL)                      AS null_cost,
                COUNT(*) FILTER (WHERE sales_date IS NULL)                       AS null_date,
                COUNT(*) FILTER (WHERE quantity IS NULL OR quantity = 0)         AS null_quantity,
                COUNT(*) FILTER (WHERE net_sale < 0)                             AS negative_revenue,
                COUNT(*) FILTER (WHERE margin_pct < 0)                           AS negative_margin,
                COUNT(DISTINCT source_file)                                      AS source_files_loaded,
                MAX(loaded_at)                                                   AS last_loaded_at,
                MIN(sales_date)                                                  AS earliest_sale,
                MAX(sales_date)                                                  AS latest_sale
            FROM pos_sales
        """)).fetchone()

    row = dict(results._mapping)
    total_rows = row["total_rows"] or 1

    def pct(n):
        return round((n / total_rows) * 100, 2)

    columns = [
        {"column": "branch",         "null_count": row["null_branch"],      "null_pct": pct(row["null_branch"]),      "status": "FAIL" if pct(row["null_branch"])    > 2 else "OK"},
        {"column": "product_name",   "null_count": row["null_product"],     "null_pct": pct(row["null_product"]),     "status": "FAIL" if pct(row["null_product"])   > 2 else "OK"},
        {"column": "net_sale",       "null_count": row["null_revenue"],     "null_pct": pct(row["null_revenue"]),     "status": "FAIL" if pct(row["null_revenue"])   > 2 else "OK"},
        {"column": "margin_pct",     "null_count": row["null_margin"],      "null_pct": pct(row["null_margin"]),      "status": "FAIL" if pct(row["null_margin"])    > 5 else "OK"},
        {"column": "cost_ex_vat",    "null_count": row["null_cost"],        "null_pct": pct(row["null_cost"]),        "status": "FAIL" if pct(row["null_cost"])      > 5 else "OK"},
        {"column": "sales_date",     "null_count": row["null_date"],        "null_pct": pct(row["null_date"]),        "status": "FAIL" if pct(row["null_date"])      > 1 else "OK"},
        {"column": "quantity",       "null_count": row["null_quantity"],    "null_pct": pct(row["null_quantity"]),    "status": "FAIL" if pct(row["null_quantity"])  > 2 else "OK"},
        {"column": "net_sale (neg)", "null_count": row["negative_revenue"], "null_pct": pct(row["negative_revenue"]), "status": "WARN" if row["negative_revenue"]   > 0 else "OK"},
        {"column": "margin (neg)",   "null_count": row["negative_margin"],  "null_pct": pct(row["negative_margin"]),  "status": "WARN" if row["negative_margin"]    > 0 else "OK"},
    ]

    return {
        "total_rows":          total_rows,
        "source_files_loaded": row["source_files_loaded"],
        "last_loaded_at":      str(row["last_loaded_at"]),
        "earliest_sale":       str(row["earliest_sale"]),
        "latest_sale":         str(row["latest_sale"]),
        "columns":             columns,
        "overall_status":      "FAIL" if any(c["status"] == "FAIL" for c in columns) else "OK"
    }





