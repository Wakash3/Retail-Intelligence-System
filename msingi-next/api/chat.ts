# Msingi Retail Intelligence — Nuru AI Analyst (Groq)

from fastapi import APIRouter, HTTPException, Request, Depends
from pydantic import BaseModel, validator
from typing import List
from slowapi import Limiter
from slowapi.util import get_remote_address
from groq import Groq
from sqlalchemy import create_engine, text
from api.auth import get_current_user
import os
import logging
import traceback  # FIX 7: moved to top-level import

router = APIRouter()
logger = logging.getLogger("msingi.gladwell")
limiter = Limiter(key_func=get_remote_address)

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    logger.warning("GROQ_API_KEY not set — Gladwell will be unavailable")


# ─────────────────────────────────────────
# HELPER: Safe SQLAlchemy row → dict
# ─────────────────────────────────────────

def row_to_dict(row) -> dict:
    """Convert a SQLAlchemy Row to a plain dict — supports both 1.x and 2.x."""
    try:
        return dict(row._mapping)       # SQLAlchemy 2.x
    except AttributeError:
        return dict(row._asdict())      # SQLAlchemy 1.x


# ─────────────────────────────────────────
# MODELS
# ─────────────────────────────────────────

class ChatMessage(BaseModel):
    role: str
    content: str

    @validator("role")
    def valid_role(cls, v):
        if v not in ("user", "assistant"):
            raise ValueError("Invalid role")
        return v

    @validator("content")
    def content_not_empty(cls, v):
        v = v.strip()
        if not v:
            raise ValueError("Message content cannot be empty")
        if len(v) > 2000:
            raise ValueError("Message too long (max 2000 chars)")
        return v


class ChatRequest(BaseModel):
    messages: List[ChatMessage]
    system: str = ""

    @validator("messages")
    def limit_history(cls, v):
        return v[-10:]

    @validator("system")
    def sanitize_system(cls, v):
        if len(v) > 3000:
            return v[:3000]
        return v


# ─────────────────────────────────────────
# LIVE KPI CONTEXT LOADER
# ─────────────────────────────────────────

