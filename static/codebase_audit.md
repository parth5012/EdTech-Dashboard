# EdTech Dashboard — Full Codebase Audit

## Overview

This audit covers the entire codebase at `d:\work\projects\EdTech-Dashboard`. Issues are grouped by severity and category.

---

## 🔴 Critical Bugs (Will Crash or Corrupt Data)

### 1. `verify_public_badge` returns a tuple, but is compared as a bool
**File:** `utils/verification.py:13-14`, **used in:** `main.py:208`

```python
# verification.py — returns a TUPLE (True, "message"), not a bool
def verify_public_badge(badge_url: str) -> bool:
    response = requests.get(badge_url)
    if response.status_code == 200:
        return True, "Badge found and valid."   # ← TUPLE!
    else:
        return False, "Badge not found or inaccessible."

# main.py line 208 — treats the return value as a bool
if verify_public_badge(list[i]):   # ← always True (non-empty tuple is truthy)
    count += 1
```
**Impact:** Certificate count is ALWAYS incremented regardless of actual badge validity, making the feature completely broken.

**Fix:** Change `verification.py` to `return True` / `return False` only.

---

### 2. `get_interview_ques` returns a dict, but is accessed as an object
**File:** `main.py:234–239`, `utils/llms.py:77-80`

```python
# llms.py — chain returns dict via .model_dump()
chain = interview_prompt | llm2 | parser1 | RunnableLambda(lambda x: x.model_dump())
res = chain.invoke(job_desc)
return res  # ← plain dict

# main.py — accessed as object attribute
n_ques = len(ques.questions)      # KeyError / AttributeError!
question=ques.questions[0],       # same crash
ques_obj=ques,
```
**Impact:** The `/mock` route will always crash with `AttributeError: 'dict' object has no attribute 'questions'`.

**Fix:** Either remove `.model_dump()` from the chain (return the Pydantic object), or access as `ques["questions"]` in `main.py`.

---

### 3. `get_achievements` same pattern — dict vs object mismatch
**File:** `main.py:172`, `utils/llms.py:56-60`

```python
# llms.py returns dict (via .model_dump())
res = chain.invoke(...)   # returns dict

# main.py line 172 — dict subscript is fine here, but:
n_crtf = len(json_content["certifications"])  # ← OK
# main.py line 204:
if content["certificate_links"]:              # ← OK
```
This particular access pattern uses `[]` so it _technically_ works on a dict, but is inconsistent with how `InterviewQues` is handled. The real danger is that `certificates()` route deletes `session["content"]` (line 203) before it can be recovered on error.

---

### 4. `dashboard` route crashes if `Resume` not found
**File:** `main.py:146-147`

```python
resume = Resume.query.filter_by(user_id=user_id).first()
content = resume.resume_text   # ← AttributeError if resume is None
```
**Impact:** If a user lands on `/dashboard` without an associated resume (e.g., session `user_id` set via login, not via `upload_resume`), this crashes with `AttributeError: 'NoneType' object has no attribute 'resume_text'`.

---

### 5. `dashboard` route: `job_application.query.update()` is wrong SQLAlchemy API
**File:** `main.py:184`

```python
job_application.query.update(values={"certifications_count": n_crtf})
```
This is called on an **instance**, not a **class**. `Model.instance.query` does not exist in SQLAlchemy 2.x. The update never happens and this line silently fails or raises an `AttributeError`.

**Fix:** Use `job_application.certifications_count = n_crtf` directly, since the object is already being added to the session on line 188.

---

### 6. `submit` endpoint has no auth/session guard
**File:** `main.py:244-267`

```python
@app.route("/api/mock-interview/submit", methods=["post"])
def submit():
    if request.method == "POST":
        ...
        application_id = session["application_id"]  # KeyError if no session!
```
**Impact:** Any unauthenticated POST to `/api/mock-interview/submit` raises `KeyError`. There is no `if "application_id" not in session: return 401`.

---

### 7. `results` route: unguarded `session["interview_id"]` access
**File:** `main.py:272`

```python
id = session["interview_id"]   # KeyError if user visits /results directly
```
No session guard. Direct navigation or session expiry crashes with an unhandled `KeyError`.

---

### 8. `upload_resume` variable name collision
**File:** `main.py:117,130`

```python
resume = request.files["resume"]   # FileStorage object
...
resume = Resume(user_id=user_id, resume_text=content)   # Overwrites the variable!
```
The `resume` variable is reused for two completely different objects. While it doesn't crash in the current flow (the file is already saved before the reassignment), this is a maintenance hazard.

---

### 9. Module-level side-effect in `verification.py`
**File:** `utils/verification.py:3`

```python
url = "https://api.credly.com/v1/badges/bc86b51a-..."
```
This line executes a variable assignment at **import time** (harmless), but the intent seems to be an API call. If someone uncomments the block above it, it would make an outbound HTTP request during app startup — a hidden side-effect.

