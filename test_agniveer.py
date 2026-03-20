#!/usr/bin/env python3
"""
Agniveer API - Full Automated Test Suite
Run: python test_agniveer.py
Requires: pip install requests
"""

import requests
import json
import sys
import time
from datetime import date, datetime

BASE = "http://127.0.0.1:8001"
TOKEN = None
REFRESH_TOKEN = None
SOLDIER_ID = None
BATTALION_ID = None

PASS = "\033[92m✓\033[0m"
FAIL = "\033[91m✗\033[0m"
SKIP = "\033[93m–\033[0m"
BOLD = "\033[1m"
RESET = "\033[0m"

results = []

def h(token=None):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers

def bearer(token=None):
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers

def run(label, method, path, *, params=None, json_body=None, form_body=None,
        auth=False, bearer_auth=False, expected_status=None, extract=None):
    global TOKEN
    url = BASE + path
    token = TOKEN if (auth or bearer_auth) else None
    req_headers = h(token) if not bearer_auth else bearer(token)
    if form_body:
        req_headers = {"Authorization": f"Bearer {token}"} if token else {}

    try:
        if method == "GET":
            r = requests.get(url, headers=req_headers, params=params, timeout=8)
        elif method == "POST":
            if form_body:
                r = requests.post(url, data=form_body, headers=req_headers, params=params, timeout=8)
            else:
                r = requests.post(url, headers=req_headers, json=json_body, params=params, timeout=8)
        elif method == "PUT":
            r = requests.put(url, headers=req_headers, json=json_body, params=params, timeout=8)
        elif method == "DELETE":
            r = requests.delete(url, headers=req_headers, params=params, timeout=8)
        else:
            raise ValueError(f"Unknown method {method}")

        status = r.status_code
        try:
            body = r.json()
        except Exception:
            body = r.text

        ok = (status < 400) if expected_status is None else (status == expected_status)
        icon = PASS if ok else FAIL
        status_str = f"{status}"
        note = ""

        extracted = None
        if ok and extract and isinstance(body, dict):
            extracted = body.get(extract)

        results.append((label, ok, status, body))
        print(f"  {icon} [{status_str}] {label}")
        if not ok:
            snippet = json.dumps(body)[:200] if isinstance(body, dict) else str(body)[:200]
            print(f"       {FAIL} {snippet}")

        return body, ok, extracted

    except requests.exceptions.ConnectionError:
        print(f"  {FAIL} [ERR] {label} — Cannot connect to {BASE}. Is the server running?")
        results.append((label, False, 0, "Connection refused"))
        sys.exit(1)
    except Exception as e:
        print(f"  {FAIL} [ERR] {label} — {e}")
        results.append((label, False, 0, str(e)))
        return None, False, None


# ─── Unique test user ────────────────────────────────────────────────────────

# Fix the email in your test data
TEST_USER = {
    "email": "testuser@agniveer.in",   # ← real-looking domain
    "username": "testuser01",
    "full_name": "Test User",
    "password": "TestPass@123",
    "role": "candidate"
}

ts = int(time.time())
TEST_EMAIL    = f"test_{ts}@agniveer.test"
TEST_USERNAME = f"testuser_{ts}"
TEST_PASSWORD = "TestPass@1234"
TEST_FULLNAME = "Test Soldier"

print(f"\n{BOLD}{'─'*55}{RESET}")
print(f"{BOLD}  Agniveer API Test Suite — {BASE}{RESET}")
print(f"{BOLD}{'─'*55}{RESET}")


# ─── 1. HEALTH ───────────────────────────────────────────────────────────────
print(f"\n{BOLD}[1] Health Checks{RESET}")
run("GET /health",           "GET", "/health")
run("GET /health/ai",        "GET", "/health/ai")
run("GET /api/v1/auth/health",         "GET", "/api/v1/auth/health")
run("GET /api/v1/recruitment/health",  "GET", "/api/v1/recruitment/health")
run("GET /api/v1/soldier/health",      "GET", "/api/v1/soldier/health")
run("GET /api/v1/training/health",     "GET", "/api/v1/training/health")
run("GET /api/v1/notifications/health","GET", "/api/v1/notifications/health")
run("GET /api/v1/reports/health",      "GET", "/api/v1/reports/health")
run("GET /api/v1/ml/health",           "GET", "/api/v1/ml/health")
run("GET /api/v1/documents/health",    "GET", "/api/v1/documents/health")
run("GET /api/v1/weather/health",      "GET", "/api/v1/weather/health")
run("GET /api/v1/ai predict/status",   "GET", "/api/v1/ai/predict/status")


