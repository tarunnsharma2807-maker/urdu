# UrduDuo — PRD

## Problem statement
A personalised Duolingo-style Urdu learning app, originally a single static HTML, gifted to "Srushti" with a custom birthday overlay. The user requested:
1. Make it fully responsive (mobile + tablet + desktop).
2. Fix AI (was pointing to a broken cloudflare worker).
3. Birthday page: remove "Saalgirah Mubarak Ho" + "Teri muskurahat..." line, replace with an original Urdu poem about how important she is (marigold theory).
4. Portrait should be her choice (upload her own); Duolingo owl mascot must be constant.
5. Universal login so the same account works across devices.

## Architecture
- **Frontend**: single static HTML page served from `/app/frontend/public/index.html` via CRA dev server. React `App.js` renders nothing (just hides `#root`). Backend URL injected via `%REACT_APP_BACKEND_URL%`.
- **Backend**: FastAPI at `/api/*`, MongoDB for users, sessions, progress.
- **Auth**: Emergent-managed Google OAuth → cookie session (`session_token`, 7d).
- **AI**: Anthropic `claude-haiku-4-5-20251001` via Emergent Universal LLM key, exposed at `POST /api/ai/chat` (cheap & fast).

## Implemented (2026-02-11)
- Backend rewritten (`server.py`):
  - `POST /api/auth/session`, `GET /api/auth/me`, `POST /api/auth/logout`.
  - `GET /api/progress`, `POST /api/progress` (cross-device XP/streak/done + portrait dataURL).
  - `POST /api/ai/chat` — Urdu tutor system prompt baked in, history support, cheap Haiku model.
- Frontend (`public/index.html`):
  - Login screen replaced with "Continue with Google" + guest fallback.
  - Birthday overlay: removed Saalgirah/Teri muskurahat. New 6-line Urdu poem (marigold/lamp metaphor) with Nastaliq + Roman + English. SVG Duolingo owl mascot pinned bottom-left. Portrait upload compresses to ≤480px JPEG and is synced to backend.
  - All AI calls routed to `/api/ai/chat`.
  - Responsive: hamburger menu on ≤760px, fluid font sizes via `clamp`, single-column MCQ, smaller letter grid, scrollable bday on mobile.
  - Boot flow: handles `#session_id=...` from OAuth, hits `/auth/me`, pulls cloud progress.

## Backlog (next iterations)
- P1: rotate `session_token` in cookie after refresh (currently we store Emergent's token directly — fine for now, but rotation is cleaner).
- P1: persist learnt-letter mastery on backend per user.
- P2: streak math based on calendar days, not just login.
- P2: leaderboard / share progress card image.
- P2: dark mode toggle.

## Test credentials
See `/app/memory/test_credentials.md`.
