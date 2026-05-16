"""
EdTech Dashboard - End-to-End Integration Test
Tests: signup -> upload resume -> dashboard -> mock interview -> results
"""
import requests
import os
import sys
import time

BASE_URL = "http://127.0.0.1:5000"
RESUME_PATH = os.path.join(os.path.dirname(__file__), "resume4.pdf")
TEST_EMAIL = "e2etest_auto@example.com"
TEST_PASSWORD = "Test@1234"
TEST_USERNAME = "e2etestuser"
JOB_DESC = (
    "We are hiring a Data Analyst at Google. The role requires Python, SQL, "
    "Data Visualization, Machine Learning, and experience with pandas and matplotlib. "
    "Candidates should have strong analytical skills and communication abilities."
)

PASS = "[PASS]"
FAIL = "[FAIL]"
INFO = "[INFO]"

def section(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print('='*60)

def check(label, condition, detail=""):
    status = PASS if condition else FAIL
    print(f"  {status} {label}", f"| {detail}" if detail else "")
    return condition

def run_tests():
    session = requests.Session()
    all_passed = True

    # ------------------------------------------------------------------ #
    section("STEP 1: Signup")
    # ------------------------------------------------------------------ #
    r = session.post(f"{BASE_URL}/signup", data={
        "username": TEST_USERNAME,
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD,
    }, allow_redirects=True)

    ok = r.status_code == 200 and ("login" in r.url or "PlacementReady" in r.text)
    all_passed &= check("Signup completes without 500", r.status_code != 500,
                        f"status={r.status_code} url={r.url}")
    check("Redirected after signup (login or home page)", ok, f"final url={r.url}")

    # ------------------------------------------------------------------ #
    section("STEP 2: Login")
    # ------------------------------------------------------------------ #
    r = session.post(f"{BASE_URL}/login", data={
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD,
    }, allow_redirects=True)

    login_ok = r.status_code == 200 and "user_dashboard" in r.url
    all_passed &= check("Login succeeds (redirects to user_dashboard)",
                        login_ok, f"status={r.status_code} url={r.url}")

    # ------------------------------------------------------------------ #
    section("STEP 3: Upload Resume -> Dashboard (LLM calls, may take 30-60s)")
    # ------------------------------------------------------------------ #
    if not os.path.exists(RESUME_PATH):
        print(f"  {FAIL} Resume file not found: {RESUME_PATH}")
        sys.exit(1)

    print(f"  {INFO} Uploading {RESUME_PATH} ...")
    start = time.time()
    with open(RESUME_PATH, "rb") as f:
        r = session.post(
            f"{BASE_URL}/upload_resume",
            data={"job_description": JOB_DESC, "email": TEST_EMAIL},
            files={"resume": ("resume4.pdf", f, "application/pdf")},
            allow_redirects=True,
            timeout=120,
        )
    elapsed = time.time() - start
    print(f"  {INFO} Request completed in {elapsed:.1f}s")

    dashboard_ok = r.status_code == 200 and "dashboard" in r.url
    all_passed &= check("Upload + dashboard loads (no 500)",
                        r.status_code != 500, f"status={r.status_code} url={r.url}")
    all_passed &= check("Redirected to /dashboard after upload",
                        dashboard_ok, f"url={r.url}")

    # Spot-check dashboard content
    if dashboard_ok:
        has_ats = "ats" in r.text.lower() or "score" in r.text.lower()
        check("Dashboard contains score content", has_ats)

    # ------------------------------------------------------------------ #
    section("STEP 4: Mock Interview (LLM generates questions, may take 20-30s)")
    # ------------------------------------------------------------------ #
    print(f"  {INFO} Requesting /mock ...")
    start = time.time()
    r = session.get(f"{BASE_URL}/mock", allow_redirects=True, timeout=120)
    elapsed = time.time() - start
    print(f"  {INFO} Request completed in {elapsed:.1f}s")

    mock_ok = r.status_code == 200 and "mock" in r.url
    all_passed &= check("Mock interview page loads (no 500)",
                        r.status_code != 500, f"status={r.status_code} url={r.url}")
    all_passed &= check("Mock interview URL reached (/mock)",
                        mock_ok, f"url={r.url}")

    if mock_ok:
        has_question = "question" in r.text.lower() or "interview" in r.text.lower()
        check("Mock page contains interview question content", has_question)

    # ------------------------------------------------------------------ #
    section("STEP 5: Results Page")
    # ------------------------------------------------------------------ #
    r = session.get(f"{BASE_URL}/results", allow_redirects=True, timeout=30)
    # Results requires interview_id in session — only populated after /submit
    # So it should redirect to home gracefully (our session guard fix)
    results_no_crash = r.status_code in (200, 302)
    all_passed &= check("Results page does not 500 (session guard working)",
                        r.status_code != 500, f"status={r.status_code} url={r.url}")
    check("Results redirects to home when no interview_id in session",
          "127.0.0.1:5000/" in r.url or r.url.endswith("/"), f"url={r.url}")

    # ------------------------------------------------------------------ #
    section("STEP 6: Error Handler Checks")
    # ------------------------------------------------------------------ #
    r = session.get(f"{BASE_URL}/nonexistent-xyz-page", timeout=10)
    all_passed &= check("404 handler returns 404 status", r.status_code == 404,
                        f"status={r.status_code}")
    check("404 page has custom content", "404" in r.text or "not found" in r.text.lower())

    # ------------------------------------------------------------------ #
    section("FINAL RESULT")
    # ------------------------------------------------------------------ #
    if all_passed:
        print(f"\n  {PASS} ALL CRITICAL CHECKS PASSED\n")
    else:
        print(f"\n  {FAIL} SOME CHECKS FAILED — review output above\n")

    return all_passed

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