# ─── 2. AUTH ─────────────────────────────────────────────────────────────────
print(f"\n{BOLD}[2] Auth Service{RESET}")
run("GET /api/v1/auth/ (ping)", "GET", "/api/v1/auth/")

body, ok, _ = run(
    "POST /auth/register",
    "POST", "/api/v1/auth/register",
    json_body={
        "email": TEST_EMAIL,
        "username": TEST_USERNAME,
        "full_name": TEST_FULLNAME,
        "password": TEST_PASSWORD,
        "role": "candidate"
    },
    expected_status=201
)

body, ok, _ = run(
    "POST /auth/login",
    "POST", "/api/v1/auth/login",
    form_body={
        "username": TEST_USERNAME,
        "password": TEST_PASSWORD,
        "grant_type": "password"
    },
    expected_status=200
)
if ok and isinstance(body, dict):
    TOKEN = body.get("access_token")
    REFRESH_TOKEN = body.get("refresh_token")
    print(f"       → Token acquired: {TOKEN[:30]}..." if TOKEN else "       → No token in response!")

if not TOKEN:
    print(f"\n{FAIL} Cannot proceed without auth token. Aborting.")
    sys.exit(1)

run("GET /auth/me", "GET", "/api/v1/auth/me", auth=True)

run("PUT /auth/me", "PUT", "/api/v1/auth/me",
    json_body={"full_name": "Updated Test Soldier"},
    auth=True)

run("POST /auth/password/change", "POST", "/api/v1/auth/password/change",
    json_body={"current_password": TEST_PASSWORD, "new_password": "NewPass@5678"},
    auth=True)
# Switch to new password
TEST_PASSWORD = "NewPass@5678"

if REFRESH_TOKEN:
    run("POST /auth/refresh", "POST", "/api/v1/auth/refresh",
        params={"refresh_token": REFRESH_TOKEN})


# ─── 3. RECRUITMENT ──────────────────────────────────────────────────────────
print(f"\n{BOLD}[3] Recruitment Service{RESET}")
run("GET /recruitment/ (ping)", "GET", "/api/v1/recruitment/")

body, ok, _ = run(
    "POST /recruitment/apply",
    "POST", "/api/v1/recruitment/apply",
    json_body={
        "date_of_birth": "2000-06-15",
        "gender": "male",
        "blood_group": "B+",
        "aadhaar_number": "123456789012",
        "address": "123 Test Street, Ahmedabad",
        "city": "Ahmedabad",
        "state": "Gujarat",
        "pincode": "380001",
        "father_name": "Test Father",
        "mother_name": "Test Mother",
        "emergency_contact_name": "Emergency Contact",
        "emergency_contact_phone": "9876543210",
        "education_qualification": "12th Pass",
        "passing_year": 2018,
        "marks_percentage": 72.5,
        "height_cm": 170,
        "weight_kg": 65.0,
        "chest_cm": 82
    },
    auth=True,
    expected_status=201
)

run("GET /recruitment/status",      "GET", "/api/v1/recruitment/status",      auth=True)
run("GET /recruitment/exam-centers","GET", "/api/v1/recruitment/exam-centers", params={"state": "Gujarat"})
run("GET /recruitment/exams",       "GET", "/api/v1/recruitment/exams")
run("GET /recruitment/admit-card",  "GET", "/api/v1/recruitment/admit-card",   auth=True)

body, ok, _ = run("GET /recruitment/exams/{1}", "GET", "/api/v1/recruitment/exams/1")


# ─── 4. SOLDIER SERVICE ──────────────────────────────────────────────────────
print(f"\n{BOLD}[4] Soldier Service{RESET}")
run("GET /soldier/ (ping)", "GET", "/api/v1/soldier/")

# Create battalion first (admin action — may fail without admin role, that's OK)
body, ok, _ = run(
    "POST /soldier/battalions",
    "POST", "/api/v1/soldier/battalions",
    json_body={
        "battalion_name": "Test Battalion Alpha",
        "battalion_code": f"TBA{ts % 10000}",
        "location": "Ahmedabad Training Ground",
        "city": "Ahmedabad",
        "state": "Gujarat",
        "commander_name": "Col. Test"
    },
    auth=True,
    expected_status=201
)
if ok and isinstance(body, dict):
    BATTALION_ID = body.get("id")