def get_live_kpi_context() -> str:
    """Pull live KPIs from PostgreSQL and format as context for Gladwell."""
    try:
        db_url = os.getenv("DB_URL")
        if not db_url:
            # FIX 6: Catch missing DB_URL early with a clear error
            raise ValueError("DB_URL environment variable is not set")

        engine = create_engine(db_url, pool_pre_ping=True)

        with engine.connect() as conn:
            summary_row = conn.execute(text("""
                SELECT
                    COUNT(DISTINCT branch)             AS total_branches,
                    COUNT(DISTINCT sku_code)           AS total_products,
                    ROUND(SUM(net_sale)::NUMERIC, 2)   AS total_revenue,
                    ROUND(AVG(margin_pct)::NUMERIC, 2) AS avg_margin,
                    MAX(sales_date)                    AS latest_date
                FROM pos_sales
            """)).fetchone()

            branch_rows = conn.execute(text("""
                SELECT
                    branch,
                    ROUND(SUM(net_sale)::NUMERIC, 2)   AS revenue,
                    ROUND(AVG(margin_pct)::NUMERIC, 2) AS avg_margin,
                    COUNT(DISTINCT sku_code)            AS products
                FROM pos_sales
                GROUP BY branch
                ORDER BY revenue DESC
            """)).fetchall()

            low_margin_rows = conn.execute(text("""
                SELECT product_name, branch,
                       ROUND(AVG(margin_pct)::NUMERIC, 2) AS avg_margin
                FROM pos_sales
                WHERE margin_pct < 5 AND margin_pct IS NOT NULL
                GROUP BY product_name, branch
                ORDER BY avg_margin ASC
                LIMIT 5
            """)).fetchall()

            top_product_rows = conn.execute(text("""
                SELECT product_name,
                       ROUND(SUM(net_sale)::NUMERIC, 2) AS revenue
                FROM pos_sales
                GROUP BY product_name
                ORDER BY revenue DESC
                LIMIT 5
            """)).fetchall()

            stockout_rows = conn.execute(text("""
                SELECT product_name, branch,
                       SUM(quantity) AS total_qty
                FROM pos_sales
                GROUP BY product_name, branch
                HAVING SUM(quantity) < 10
                ORDER BY total_qty ASC
                LIMIT 5
            """)).fetchall()

            dept_rows = conn.execute(text("""
                SELECT department,
                       ROUND(SUM(net_sale)::NUMERIC, 2)   AS revenue,
                       ROUND(AVG(margin_pct)::NUMERIC, 2) AS avg_margin
                FROM pos_sales
                WHERE department IS NOT NULL
                GROUP BY department
                ORDER BY revenue DESC
                LIMIT 5
            """)).fetchall()

        # ── FIX 1 & 2: Convert ALL rows to plain dicts immediately ──
        # Replaces row._asdict() (1.x only) and raw attribute access.
        # Every row is a safe plain dict from this point on.
        summary      = row_to_dict(summary_row) if summary_row else {}
        branches     = [row_to_dict(r) for r in branch_rows]
        low_margin   = [row_to_dict(r) for r in low_margin_rows]
        top_products = [row_to_dict(r) for r in top_product_rows]
        stockouts    = [row_to_dict(r) for r in stockout_rows]
        departments  = [row_to_dict(r) for r in dept_rows]

        # ── Summary scalars (FIX 2: use converted dict, not raw row) ──
        total_branches = summary.get("total_branches") or 0
        total_products = summary.get("total_products") or 0
        total_revenue  = float(summary.get("total_revenue") or 0)
        avg_margin     = float(summary.get("avg_margin") or 0)
        latest_date    = summary.get("latest_date") or "N/A"

        # ── FIX 3, 4, 5: All list rows accessed safely via dict.get() ──

        branch_lines = "\n".join([
            f"  - {r.get('branch') or 'N/A'}: "
            f"KES {float(r.get('revenue') or 0):,.0f} revenue | "
            f"{float(r.get('avg_margin') or 0):.1f}% avg margin | "
            f"{int(r.get('products') or 0)} products"
            for r in branches
        ]) or "  No branch data"

        low_margin_lines = "\n".join([
            f"  - {r.get('product_name') or 'Unknown'} @ {r.get('branch') or 'N/A'}: "
            f"{float(r.get('avg_margin') or 0):.1f}% margin"
            for r in low_margin
        ]) or "  None detected"

        top_product_lines = "\n".join([
            f"  - {r.get('product_name') or 'Unknown'}: "
            f"KES {float(r.get('revenue') or 0):,.0f}"
            for r in top_products
        ]) or "  No product data"

        stockout_lines = "\n".join([
            # FIX 4: product_name and branch guarded against None
            f"  - {r.get('product_name') or 'Unknown'} @ {r.get('branch') or 'N/A'}: "
            f"{int(r.get('total_qty') or 0)} units remaining"
            for r in stockouts
        ]) or "  None detected"

        dept_lines = "\n".join([
            f"  - {r.get('department') or 'Unknown'}: "
            f"KES {float(r.get('revenue') or 0):,.0f} | "
            f"{float(r.get('avg_margin') or 0):.1f}% margin"
            for r in departments
        ]) or "  No department data"

        context = f"""
You are Gladwell — an expert retail data analyst for Msingi Retail System, a multi-branch retail
chain in Kenya. Your name is Gladwell. If anyone asks your name, tell them you are
Gladwell, the Msingi Retail Intelligence AI Analyst.

You have access to live operational data and answer questions about branch
performance, product margins, stockout risks, revenue trends, and department
performance. Be concise, specific, and always reference actual numbers from
the data below. Use KES for all currency values. Format large numbers with
commas. If asked something outside retail operations, politely redirect to
business topics.

=== LIVE DATA SNAPSHOT ===
Latest data date : {latest_date}
Total branches   : {total_branches}
Total products   : {total_products}
Total revenue    : KES {total_revenue:,.0f}
Average margin   : {avg_margin:.1f}%

=== BRANCH PERFORMANCE (ranked by revenue) ===
{branch_lines}

=== TOP 5 PRODUCTS BY REVENUE ===
{top_product_lines}

=== TOP 5 DEPARTMENTS BY REVENUE ===
{dept_lines}

=== LOW MARGIN ALERTS (below 5%) ===
{low_margin_lines}

=== STOCKOUT RISK (critically low stock) ===
{stockout_lines}
"""
        return context.strip()

    except Exception as e:
        logger.error(f"Failed to load KPI context for Gladwell: {e}", exc_info=True)
        return (
            "You are Gladwell, the Msingi Retail System AI Analyst for Msingi Kenya. "
            "Your name is Gladwell. Live data is temporarily unavailable — answer "
            "based on general retail best practices and let the user know that "
            "live data could not be loaded right now."
        )