---

## 🟠 Security Vulnerabilities

### 10. Secret key can be `None`
**File:** `utils/app.py:13`

```python
app.secret_key = os.getenv('FLASK_API_KEY')
```
If `FLASK_API_KEY` is missing from `.env`, `secret_key` becomes `None`. Flask will refuse to use cookie-based sessions securely, making the app either crash or use a predictable empty key.

**Fix:** Add a guard:
```python
secret_key = os.getenv('FLASK_API_KEY')
if not secret_key:
    raise RuntimeError("FLASK_API_KEY is not set!")
app.secret_key = secret_key
```

---

### 11. No CSRF protection on state-changing forms
**Files:** `main.py` — `/signup`, `/upload_resume`, `/login`

None of the POST forms use Flask-WTF CSRF tokens. This exposes the app to Cross-Site Request Forgery attacks.

---

### 12. `upload_resume` allows any email to hijack sessions
**File:** `main.py:124-128`

```python
email = request.form.get("email")
user = User.query.filter_by(email=email).first()
...
session["user_id"] = user.id
```
Any unauthenticated user can POST an arbitrary email to `/upload_resume` and hijack another user's session. There is no check that the logged-in user owns that email.

---

### 13. No file type validation on resume upload
**File:** `main.py:117-122`

```python
resume = request.files["resume"]
filename = secure_filename(resume.filename)
filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
resume.save(filepath)
```
There's no validation that the uploaded file is actually a PDF or DOCX. A user could upload `.exe`, `.sh`, or malicious files. `secure_filename` only sanitizes the name, not the content.

---

### 14. `/debug-sentry` endpoint left in production
**File:** `main.py:287-292`

```python
@app.route("/debug-sentry")
def trigger_error():
    division_by_zero = 1 / 0
```
This intentional crash endpoint is publicly accessible. It should be removed before going to production or guarded behind an admin check.

---

### 15. Login returns raw string on failure
**File:** `main.py:104`

```python
return "Invalid email or password"
```
This bypasses the template system, exposes no consistent UI, and misses the opportunity to use `flash()` + redirect. It also returns HTTP 200 on failure, which can confuse clients.

---

## 🟡 Architectural Flaws

### 16. `resume_path = 0` — global mutable state
**File:** `main.py:49`

```python
resume_path = 0
```
This global is declared but never actually used (the real path is handled via the session). In a multi-threaded WSGI server (gunicorn), global mutable state is a concurrency bug waiting to happen.

---

### 17. `datetime.now()` called at class definition time (frozen timestamp)
**File:** `utils/models.py:18, 41, 62, 98, 128`

```python
created_at: Mapped[datetime] = mapped_column(types.DateTime, default=datetime.now())
```
`datetime.now()` is called **once** when the module is imported. Every record will share the same frozen timestamp (the server start time).

**Fix:** Pass the callable, not its return value:
```python
default=datetime.now   # without ()
```

---

### 18. Dashboard route does N+1 LLM calls sequentially
**File:** `main.py:154-170`

`get_job_details`, `get_achievements`, `get_str_output`, `get_readiness_score`, and `get_ats_score` are all called sequentially. A `LangGraph` parallel workflow (`get_dashboard_workflow`) exists in `utils/graphs.py` but is commented out.

**Impact:** Each call has significant latency (LLM inference). Running 5 calls sequentially makes the dashboard endpoint take 10–30 seconds to respond.

---

### 19. LangGraph workflow is dead code
**File:** `main.py:150-153`, `utils/graphs.py`

The entire `get_dashboard_workflow()` and `graphs.py` module is effectively dead code — commented out and never invoked. The parallel graph would give a significant latency reduction.

---

### 20. Session used as a temporary data store between requests
**File:** `main.py` — `session["content"]`, `session["desc"]`, `session["application_id"]`

Sensitive data (full resume content as JSON, job descriptions, DB IDs) is stored in the Flask client-side cookie session. Flask sessions are signed but not encrypted. The data is visible to the client.

**Fix:** Use server-side sessions (e.g., `flask-session` with Redis or a DB backend).

---

### 21. `get_interview_ques` passes a plain `str` but the prompt expects a dict
**File:** `utils/llms.py:78`

```python
res = chain.invoke(job_desc)   # job_desc is a str
```
The `interview_prompt` template has `input_variables=["job_desc"]`, meaning it expects `{"job_desc": "..."}`, not a raw string. This likely either fails silently (LangChain infers the key) or raises a `KeyError`.

---

### 22. `get_str_output` passes a plain string to a prompt expecting a variable
**File:** `utils/llms.py:66`