run("GET /soldier/battalions", "GET", "/api/v1/soldier/battalions")
if BATTALION_ID:
    run(f"GET /soldier/battalions/{BATTALION_ID}", "GET", f"/api/v1/soldier/battalions/{BATTALION_ID}")

# Get my soldier profile (may 404 if not a soldier role)
run("GET /soldier/profile",    "GET", "/api/v1/soldier/profile",    auth=True)
run("GET /soldier/medical-records", "GET", "/api/v1/soldier/medical-records", auth=True)
run("GET /soldier/training-records","GET", "/api/v1/soldier/training-records", auth=True)
run("GET /soldier/schedule",   "GET", "/api/v1/soldier/schedule",
    params={"date": str(date.today())}, auth=True)
run("GET /soldier/equipment",  "GET", "/api/v1/soldier/equipment",  auth=True)
run("GET /soldier/events",     "GET", "/api/v1/soldier/events",     auth=True)
run("GET /soldier/stipends",   "GET", "/api/v1/soldier/stipends",   auth=True)
run("GET /soldier/rankings",   "GET", "/api/v1/soldier/rankings",
    params={"month": datetime.now().month, "year": datetime.now().year})
run("GET /soldier/sos/active", "GET", "/api/v1/soldier/sos/active")


# ─── 5. TRAINING SERVICE ─────────────────────────────────────────────────────
print(f"\n{BOLD}[5] Training Service{RESET}")
run("GET /training/ (ping)", "GET", "/api/v1/training/")

run("GET /training/records", "GET", "/api/v1/training/records",
    params={"training_type": "fitness"}, auth=True)


# ─── 6. NOTIFICATIONS ────────────────────────────────────────────────────────
print(f"\n{BOLD}[6] Notification Service{RESET}")
run("GET /notifications/ (ping)", "GET", "/api/v1/notifications/")

run("POST /notifications/send", "POST", "/api/v1/notifications/send",
    params={"user_id": 1, "title": "Test Notification", "body": "API test message", "notification_type": "info"},
    auth=True)

run("POST /notifications/broadcast", "POST", "/api/v1/notifications/broadcast",
    params={"title": "Broadcast Test", "body": "Testing broadcast", "notification_type": "info"},
    auth=True)

run("GET /notifications/sos/active",  "GET", "/api/v1/notifications/sos/active", auth=True)
run("GET /notifications/sos/history", "GET", "/api/v1/notifications/sos/history", auth=True)


# ─── 7. ML SERVICE ───────────────────────────────────────────────────────────
print(f"\n{BOLD}[7] ML Service{RESET}")
run("GET /ml/ (ping)", "GET", "/api/v1/ml/")

run("POST /ml/predict/performance", "POST", "/api/v1/ml/predict/performance",
    json_body={
        "running_time_minutes": 14.5,
        "pushups_count": 42,
        "pullups_count": 12,
        "endurance_score": 78.5,
        "shooting_accuracy": 85.0,
        "decision_score": 80.0
    }, auth=True)

run("POST /ml/predict/injury-risk", "POST", "/api/v1/ml/predict/injury-risk",
    json_body={
        "training_intensity": 7.5,
        "training_frequency": 5,
        "recovery_days": 2,
        "previous_injuries": 0,
        "sleep_hours": 7.5,
        "stress_level": 4.0
    }, auth=True)

run("POST /ml/analyze/trend", "POST", "/api/v1/ml/analyze/trend",
    json_body={"soldier_id": 1, "months": 3},
    auth=True)

run("POST /ml/training/optimize", "POST", "/api/v1/ml/training/optimize",
    params={"soldier_id": 1}, auth=True)

run("POST /ml/medical/analyze", "POST", "/api/v1/ml/medical/analyze",
    params={"soldier_id": 1}, auth=True)


# ─── 8. AI SERVICE ───────────────────────────────────────────────────────────
print(f"\n{BOLD}[8] AI Service (RAG / OCR / Prediction / Summarization){RESET}")

run("POST /ai/rag/add_document", "POST", "/api/v1/ai/rag/add_document",
    params={"title": "Agnipath Scheme Overview", "content": "The Agnipath scheme is India's military recruitment scheme for short-term service. Agniveers serve 4 years.", "category": "recruitment"},
    bearer_auth=True)

