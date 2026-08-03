# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

Behavioral guidelines to reduce common LLM coding mistakes. Merge with project-specific instructions as needed.

**Tradeoff:** These guidelines bias toward caution over speed. For trivial tasks, use judgment.

## 1. Think Before Coding

**Don't assume. Don't hide confusion. Surface tradeoffs.**

Before implementing:
- State your assumptions explicitly. If uncertain, ask.
- If multiple interpretations exist, present them - don't pick silently.
- If a simpler approach exists, say so. Push back when warranted.
- If something is unclear, stop. Name what's confusing. Ask.

## 2. Simplicity First

**Minimum code that solves the problem. Nothing speculative.**

- No features beyond what was asked.
- No abstractions for single-use code.
- No "flexibility" or "configurability" that wasn't requested.
- No error handling for impossible scenarios.
- If you write 200 lines and it could be 50, rewrite it.

Ask yourself: "Would a senior engineer say this is overcomplicated?" If yes, simplify.

## 3. Surgical Changes

**Touch only what you must. Clean up only your own mess.**

When editing existing code:
- Don't "improve" adjacent code, comments, or formatting.
- Don't refactor things that aren't broken.
- Match existing style, even if you'd do it differently.
- If you notice unrelated dead code, mention it - don't delete it.

When your changes create orphans:
- Remove imports/variables/functions that YOUR changes made unused.
- Don't remove pre-existing dead code unless asked.

The test: Every changed line should trace directly to the user's request.

## 4. Goal-Driven Execution

**Define success criteria. Loop until verified.**

Transform tasks into verifiable goals:
- "Add validation" → "Write tests for invalid inputs, then make them pass"
- "Fix the bug" → "Write a test that reproduces it, then make it pass"
- "Refactor X" → "Ensure tests pass before and after"

For multi-step tasks, state a brief plan:
```
1. [Step] → verify: [check]
2. [Step] → verify: [check]
3. [Step] → verify: [check]
```

Strong success criteria let you loop independently. Weak criteria ("make it work") require constant clarification.

---

**These guidelines are working if:** fewer unnecessary changes in diffs, fewer rewrites due to overcomplication, and clarifying questions come before implementation rather than after mistakes.

---

## Project Overview

"메이플 썬데이" — a MapleStory fan site tracking Sunday Maple events and providing character lookup. Two separate deployment targets:

- **Backend**: FastAPI on Render (`backend/`)
- **Frontend**: Static HTML/CSS/Vue 3 (CDN) on Vercel (`frontend/`)

## Commands

### Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

Docker (matches Render production):
```bash
cd backend
docker compose up --build
```

Required env vars (`.env` in `backend/`):
- `NEXON_API_KEY` — Nexon Open API key
- `SUPABASE_URL` — Supabase project URL
- `SUPABASE_ANON_KEY` — Supabase anon key
- `NEXON_HTTP_TRUST_ENV` — set to `true` only if running behind a proxy

### Frontend

No build step — open HTML files directly in a browser or serve with any static server:
```bash
cd frontend
npx serve .
```

## Architecture

### Backend (`backend/`)

**Entry point**: `main.py` — registers three routers and global middleware (CORS, GZip).

**Routers** (`routers/`):
- `character.py` — `GET /api/character?nickname=...`: fetches ~17 Nexon API endpoints concurrently in batched `asyncio.gather` calls, assembles a `CharacterResponse`. Handles retry with exponential backoff for transient errors (429, 5xx, timeouts).
- `sunday.py` — `GET /api/sunday/history/recent` and `/api/sunday/history/all`: reads from Supabase (`calender_sunday` and `show_live` tables).
- `notice.py` — `GET /api/notices`: fetches 4 Nexon notice endpoints concurrently.

**Caching** (`core/cache.py`): In-memory TTL cache (single process, resets on restart). All external fetches go through `get_cache().get_or_set(...)`. TTLs and keys are centralized in `core/cache_keys.py`.

**External data sources**:
- Nexon Open API (`https://open.api.nexon.com/maplestory/v1`) — character data and notices. Dates use KST yesterday (or 2 days ago before 02:00 KST).
- Supabase — Sunday event history and live show schedule.

**Key pattern in `character.py`**: The `_nget(d, snake_key, camel_key)` helper handles both snake_case and camelCase Nexon API response shapes transparently throughout.

### Frontend (`frontend/`)

Standalone HTML pages using Vue 3 via CDN (no build toolchain):
- `index.html` — homepage with character search and recent Sunday history
- `calendar.html` — full Sunday event calendar
- `result.html` — character detail page
- `sunday.html` — Sunday Maple prediction/info
- `board.html` — notice board
- `dashboard.html` — two sections only: (1) benefits that appeared most in the last 52 Sundays, each with a
  52-week strip and its typical cadence; (2) the full archive in a scroll box, tabbed 혜택별 / 날짜별

`dashboard.html` is the one page that does not call the backend. It loads
`frontend/data/sunday-cycles.js` via a plain `<script src>` (which sets `window.SUNDAY_CYCLES`) —
deliberately not `fetch` + JSON, so the page still works when the HTML is opened directly over
`file://`. Regenerate that file with `python tools/build_sunday_cycles.py [원본.txt]` whenever
가마님's "역대 썬데이메이플 정리" post is updated — "경과"/"주기 초과" are computed against the
browser's current date, so stale data quietly ages.

All pages call the backend API directly. The backend URL is hardcoded in each HTML file's `<script>` section. `vercel.json` enables clean URLs.

### Supabase Tables

- `calender_sunday` — columns: `date`, `main_event`, `perks_text` (Sunday event history)
- `show_live` — columns: `event`, `live_show_day`, `note` (broadcast schedule)
