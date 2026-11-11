# LOG

## 2026-11-10 — Wayfinder map #5 shipped (branch `wf/5-auth`, PR #118)

**Status: Done** (all 3 tickets closed; PR filed + watched; NOT MERGED)

- **Pre-flight**: gh ✅, git ✅, **OCR LLM ❌** (100.87.250.35:20128 connection refused, retried 3×). User chose to proceed; OCR axis skipped everywhere, compensated by code-review skill sub-agents + CodeRabbit/parthpr bots.
- **Phase 1 (HITL)**: #6 grilling session — human decided: signed cookie + hardening (SECRET_KEY env var, HTTPOnly/SameSite=Lax, 7-day permanent); password min 8 + empty-field checks; simple flow + /logout, no next-param.
- **Phase 2 (AFK, single-PR mode — 2 code-changing tickets < 5)**:
  - #7: login POST, signup validation, logout route, login.html form wiring, session hardening. Self-review 2 iterations (code-review axis): signup flashes block added, exact flash-text assertions, docs updated. 11 tests.
  - #8: login_required decorator on 5 routes; redundant inline checks removed. Self-review 1 iteration: client fixture deduped into conftest.py. 5 tests. 16 total green.
- **PR**: [#118](https://github.com/parth5012/EdTech-Dashboard/pull/118) filed via pr template, bots triggered (@coderabbitai review, /review), watch_pull_request active. Checks: Vercel ✅, GitGuardian ✅, CodeRabbit pending.
- **Skipped**: ocr-review axis (service down) — noted on both ticket comments and PR body.

# LEARNINGS (edge cases)

- `app.secret_key` was reading `FLASK_API_KEY` (an LLM API key env var) — wrong var for a session secret. Now `SECRET_KEY`. **Deployment must set `SECRET_KEY` or sessions break.** Documented in `static/codebase_audit.md` §10.
- Flask-Session filesystem storage is unusable on Vercel (serverless) — signed cookie chosen deliberately.
- Postgres-only engine options (`sslmode` connect args) crash sqlite; made conditional on URI scheme.
- Flash messages are silently discarded if a template lacks a `get_flashed_messages()` block — signup.html was missing it; validation errors never displayed.
- Testing this app requires env vars at import time (`SECRET_KEY`, `GEMINI_API_KEY`, `GROQ_API_KEY`, sqlite `URI`) — handled in `test/conftest.py` before utils imports.
