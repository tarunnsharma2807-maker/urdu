"""UrduDuo backend - Emergent Google auth + Urdu tutor AI proxy + cross-device progress."""
from fastapi import FastAPI, APIRouter, Request, Response, HTTPException, Cookie, Body
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import uuid
import logging
import httpx
from pathlib import Path
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone, timedelta

from emergentintegrations.llm.chat import LlmChat, UserMessage

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

EMERGENT_LLM_KEY = os.environ.get('EMERGENT_LLM_KEY', '')
EMERGENT_AUTH_URL = "https://demobackend.emergentagent.com/auth/v1/env/oauth/session-data"

app = FastAPI()
api_router = APIRouter(prefix="/api")


# ── AUTH ──────────────────────────────────────────────────────
async def get_current_user(request: Request) -> Optional[Dict[str, Any]]:
    token = request.cookies.get("session_token")
    if not token:
        auth = request.headers.get("Authorization", "")
        if auth.startswith("Bearer "):
            token = auth[7:]
    if not token:
        return None
    sess = await db.user_sessions.find_one({"session_token": token}, {"_id": 0})
    if not sess:
        return None
    exp = sess["expires_at"]
    if isinstance(exp, str):
        exp = datetime.fromisoformat(exp)
    if exp.tzinfo is None:
        exp = exp.replace(tzinfo=timezone.utc)
    if exp < datetime.now(timezone.utc):
        return None
    user = await db.users.find_one({"user_id": sess["user_id"]}, {"_id": 0})
    return user


@api_router.post("/auth/session")
async def auth_session(request: Request, response: Response):
    """Exchange X-Session-ID (from Emergent Google auth redirect) for our session cookie."""
    session_id = request.headers.get("X-Session-ID")
    if not session_id:
        raise HTTPException(status_code=400, detail="Missing X-Session-ID")
    async with httpx.AsyncClient(timeout=15) as c:
        r = await c.get(EMERGENT_AUTH_URL, headers={"X-Session-ID": session_id})
    if r.status_code != 200:
        raise HTTPException(status_code=401, detail="Invalid session_id")
    data = r.json()
    email = data["email"]
    existing = await db.users.find_one({"email": email}, {"_id": 0})
    if existing:
        user_id = existing["user_id"]
        await db.users.update_one(
            {"user_id": user_id},
            {"$set": {"name": data["name"], "picture": data.get("picture", "")}}
        )
    else:
        user_id = f"user_{uuid.uuid4().hex[:12]}"
        await db.users.insert_one({
            "user_id": user_id,
            "email": email,
            "name": data["name"],
            "picture": data.get("picture", ""),
            "portrait": "",
            "created_at": datetime.now(timezone.utc).isoformat(),
        })
    session_token = data["session_token"]
    expires_at = datetime.now(timezone.utc) + timedelta(days=7)
    await db.user_sessions.insert_one({
        "user_id": user_id,
        "session_token": session_token,
        "expires_at": expires_at.isoformat(),
        "created_at": datetime.now(timezone.utc).isoformat(),
    })
    response.set_cookie(
        "session_token", session_token,
        max_age=7 * 24 * 3600,
        httponly=True, secure=True, samesite="none", path="/"
    )
    user = await db.users.find_one({"user_id": user_id}, {"_id": 0})
    return {"user": user}


@api_router.get("/auth/me")
async def auth_me(request: Request):
    user = await get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user


@api_router.post("/auth/logout")
async def auth_logout(request: Request, response: Response):
    token = request.cookies.get("session_token")
    if token:
        await db.user_sessions.delete_one({"session_token": token})
    response.delete_cookie("session_token", path="/")
    return {"ok": True}


# ── PROGRESS (cross-device) ───────────────────────────────────
class ProgressPayload(BaseModel):
    xp: int = 0
    streak: int = 1
    done: List[str] = []
    portrait: Optional[str] = None  # data URL for chosen portrait


class VocabMasteryItem(BaseModel):
    word: str  # urdu script as id
    status: str  # 'known' | 'unsure' | 'new'