```python
chain = analyser_prompt | llm1 | StrOutputParser()
return chain.invoke(resume_content)  # str, but prompt needs {"resume_content": ...}
```
Same issue as above — the `analyser_prompt` has `{resume_content}` placeholder, so `.invoke()` needs a dict.

---

### 23. `is_answer` LLM returns a string, cast to bool is always `True`
**File:** `utils/llms.py:87`

```python
res = chain.invoke({...})  # Returns "True" or "False" string
return bool(res)           # bool("False") == True! Non-empty string is always True
```
**Fix:**
```python
return res.strip().lower() == "true"
```

---

### 24. `get_performance_score` only uses the first platform link
**File:** `utils/stats.py:297`

```python
platform, username = parse_input(json_content['platform_links'][0])
```
Only the first platform link from the resume is scored. All others are ignored.

---

### 25. `user_dashboard` route has no authentication check
**File:** `main.py:109-111`

```python
@app.route("/user_dashboard")
def user_dashboard():
    return render_template("user_dashboard.html")
```
Any unauthenticated user can view the dashboard page. There is no `if "user_id" not in session: redirect(login)` guard.

---

### 26. `MockInterview` always queries the first record for a user
**File:** `main.py:229-230`

```python
jobapplication = JobApplication.query.filter_by(user_id=user_id).first()
```
If a user has applied to multiple jobs, this always picks the oldest application, not the most recent one from the session flow.

---

## 🔵 Code Quality Issues

### 27. Shadowing built-in `list`
**File:** `main.py:205`

```python
list = content["certificate_links"]
```
The variable name `list` shadows Python's built-in `list` type, which can cause surprising bugs in the same scope.

---

### 28. `get_resume_content` type hint uses `__file__`
**File:** `utils/llms.py:39`, `utils/answer.py:7`

```python
def get_resume_content(resume: __file__) -> str:
```
`__file__` is a module-level string (the file path of the current module), not a type. The correct annotation is `str` or `pathlib.Path`.

---

### 29. Huge amount of commented-out dead code
**Files:** `main.py`, `utils/stats.py`, `utils/ats.py`, `utils/verification.py`

`utils/ats.py` is entirely commented-out code. `utils/stats.py` has ~150 lines of commented-out Streamlit code. This indicates the project was migrated from Streamlit but the old code was never cleaned up.

---

### 30. `db.py` exists but is unused
**File:** `utils/db.py`

There is a separate `utils/db.py` file but the database setup is done in `utils/app.py`. This creates confusion about the single source of truth for DB configuration.

---

### 31. `mock_fixed.html` and `questions.html` are orphan templates
**Files:** `templates/mock_fixed.html`, `templates/questions.html`

These templates are never referenced by any route in `main.py`, suggesting they are leftover experiment files.

---

### 32. `traces_sample_rate=1.0` in production Sentry config
**File:** `main.py:46`

A sample rate of `1.0` captures 100% of transactions. This is fine for development but will generate significant Sentry quota consumption in production.

---

## ✅ Suggested Improvements & New Features

### Architecture

| Priority | Suggestion |
|---|---|
| 🔴 High | **Blueprints**: Split `main.py` into Flask Blueprints — `auth`, `dashboard`, `interview` |
| 🔴 High | **Auth decorator**: Create a `@login_required` decorator to protect all authenticated routes consistently |
| 🔴 High | **Restore the LangGraph parallel workflow** for dashboard to cut latency by ~80% |
| 🟠 Medium | **Server-side sessions** (`flask-session` + Redis) instead of cookie-based session storage |
| 🟠 Medium | **Background tasks** (Celery + Redis or `rq`) for LLM calls so the HTTP response doesn't time out |
| 🟠 Medium | **Input validation layer** with Flask-WTF or Pydantic for all form inputs |
| 🟡 Low | **API versioning**: Prefix API routes as `/api/v1/...` consistently |

### New Features

| Feature | Description |
|---|---|
| 📊 Progress Tracker | Store historical ATS scores per user across multiple applications to show improvement over time |
| 📝 Cover Letter Generator | The `generate_cover_letter` function already exists in `llms.py` but has no route or UI |
| 💬 Filler Word Detector | `find_filler_word_count` in `answer.py` is implemented but not wired to any route |
| 🧠 Vocal Analysis | The `InterviewAnswer.vocal_analysis` field exists in the DB model but is never populated |
| 📋 Multi-Platform Score | Score ALL platform links (LeetCode + GitHub + Codeforces) and aggregate, not just the first one |
| 🔔 Email Notifications | Notify users via email when interview results are ready |
| 👤 Profile Page | A dedicated user profile page — currently `user_dashboard.html` is a placeholder with no data |
| 🔑 OAuth Login | Google/GitHub OAuth to simplify signup flow |
| 📱 Async Submission UX | Use WebSockets or SSE to stream LLM results to the frontend instead of a blocking HTTP call |
