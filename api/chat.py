# api/chat.py
# Msingi Retail Intelligence — Nuru AI Analyst (Groq)
# The Groq API key lives here (server side) and is NEVER sent to the frontend.

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
router = APIRouter()
logger = logging.getLogger("msingi.gladwell")
limiter = Limiter(key_func=get_remote_address)

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    logger.warning("GROQ_API_KEY not set — Gladwell will be unavailable")

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
        engine = create_engine(os.getenv("DB_URL"), pool_pre_ping=True)
        with engine.connect() as conn:
            summary = conn.execute(text("""
                SELECT
                    COUNT(DISTINCT branch)             AS total_branches,
                    COUNT(DISTINCT sku_code)           AS total_products,
                    ROUND(SUM(net_sale)::NUMERIC, 2)   AS total_revenue,
                    ROUND(AVG(margin_pct)::NUMERIC, 2) AS avg_margin,
                    MAX(sales_date)                    AS latest_date
                FROM pos_sales
            """)).fetchone()

            branches = conn.execute(text("""
                SELECT
                    branch,
                    ROUND(SUM(net_sale)::NUMERIC, 2)   AS revenue,
                    ROUND(AVG(margin_pct)::NUMERIC, 2) AS avg_margin,
                    COUNT(DISTINCT sku_code)            AS products
                FROM pos_sales
                GROUP BY branch
                ORDER BY revenue DESC
            """)).fetchall()

            low_margin = conn.execute(text("""
                SELECT product_name, branch,
                       ROUND(AVG(margin_pct)::NUMERIC, 2) AS avg_margin
                FROM pos_sales
                WHERE margin_pct < 5 AND margin_pct IS NOT NULL
                GROUP BY product_name, branch
                ORDER BY avg_margin ASC
                LIMIT 5
            """)).fetchall()

            top_products = conn.execute(text("""
                SELECT product_name,
                       ROUND(SUM(net_sale)::NUMERIC, 2) AS revenue
                FROM pos_sales
                GROUP BY product_name
                ORDER BY revenue DESC
                LIMIT 5
            """)).fetchall()

            stockout = conn.execute(text("""
                SELECT product_name, branch,
                       SUM(quantity) AS total_qty
                FROM pos_sales
                GROUP BY product_name, branch
                HAVING SUM(quantity) < 10
                ORDER BY total_qty ASC
                LIMIT 5
            """)).fetchall()

            departments = conn.execute(text("""
                SELECT department,
                       ROUND(SUM(net_sale)::NUMERIC, 2)   AS revenue,
                       ROUND(AVG(margin_pct)::NUMERIC, 2) AS avg_margin
                FROM pos_sales
                WHERE department IS NOT NULL
                GROUP BY department
                ORDER BY revenue DESC
                LIMIT 5
            """)).fetchall()

        # Clean up data for formatting (replace None with 0)
        class CleanRow:
            def __init__(self, row):
                if row:
                    self.__dict__.update({
                        k: (v if v is not None else 0) 
                        for k, v in row._asdict().items()
                    })
                else:
                    self.total_branches = 0
                    self.total_products = 0
                    self.total_revenue = 0
                    self.avg_margin = 0
                    self.latest_date = "N/A"
        
        c_summary = CleanRow(summary)

        branch_lines = "\n".join([
            f"  - {r.branch or 'N/A'}: KES {float(r.revenue or 0):,.0f} revenue | "
            f"{float(r.avg_margin or 0):.1f}% avg margin | {int(getattr(r, 'products', 0))} products"
            for r in branches
        ])

        low_margin_lines = "\n".join([
            f"  - {r.product_name or 'Unknown'} @ {r.branch or 'N/A'}: {float(r.avg_margin or 0):.1f}% margin"
            for r in low_margin
        ]) or "  None detected"

        top_product_lines = "\n".join([
            f"  - {r.product_name or 'Unknown'}: KES {float(r.revenue or 0):,.0f}"
            for r in top_products
        ])

        stockout_lines = "\n".join([
            f"  - {r.product_name} @ {r.branch}: {int(r.total_qty or 0)} units remaining"
            for r in stockout
        ]) or "  None detected"

        dept_lines = "\n".join([
            f"  - {r.department}: KES {float(r.revenue or 0):,.0f} | {float(r.avg_margin or 0):.1f}% margin"
            for r in departments
        ])

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
Latest data date : {summary.latest_date or "N/A"}
Total branches   : {c_summary.total_branches}
Total products   : {c_summary.total_products}
Total revenue    : KES {float(c_summary.total_revenue):,.0f}
Average margin   : {float(c_summary.avg_margin):.1f}%

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
# GLADWELL ANALYST ENDPOINT (UPDATED WITH FULL ERROR LOGGING)
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
        # Log the full error with traceback for debugging
        import traceback
        error_trace = traceback.format_exc()
        logger.error(f"Gladwell Groq error:\n{error_trace}")
        return {"reply": f"Groq API error: {type(e).__name__} - {str(e)}"}