# ─────────────────────────────────────────
# STANDARD CHAT ENDPOINT
# ─────────────────────────────────────────

@router.post("/chat")
@limiter.limit("20/minute")
async def chat(
    request: Request,
    body: ChatRequest,
    current_user=Depends(get_current_user)
):
    if not GROQ_API_KEY:
        raise HTTPException(status_code=503, detail="Gladwell is currently unavailable")

    try:
        client = Groq(api_key=GROQ_API_KEY)

        messages = []
        if body.system:
            messages.append({"role": "system", "content": body.system})
        messages += [{"role": m.role, "content": m.content} for m in body.messages]

        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=messages,
            max_tokens=512,
            temperature=0.7,
        )

        reply = response.choices[0].message.content or ""
        return {"reply": reply}

    except Exception as e:
        error_msg = str(e).lower()
        if "rate limit" in error_msg:
            logger.warning(f"Groq rate limit hit: {e}")
            raise HTTPException(status_code=429, detail="Too many requests. Please wait a moment.")
        if "authentication" in error_msg or "api key" in error_msg:
            logger.error(f"Groq auth error: {e}")
            return {"reply": "I'm sorry, Gladwell is having trouble connecting right now. Please check the Groq API key in the server configuration."}
        logger.error(f"Groq API error: {e}")
        return {"reply": "Gladwell is temporarily unavailable. Please try again later."}


# ─────────────────────────────────────────
# GLADWELL ANALYST ENDPOINT
# ─────────────────────────────────────────

@router.post("/chat/analyst")
@limiter.limit("15/minute")
async def chat_analyst(
    request: Request,
    body: ChatRequest,
    current_user=Depends(get_current_user)
):
    """
    Gladwell analyst chat — Groq receives live KPI data as system context.
    Management can ask natural language questions about the business.
    """
    if not GROQ_API_KEY:
        return {"reply": "GROQ_API_KEY not set in .env file. Please contact administrator."}

    try:
        client = Groq(api_key=GROQ_API_KEY)

        # Always inject live KPI context as Gladwell's system prompt
        live_context = get_live_kpi_context()

        messages = [{"role": "system", "content": live_context}]
        messages += [{"role": m.role, "content": m.content} for m in body.messages]

        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=messages,
            max_tokens=800,
            temperature=0.4,
        )

        reply = response.choices[0].message.content or ""
        logger.info(
            f"Gladwell analyst query by {current_user.email} — "
            f"{len(body.messages)} messages in history"
        )
        return {"reply": reply}

    except Exception as e:
        error_trace = traceback.format_exc()
        logger.error(f"Gladwell Groq error:\n{error_trace}")
        return {"reply": f"Groq API error: {type(e).__name__} - {str(e)}"}