run("POST /ai/ask", "POST", "/api/v1/ai/ask",
    json_body={"query": "What is the Agnipath scheme?", "top_k": 3},
    bearer_auth=True)

run("POST /ai/predict", "POST", "/api/v1/ai/predict",
    json_body={"age": 22, "bmi": 22.5, "pushups": 45, "pullups": 14, "run_time": 13.5, "training_days": 22},
    bearer_auth=True)

run("POST /ai/summarize", "POST", "/api/v1/ai/summarize",
    json_body={"text": "The Agnipath scheme is a military recruitment scheme in India. Under this scheme, young people serve in the armed forces for four years. They receive training, stipend, and benefits. After four years, 25% are retained as regular soldiers, while the rest return to civilian life with a Seva Nidhi corpus.", "max_length": 60, "min_length": 20},
    bearer_auth=True)

run("POST /ai/extract_entities", "POST", "/api/v1/ai/extract_entities",
    params={"text": "Colonel Ramesh from Ahmedabad joined the Indian Army in 2020."},
    bearer_auth=True)

run("POST /ai/analyze_sentiment", "POST", "/api/v1/ai/analyze_sentiment",
    params={"text": "The training program is excellent and very effective for soldiers."},
    bearer_auth=True)

run("POST /ai/extract_keywords", "POST", "/api/v1/ai/extract_keywords",
    params={"text": "Agnipath military training scheme India recruitment soldiers battalion", "top_n": 5},
    bearer_auth=True)


# ─── 9. WEATHER SERVICE ──────────────────────────────────────────────────────
print(f"\n{BOLD}[9] Weather Service{RESET}")
run("GET /weather/ (ping)", "GET", "/api/v1/weather/")

run("GET /weather/current",  "GET", "/api/v1/weather/current",
    params={"location": "Ahmedabad"}, auth=True)

run("GET /weather/forecast", "GET", "/api/v1/weather/forecast",
    params={"location": "Ahmedabad", "days": 3}, auth=True)

run("POST /weather/recommendation", "POST", "/api/v1/weather/recommendation",
    params={"location": "Ahmedabad"}, auth=True)

run("POST /weather/adjust-schedule", "POST", "/api/v1/weather/adjust-schedule",
    json_body={
        "schedule": [
            {"activity": "Morning run", "duration": 30, "outdoor": True},
            {"activity": "Weapons training", "duration": 60, "outdoor": False}
        ],
        "location": "Ahmedabad"
    }, auth=True)


# ─── 10. REPORTS ─────────────────────────────────────────────────────────────
print(f"\n{BOLD}[10] Report Service{RESET}")
run("GET /reports/ (ping)", "GET", "/api/v1/reports/")

run("GET /reports/soldier/1/daily",   "GET", "/api/v1/reports/soldier/1/daily",
    params={"report_date": str(date.today())}, auth=True)
run("GET /reports/soldier/1/monthly", "GET", "/api/v1/reports/soldier/1/monthly",
    params={"month": datetime.now().month, "year": datetime.now().year}, auth=True)
run("GET /reports/soldier/1/medical", "GET", "/api/v1/reports/soldier/1/medical", auth=True)
run("GET /reports/soldier/1/stipend", "GET", "/api/v1/reports/soldier/1/stipend",
    params={"year": datetime.now().year}, auth=True)


# ─── 11. LOGOUT ──────────────────────────────────────────────────────────────
print(f"\n{BOLD}[11] Logout{RESET}")
run("POST /auth/logout", "POST", "/api/v1/auth/logout", auth=True)


# ─── SUMMARY ─────────────────────────────────────────────────────────────────
total   = len(results)
passed  = sum(1 for _, ok, *_ in results if ok)
failed  = total - passed

print(f"\n{BOLD}{'─'*55}{RESET}")
print(f"{BOLD}  Results: {passed}/{total} passed  |  {failed} failed{RESET}")
print(f"{BOLD}{'─'*55}{RESET}")

if failed:
    print(f"\n{BOLD}Failed endpoints:{RESET}")
    for label, ok, status, body in results:
        if not ok:
            snippet = json.dumps(body)[:300] if isinstance(body, dict) else str(body)[:300]
            print(f"  {FAIL} [{status}] {label}")
            print(f"       {snippet}")
    print()
    sys.exit(1)
else:
    print(f"\n  {PASS} All APIs are responding correctly!\n")
    sys.exit(0)