@api_router.get("/progress")
async def get_progress(request: Request):
    user = await get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    p = await db.user_progress.find_one({"user_id": user["user_id"]}, {"_id": 0})
    if not p:
        p = {"xp": 0, "streak": 1, "done": []}
    return {
        "xp": p.get("xp", 0),
        "streak": p.get("streak", 1),
        "done": p.get("done", []),
        "portrait": user.get("portrait", ""),
        "name": user.get("name", ""),
        "email": user.get("email", ""),
        "picture": user.get("picture", ""),
    }


@api_router.post("/progress")
async def save_progress(request: Request, body: ProgressPayload):
    user = await get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    await db.user_progress.update_one(
        {"user_id": user["user_id"]},
        {"$set": {"xp": body.xp, "streak": body.streak, "done": body.done,
                  "updated_at": datetime.now(timezone.utc).isoformat()}},
        upsert=True,
    )
    if body.portrait is not None:
        await db.users.update_one(
            {"user_id": user["user_id"]},
            {"$set": {"portrait": body.portrait}}
        )
    return {"ok": True}


@api_router.get("/vocab/mastery")
async def get_vocab_mastery(request: Request):
    user = await get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    doc = await db.vocab_mastery.find_one({"user_id": user["user_id"]}, {"_id": 0})
    return {"mastery": (doc or {}).get("mastery", {})}


@api_router.post("/vocab/mastery")
async def set_vocab_mastery(request: Request, body: VocabMasteryItem):
    user = await get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    if body.status not in ("known", "unsure", "new"):
        raise HTTPException(status_code=400, detail="status must be known|unsure|new")
    if body.status == "new":
        await db.vocab_mastery.update_one(
            {"user_id": user["user_id"]},
            {"$unset": {f"mastery.{body.word}": ""},
             "$set": {"updated_at": datetime.now(timezone.utc).isoformat()}},
            upsert=True,
        )
    else:
        await db.vocab_mastery.update_one(
            {"user_id": user["user_id"]},
            {"$set": {f"mastery.{body.word}": body.status,
                      "updated_at": datetime.now(timezone.utc).isoformat()}},
            upsert=True,
        )
    return {"ok": True}


# ── AI TUTOR ──────────────────────────────────────────────────
class ChatBody(BaseModel):
    message: str
    history: List[Dict[str, str]] = []
    system: Optional[str] = None
    session_id: Optional[str] = None
    max_tokens: int = 600


URDU_TUTOR_SYSTEM = """You are a warm Urdu language tutor for an English speaker who is learning the Urdu script from scratch.
Rules:
- Always show Urdu script for Urdu words: اردو word (romanisation) - English meaning
- Explain in clear, conversational English. Do not assume the learner knows Hindi or Devanagari.
- Keep responses SHORT, conversational, 2-4 sentences. No bullet points, no headers.
- If asked to quiz, give one Urdu word in script and ask what it means.
- شاباش (Shabash = well done!) works great for encouragement.
- Be warm and specific, like a friend explaining a beautiful language."""


@api_router.post("/ai/chat")
async def ai_chat(body: ChatBody):
    if not EMERGENT_LLM_KEY:
        raise HTTPException(status_code=500, detail="LLM key not configured")
    sys_msg = body.system or URDU_TUTOR_SYSTEM
    sid = body.session_id or f"chat_{uuid.uuid4().hex[:10]}"
    chat = LlmChat(
        api_key=EMERGENT_LLM_KEY,
        session_id=sid,
        system_message=sys_msg,
    ).with_model("anthropic", "claude-haiku-4-5-20251001")
    # combine history into one prompt for stateless behavior
    history_text = ""
    for h in body.history[-10:]:
        role = h.get("role", "user")
        content = h.get("content", "")
        if role == "user":
            history_text += f"\n[User]: {content}"
        else:
            history_text += f"\n[Tutor]: {content}"
    final_text = (history_text + f"\n[User]: {body.message}").strip() if history_text else body.message
    try:
        reply = await chat.send_message(UserMessage(text=final_text))
        return {"reply": reply, "session_id": sid}
    except Exception as e:
        logging.exception("AI chat failed")
        raise HTTPException(status_code=500, detail=f"AI error: {e}")


@app.get("/api/health")
async def health():
    return {"ok": True}


app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
