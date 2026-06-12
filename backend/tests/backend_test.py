"""UrduDuo backend integration tests via public URL."""
import os
import time
import uuid
import datetime as dt
import requests
import pytest
from pymongo import MongoClient

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://universal-login-1.preview.emergentagent.com").rstrip("/")
MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = os.environ.get("DB_NAME", "test_database")


# ── fixtures ──────────────────────────────────────────────
@pytest.fixture(scope="session")
def api():
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    return s


@pytest.fixture(scope="session")
def mongo():
    c = MongoClient(MONGO_URL)
    yield c[DB_NAME]
    c.close()


@pytest.fixture(scope="session")
def seeded_session(mongo):
    """Manually seed a user + session token; returns (user_id, token)."""
    user_id = f"TEST_user_{uuid.uuid4().hex[:8]}"
    token = f"TEST_session_{uuid.uuid4().hex}"
    now = dt.datetime.now(dt.timezone.utc)
    mongo.users.insert_one({
        "user_id": user_id,
        "email": f"TEST_{user_id}@example.com",
        "name": "Test User",
        "picture": "",
        "portrait": "",
        "created_at": now.isoformat(),
    })
    mongo.user_sessions.insert_one({
        "user_id": user_id,
        "session_token": token,
        "expires_at": (now + dt.timedelta(days=7)).isoformat(),
        "created_at": now.isoformat(),
    })
    yield user_id, token
    # teardown
    mongo.users.delete_one({"user_id": user_id})
    mongo.user_sessions.delete_one({"session_token": token})
    mongo.user_progress.delete_one({"user_id": user_id})
    mongo.vocab_mastery.delete_one({"user_id": user_id})


# ── health ────────────────────────────────────────────────
def test_health(api):
    r = api.get(f"{BASE_URL}/api/health", timeout=10)
    assert r.status_code == 200
    assert r.json() == {"ok": True}


# ── AI chat (Claude Haiku 4.5 via Emergent LLM key) ───────
def test_ai_chat_basic(api):
    r = api.post(f"{BASE_URL}/api/ai/chat",
                 json={"message": "Say hi in 1 short Urdu phrase"},
                 timeout=60)
    assert r.status_code == 200, r.text
    data = r.json()
    assert "reply" in data and isinstance(data["reply"], str) and len(data["reply"].strip()) > 0
    assert "session_id" in data and isinstance(data["session_id"], str)


def test_ai_chat_with_history(api):
    r = api.post(f"{BASE_URL}/api/ai/chat", json={
        "message": "What did I just ask?",
        "history": [
            {"role": "user", "content": "Teach me 'water' in Urdu"},
            {"role": "assistant", "content": "پانی (paani) - water"},
        ],
    }, timeout=60)
    assert r.status_code == 200, r.text
    data = r.json()
    assert len(data["reply"].strip()) > 0


# ── auth gating ───────────────────────────────────────────
def test_auth_me_unauth(api):
    r = api.get(f"{BASE_URL}/api/auth/me", timeout=10)
    assert r.status_code == 401


def test_progress_unauth(api):
    r = api.get(f"{BASE_URL}/api/progress", timeout=10)
    assert r.status_code == 401


def test_auth_session_missing_header(api):
    r = api.post(f"{BASE_URL}/api/auth/session", timeout=10)
    assert r.status_code == 400


def test_auth_session_invalid_header(api):
    r = api.post(f"{BASE_URL}/api/auth/session",
                 headers={"X-Session-ID": "definitely-not-real"},
                 timeout=20)
    assert r.status_code == 401


# ── authenticated flow with seeded session ────────────────
def test_auth_me_with_seeded_token(api, seeded_session):
    _, token = seeded_session
    r = api.get(f"{BASE_URL}/api/auth/me",
                headers={"Authorization": f"Bearer {token}"}, timeout=10)
    assert r.status_code == 200, r.text
    user = r.json()
    assert user["name"] == "Test User"
    assert "user_id" in user
    assert "_id" not in user  # ObjectId must not leak


