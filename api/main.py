# api/main.py
# Rubis POS — FastAPI Layer (Secured)

from fastapi import FastAPI, Depends, Request
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from sqlalchemy import create_engine, text
from pydantic import BaseModel, validator
from dotenv import load_dotenv
from api.auth import get_current_user, require_admin, router as auth_router
import pandas as pd
import re
import os

load_dotenv()

# ─────────────────────────────────────────
# APP SETUP
# ─────────────────────────────────────────
limiter = Limiter(key_func=get_remote_address)
app = FastAPI(title="Retail Intelligence System", version="1.0.0")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.include_router(auth_router, prefix="/auth", tags=["Authentication"])
app.add_middleware(TrustedHostMiddleware, allowed_hosts=["localhost", "127.0.0.1", "*"])

# ─────────────────────────────────────────
# SECURITY HEADERS
# ─────────────────────────────────────────
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000"
    return response

# ─────────────────────────────────────────
# INPUT VALIDATION MODELS
# ─────────────────────────────────────────
class ProductFilter(BaseModel):
    branch: str = None
    department: str = None
    limit: int = 20

    @validator('branch', 'department')
    def sanitize_string(cls, v):
        if v and not re.match(r'^[a-zA-Z0-9\s&\-]+$', v):
            raise ValueError('Invalid characters in filter')
        return v

    @validator('limit')
    def validate_limit(cls, v):
        if v < 1 or v > 1000:
            raise ValueError('Limit must be between 1 and 1000')
        return v

# ─────────────────────────────────────────
# DATABASE
# ─────────────────────────────────────────
def get_engine():
    return create_engine(os.getenv('DB_URL'))

# ─────────────────────────────────────────
# ENDPOINTS
# ─────────────────────────────────────────
@app.get("/")
def health_check():
    return {"status": "ok", "message": "Retail Intelligence System is running"}

@app.get("/summary")
def get_summary(current_user=Depends(get_current_user)):
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
        "total_net_revenue": float(total_revenue),
        "total_unique_products": total_products,
        "last_pipeline_run": str(last_load)
    }

@app.get("/branches")
def get_branch_performance(current_user=Depends(get_current_user)):
    engine = get_engine()
    df = pd.read_sql("SELECT * FROM vw_branch_performance", engine)
    return df.to_dict(orient='records')

@app.get("/departments")
def get_department_performance(current_user=Depends(get_current_user)):
    engine = get_engine()
    df = pd.read_sql("SELECT * FROM vw_department_performance", engine)
    return df.to_dict(orient='records')

@app.get("/products/top")
def get_top_products(limit: int = 20, current_user=Depends(get_current_user)):
    if limit < 1 or limit > 1000:
        limit = 20
    engine = get_engine()
    df = pd.read_sql(f"SELECT * FROM vw_top_products LIMIT {limit}", engine)
    return df.to_dict(orient='records')

@app.get("/products/low-margin")
def get_low_margin_products(current_user=Depends(get_current_user)):
    engine = get_engine()
    df = pd.read_sql("SELECT * FROM vw_low_margin_products", engine)
    return df.to_dict(orient='records')

@app.get("/products/high-value")
def get_high_value_products(current_user=Depends(get_current_user)):
    engine = get_engine()
    df = pd.read_sql("SELECT * FROM vw_high_value_products", engine)
    return df.to_dict(orient='records')

@app.get("/branch-department")
def get_branch_department(current_user=Depends(get_current_user)):
    engine = get_engine()
    df = pd.read_sql("SELECT * FROM vw_branch_department", engine)
    df = df.fillna(0)
    return df.to_dict(orient='records')

@app.get("/anomalies")
def get_anomalies(current_user=Depends(get_current_user)):
    engine = get_engine()
    df = pd.read_sql("""
        SELECT * FROM pos_sales
        WHERE margin_pct < 10
          AND margin_pct IS NOT NULL
          AND net_sale > 0
        ORDER BY margin_pct ASC
    """, engine)
    return df.to_dict(orient='records')

@app.get("/anomalies/critical")
def get_critical_anomalies(current_user=Depends(get_current_user)):
    engine = get_engine()
    df = pd.read_sql("""
        WITH dept_avg AS (
            SELECT department,
                   AVG(margin_pct) AS dept_avg,
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
    """, engine)
    return df.to_dict(orient='records')

@app.get("/stockout/critical")
def get_critical_stockout(current_user=Depends(get_current_user)):
    engine = get_engine()
    df = pd.read_sql("""
        WITH dept_avg AS (
            SELECT department,
                   AVG(quantity) AS dept_avg_qty,
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
    return df.to_dict(orient='records')

@app.get("/forecast")
def get_revenue_forecast(current_user=Depends(get_current_user)):
    engine = get_engine()
    df = pd.read_sql("""
        SELECT
            branch,
            ROUND(SUM(net_sale)::NUMERIC, 2) AS current_revenue,
            ROUND(SUM(net_sale)::NUMERIC * 1.05, 2) AS month1_target,
            ROUND(SUM(net_sale)::NUMERIC * 1.1025, 2) AS month2_target,
            ROUND(SUM(net_sale)::NUMERIC * 1.157625, 2) AS month3_target,
            ROUND(AVG(margin_pct)::NUMERIC, 2) AS avg_margin
        FROM pos_sales
        WHERE net_sale IS NOT NULL
        GROUP BY branch
        ORDER BY current_revenue DESC
    """, engine)
    return df.to_dict(orient='records')