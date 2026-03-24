# api/chat.py
# Rubis Intelligence — Chatbot proxy endpoint (Groq)
# The Groq API key lives here (server side) and is NEVER sent to the frontend.

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, validator
from typing import List
from slowapi import Limiter
from slowapi.util import get_remote_address
from groq import Groq
import os
import logging

router = APIRouter()
logger = logging.getLogger("rubis.chat")
limiter = Limiter(key_func=get_remote_address)

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    logger.warning("GROQ_API_KEY not set — chatbot will be unavailable")

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
        # Keep only the last 10 messages to control token usage
        return v[-10:]

    @validator("system")
    def sanitize_system(cls, v):
        # The system prompt comes from the HTML — cap it to prevent abuse
        if len(v) > 3000:
            return v[:3000]
        return v

# ─────────────────────────────────────────
# CHAT ENDPOINT
# Rate limited to prevent API abuse
# ─────────────────────────────────────────
@router.post("/chat")
@limiter.limit("20/minute")
async def chat(request: Request, body: ChatRequest):
    if not GROQ_API_KEY:
        raise HTTPException(status_code=503, detail="Chatbot service unavailable")

    try:
        client = Groq(api_key=GROQ_API_KEY)

        # Build messages — Groq uses the same OpenAI-compatible format
        messages = []

        # System prompt goes first
        if body.system:
            messages.append({"role": "system", "content": body.system})

        # Add conversation history
        messages += [{"role": m.role, "content": m.content} for m in body.messages]

        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",   # Fast, free, great for chatbot use
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
            raise HTTPException(status_code=502, detail="AI service configuration error.")
        logger.error(f"Groq API error: {e}")
        raise HTTPException(status_code=502, detail="AI service error. Please try again.")