def test_progress_upsert_and_persist(api, seeded_session, mongo):
    user_id, token = seeded_session
    headers = {"Authorization": f"Bearer {token}"}

    # initial GET — empty defaults
    r = api.get(f"{BASE_URL}/api/progress", headers=headers, timeout=10)
    assert r.status_code == 200
    initial = r.json()
    assert initial["xp"] == 0
    assert initial["streak"] == 1
    assert initial["done"] == []

    # POST progress
    payload = {"xp": 120, "streak": 5, "done": ["alphabet-1", "writing-2"]}
    r = api.post(f"{BASE_URL}/api/progress", headers=headers, json=payload, timeout=10)
    assert r.status_code == 200
    assert r.json().get("ok") is True

    # Verify via GET
    r = api.get(f"{BASE_URL}/api/progress", headers=headers, timeout=10)
    assert r.status_code == 200
    got = r.json()
    assert got["xp"] == 120
    assert got["streak"] == 5
    assert got["done"] == ["alphabet-1", "writing-2"]

    # Verify in DB
    doc = mongo.user_progress.find_one({"user_id": user_id})
    assert doc is not None
    assert doc["xp"] == 120


def test_progress_portrait_save(api, seeded_session, mongo):
    user_id, token = seeded_session
    headers = {"Authorization": f"Bearer {token}"}
    data_url = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII="
    r = api.post(f"{BASE_URL}/api/progress", headers=headers,
                 json={"xp": 120, "streak": 5, "done": [], "portrait": data_url}, timeout=10)
    assert r.status_code == 200

    r = api.get(f"{BASE_URL}/api/progress", headers=headers, timeout=10)
    assert r.status_code == 200
    assert r.json()["portrait"] == data_url

    user = mongo.users.find_one({"user_id": user_id})
    assert user["portrait"] == data_url


# ── vocab mastery (cross-device per-card known/unsure/new) ─
def test_vocab_mastery_unauth(api):
    r = api.get(f"{BASE_URL}/api/vocab/mastery", timeout=10)
    assert r.status_code == 401
    r = api.post(f"{BASE_URL}/api/vocab/mastery",
                 json={"word": "السلام علیکم", "status": "known"}, timeout=10)
    assert r.status_code == 401


def test_vocab_mastery_invalid_status(api, seeded_session):
    _, token = seeded_session
    headers = {"Authorization": f"Bearer {token}"}
    r = api.post(f"{BASE_URL}/api/vocab/mastery", headers=headers,
                 json={"word": "السلام علیکم", "status": "foo"}, timeout=10)
    assert r.status_code == 400


def test_vocab_mastery_set_get_remove(api, seeded_session, mongo):
    user_id, token = seeded_session
    headers = {"Authorization": f"Bearer {token}"}

    # Initial mastery — empty
    r = api.get(f"{BASE_URL}/api/vocab/mastery", headers=headers, timeout=10)
    assert r.status_code == 200
    assert r.json() == {"mastery": {}}

    # Mark a word "known"
    word_a = "السلام علیکم"
    r = api.post(f"{BASE_URL}/api/vocab/mastery", headers=headers,
                 json={"word": word_a, "status": "known"}, timeout=10)
    assert r.status_code == 200
    assert r.json().get("ok") is True

    # Mark another word "unsure"
    word_b = "پانی"
    r = api.post(f"{BASE_URL}/api/vocab/mastery", headers=headers,
                 json={"word": word_b, "status": "unsure"}, timeout=10)
    assert r.status_code == 200

    # GET — both entries present
    r = api.get(f"{BASE_URL}/api/vocab/mastery", headers=headers, timeout=10)
    assert r.status_code == 200
    mastery = r.json()["mastery"]
    assert mastery.get(word_a) == "known"
    assert mastery.get(word_b) == "unsure"

    # DB cross-check
    doc = mongo.vocab_mastery.find_one({"user_id": user_id})
    assert doc is not None
    assert doc["mastery"][word_a] == "known"
    assert doc["mastery"][word_b] == "unsure"

    # Transition known -> unsure
    r = api.post(f"{BASE_URL}/api/vocab/mastery", headers=headers,
                 json={"word": word_a, "status": "unsure"}, timeout=10)
    assert r.status_code == 200
    r = api.get(f"{BASE_URL}/api/vocab/mastery", headers=headers, timeout=10)
    assert r.json()["mastery"][word_a] == "unsure"

    # status:'new' should REMOVE the entry
    r = api.post(f"{BASE_URL}/api/vocab/mastery", headers=headers,
                 json={"word": word_a, "status": "new"}, timeout=10)
    assert r.status_code == 200
    r = api.get(f"{BASE_URL}/api/vocab/mastery", headers=headers, timeout=10)
    final = r.json()["mastery"]
    assert word_a not in final
    assert final.get(word_b) == "unsure"

