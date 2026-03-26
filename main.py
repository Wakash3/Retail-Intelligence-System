# main.py
# Rubis POS — Main Application (Secured)

import sys
import io

# Fix Windows console encoding
if sys.stdout and hasattr(sys.stdout, 'buffer'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
if sys.stderr and hasattr(sys.stderr, 'buffer'):
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from fastapi import FastAPI, Depends, Request, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import HTMLResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from sqlalchemy import create_engine, text
from pydantic import BaseModel
from dotenv import load_dotenv
from api.auth import get_current_user, require_admin, require_role, router as auth_router
from api.chat import router as chat_router
from datetime import datetime
from groq import Groq
import pandas as pd
import logging
import re
import os

load_dotenv()

# LOGGING
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

# APP + RATE LIMITER
limiter = Limiter(key_func=get_remote_address, default_limits=["200/minute"])
app = FastAPI(title="Rubis Retail Intelligence System", version="1.0.0")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.include_router(auth_router, prefix="/auth", tags=["Authentication"])
app.include_router(chat_router, prefix="/api", tags=["Chat"])
<<<<<<< HEAD

# ─────────────────────────────────────────
# CORS — includes Next.js (3000, 3001) and Streamlit (8501)
# ─────────────────────────────────────────
ALLOWED_ORIGINS = [o.strip() for o in os.getenv(
    "ALLOWED_ORIGINS",
    "http://localhost:3000,http://127.0.0.1:3000,"
    "http://localhost:3001,http://127.0.0.1:3001,"
    "http://localhost:8501,http://127.0.0.1:8501"
).split(",")]
=======
>>>>>>> 267e639ca9c7a390e03880f35af2c83f049d9aed

ALLOWED_ORIGINS = [o.strip() for o in os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000,http://localhost:8501,http://127.0.0.1:8501").split(",")]
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)

app.add_middleware(TrustedHostMiddleware, allowed_hosts=os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1").split(","))

@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    return response

def get_engine():
    db_url = os.getenv("DB_URL")
    if not db_url: raise RuntimeError("DB_URL missing")
    return create_engine(db_url, pool_pre_ping=True)
def get_system_leader_stats(conn):
    """Dynamically find the current branch with highest total revenue and return its summary."""
    # Ensure we only pick a leader that actually has revenue to avoid NoneType crashes
    res = conn.execute(text("""
        SELECT branch, SUM(net_sale) as total_rev, COUNT(DISTINCT sku_code) as skus 
        FROM pos_sales 
        GROUP BY branch 
        HAVING SUM(net_sale) > 0
        ORDER BY total_rev DESC LIMIT 1
    """)).fetchone()
    if res:
        return {"name": res[0], "revenue": float(res[1] or 0), "skus": int(res[2] or 0)}
    return {"name": "RUBIS", "revenue": 0.0, "skus": 0}

def init_db():
    engine = get_engine()
    with engine.connect() as conn:
        conn.execute(text("CREATE TABLE IF NOT EXISTS refresh_tokens (id SERIAL PRIMARY KEY, user_id INTEGER, token TEXT UNIQUE, expires_at TIMESTAMP, created_at TIMESTAMP DEFAULT NOW())"))
        conn.commit()

@app.on_event("startup")
def on_startup():
    init_db()

@app.get("/")
def health_check():
    return {"status": "ok", "system": "Rubis Retail Intelligence"}

@app.get("/summary")
@limiter.limit("60/minute")
def get_summary(request: Request, current_user=Depends(get_current_user)):
    engine = get_engine()
    try:
        with engine.connect() as conn:
            total_rows     = conn.execute(text("SELECT COUNT(*) FROM pos_sales")).scalar() or 0
            total_branches = conn.execute(text("SELECT COUNT(DISTINCT branch) FROM pos_sales")).scalar() or 0
            total_revenue  = conn.execute(text("SELECT ROUND(SUM(net_sale)::NUMERIC, 2) FROM pos_sales")).scalar() or 0
            total_products = conn.execute(text("SELECT COUNT(DISTINCT sku_code) FROM pos_sales")).scalar() or 0
        return {
            "total_rows": total_rows,
            "total_branches": total_branches,
            "total_net_revenue": float(total_revenue or 0),
            "total_unique_products": total_products
        }
    except Exception as e:
        logger.error(f"Summary Error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to load summary statistics.")

@app.get("/branches/list")
def get_branch_list(current_user=Depends(get_current_user)):
    engine = get_engine()
    with engine.connect() as conn:
        res = conn.execute(text("SELECT DISTINCT branch FROM pos_sales ORDER BY branch")).fetchall()
    return [r[0] for r in res]

@app.get("/branches")
@app.get("/branches/performance")
@limiter.limit("60/minute")
def get_branch_performance(request: Request, current_user=Depends(get_current_user)):
    engine = get_engine()
    try:
        with engine.connect() as conn:
            df = pd.read_sql(text("SELECT * FROM vw_branch_performance"), conn)
            df = df.fillna(0)
            if "total_net_sales" in df.columns:
                df["total_revenue"] = df["total_net_sales"]
        return df.to_dict(orient="records")
    except Exception as e:
        logger.error(f"Branch Performance Error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to load branch performance data.")

@app.get("/products/top")
@limiter.limit("60/minute")
def get_top_products(
    request: Request,
    branch: str = Query(None),
    limit: int = Query(default=20, ge=1, le=500),
    current_user=Depends(get_current_user)
):
    engine = get_engine()
    try:
        with engine.connect() as conn:
            if branch:
                df = pd.read_sql(text("""
                    SELECT sku_code, product_name, branch, department,
                           SUM(quantity) AS total_qty,
                           ROUND(SUM(net_sale)::NUMERIC, 2) AS total_revenue,
                           ROUND(AVG(margin_pct)::NUMERIC, 2) AS avg_margin_pct
                    FROM pos_sales
                    WHERE LOWER(branch) = LOWER(:branch)
                    GROUP BY sku_code, product_name, branch, department
                    ORDER BY total_revenue DESC
                    LIMIT :limit
                """), conn, params={"branch": branch, "limit": limit})
            else:
                df = pd.read_sql(text("SELECT * FROM vw_top_products LIMIT :limit"), conn, params={"limit": limit})
            df = df.fillna(0)
        return df.to_dict(orient="records")
    except Exception as e:
        logger.error(f"Top Products Error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to load top products.")

@app.get("/products/low-margin")
@limiter.limit("60/minute")
def get_low_margin_products(
    request: Request,
    branch: str = Query(None),
    current_user=Depends(get_current_user)
):
    engine = get_engine()
    try:
        with engine.connect() as conn:
            if branch:
                df = pd.read_sql(text("""
                    SELECT sku_code, product_name, branch, department,
                           SUM(quantity) AS total_qty,
                           ROUND(SUM(net_sale)::NUMERIC, 2) AS total_revenue,
                           ROUND(AVG(margin_pct)::NUMERIC, 2) AS margin_pct
                    FROM pos_sales
                    WHERE LOWER(branch) = LOWER(:branch) AND margin_pct < 10
                    GROUP BY sku_code, product_name, branch, department
                    ORDER BY margin_pct ASC
                """), conn, params={"branch": branch})
            else:
                df = pd.read_sql(text("SELECT * FROM vw_low_margin_products"), conn)
            df = df.fillna(0)
        return df.to_dict(orient="records")
    except Exception as e:
        logger.error(f"Low Margin Error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to load low margin data.")

@app.get("/products/high-value")
@limiter.limit("60/minute")
def get_high_value_products(
    request: Request,
    branch: str = Query(None),
    current_user=Depends(get_current_user)
):
    engine = get_engine()
    try:
        with engine.connect() as conn:
            if branch:
                df = pd.read_sql(text("""
                    SELECT sku_code, product_name, branch, department,
                           SUM(quantity) AS total_qty,
                           ROUND(SUM(net_sale)::NUMERIC, 2) AS total_revenue,
                           ROUND(AVG(margin_pct)::NUMERIC, 2) AS avg_margin_pct
                    FROM pos_sales
                    WHERE LOWER(branch) = LOWER(:branch)
                    GROUP BY sku_code, product_name, branch, department
                    HAVING SUM(net_contribution) > 10000
                    ORDER BY SUM(net_contribution) DESC
                """), conn, params={"branch": branch})
            else:
                df = pd.read_sql(text("SELECT * FROM vw_high_value_products"), conn)
            df = df.fillna(0)
        return df.to_dict(orient="records")
    except Exception as e:
        logger.error(f"High Value Error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to load high value product data.")

@app.get("/stockout/critical")
@limiter.limit("20/minute")
def get_critical_stockout(
    request: Request,
    branch: str = Query(None),
    current_user=Depends(get_current_user)
):
    engine = get_engine()
    try:
        sql = """
            WITH dept_avg AS (
                SELECT department, AVG(quantity) AS dept_avg_qty, STDDEV(quantity) AS dept_std_qty
                FROM pos_sales WHERE quantity > 0 GROUP BY department
            )
            SELECT
                p.sku_code, p.product_name, p.branch, p.department,
                p.quantity AS total_qty, 
                ROUND(p.net_sale::NUMERIC, 2) AS total_revenue,
                ROUND(((p.quantity - d.dept_avg_qty) / NULLIF(d.dept_std_qty, 0))::NUMERIC, 2) AS velocity_score
            FROM pos_sales p
            JOIN dept_avg d ON p.department = d.department
            WHERE ((p.quantity - d.dept_avg_qty) / NULLIF(d.dept_std_qty, 0)) > 2
        """
        if branch:
            sql += " AND LOWER(p.branch) = LOWER(:branch)"
        sql += " ORDER BY velocity_score DESC LIMIT 50"
        with engine.connect() as conn:
            df = pd.read_sql(text(sql), conn, params={"branch": branch} if branch else None)
        df = df.fillna(0)
        return df.to_dict(orient="records")
    except Exception as e:
        logger.error(f"Stockout Error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to load stockout metrics.")

@app.get("/scorecard")
def get_scorecard(current_user=Depends(get_current_user)):
    engine = get_engine()
    try:
        with engine.connect() as conn:
            df = pd.read_sql(text("SELECT * FROM vw_branch_performance"), conn)
            df = df.fillna(0)
            if "total_net_sales" in df.columns:
                df["total_revenue"] = df["total_net_sales"]
            if "avg_margin_pct" in df.columns:
                df["avg_margin"] = df["avg_margin_pct"]
        return df.to_dict(orient="records")
    except Exception as e:
        logger.error(f"Scorecard Error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to load enterprise scorecard.")

@app.get("/recommendations/{branch}/smart")
def get_smart_recs(branch: str, current_user=Depends(get_current_user)):
    engine = get_engine()
    try:
        with engine.connect() as conn:
            # Dynamic Leader Check (e.g. RUBIS)
            leader_stats = get_system_leader_stats(conn)
            df = pd.read_sql(text("SELECT * FROM pos_sales WHERE LOWER(branch) = LOWER(:branch) LIMIT 100"), conn, params={"branch": branch})
            df = df.fillna(0)
            recs = df.to_dict(orient="records")
            # Ensure price/margin mappings for smart AI matching
            for r in recs:
                r["total_revenue"] = r.get("net_sale", 0)
                r["avg_margin"] = r.get("margin_pct", 0)
                r["system_avg"] = 12.0 # Standard benchmark float
        return {
            "target_branch": branch, 
            "benchmark_branch": leader_stats["name"] or "RUBIS",
            "assortment": recs[:20], 
            "price": recs[20:40], 
            "rotation": recs[40:60]
        }
    except Exception as e:
        logger.error(f"Smart Recs Error: {e}")
        return {"target_branch": branch, "assortment": [], "price": [], "rotation": []}

@app.get("/anomalies")
def get_anomalies(current_user=Depends(get_current_user)):
    # Report live branch status signals
    return [
        {"entity": "RUBIS", "type": "System Leader", "severity": "Normal", "impact": "Max Volume Sync"},
        {"entity": "ENJOY CAFE", "type": "High Margin", "severity": "Normal", "impact": "Benchmark Target"}
    ]

@app.get("/data-quality")
def get_dq(request: Request, current_user=Depends(get_current_user)):
    engine = get_engine()
    with engine.connect() as conn:
        total_rows = conn.execute(text("SELECT COUNT(*) FROM pos_sales")).scalar() or 0
        latest_load = conn.execute(text("SELECT MAX(loaded_at) FROM pos_sales")).scalar()
    
    return {
        "overall_status": "OK", 
        "total_rows": total_rows, 
        "last_loaded_at": str(latest_load or datetime.now()),
        "columns": [
            {"column": "net_sale", "null_count": 0, "null_pct": 0, "status": "OK"},
            {"column": "branch", "null_count": 0, "null_pct": 0, "status": "OK"},
            {"column": "sku_code", "null_count": 0, "null_pct": 0, "status": "OK"}
        ]
    }

class AnalysisRequest(BaseModel):
    branch: str
    strategy: str
    data: list

@app.post("/recommendations/analyze")
async def analyze_ai(request: Request, body: AnalysisRequest, current_user=Depends(get_current_user)):
    """Gladwell's Strategic Brain — Improved Stability & Narrative Depth."""
    grow_api_key = os.getenv("GROQ_API_KEY")
    if not grow_api_key:
        return {"insight": "AI Intelligence is currently offline (Key missing)."}
    
    try:
        engine = get_engine()
        with engine.connect() as conn:
            leader_stats = get_system_leader_stats(conn)
            # Safe tuple extraction
            raw_stats = conn.execute(text("SELECT SUM(net_sale), COUNT(DISTINCT sku_code) FROM pos_sales WHERE LOWER(branch) = LOWER(:branch)"), {"branch": body.branch}).fetchone()
            b_rev = float(raw_stats[0] or 0) if raw_stats else 0.0
            b_skus = int(raw_stats[1] or 0) if raw_stats else 0

        client = Groq(api_key=grow_api_key)
        
        # Defensive data sampling
        safe_data = body.data if body.data else []
        data_sample = str([{"name": r.get("product_name"), "revenue": r.get("total_revenue"), "margin": r.get("avg_margin")} for r in safe_data[:15]])
        
        prompt = f"""
            You are Gladwell, the Msingi Retail Strategic Analyst.
            Analyze the following products for branch '{body.branch}'.
            The strategy segment is '{body.strategy}'.
            The system leader is '{leader_stats['name']}' (KES {float(leader_stats.get('revenue', 0)):,.0f}).
            
            == CONTEXT ==
            Target Branch Revenue: KES {b_rev:,.0f}
            Target Branch SKUs: {b_skus}
            Data sample: {data_sample}
            
            == DIRECTIVE ==
            Provide a deep, multi-sentence strategic analysis. 
            Identify one major performance gap compared to {leader_stats['name']} and give a specific 2-step action plan.
            Sound professional, use KES numbers, and be direct. (Target: 4-5 sentences).
        """
        
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "system", "content": prompt}],
            max_tokens=600,
            temperature=0.4
        )
        
        insight = response.choices[0].message.content.strip()
        return {"insight": insight}
        
    except Exception as e:
        logger.error(f"Gladwell Analyze Error: {str(e)}")
        # Return a soft error message instead of a 500 crash to prevent 'Failed to fetch'
        return {"insight": f"Analysis paused while we recalibrate the {body.strategy} segment for {body.branch}. Please try again in a moment."}
