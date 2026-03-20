import warnings
warnings.filterwarnings("ignore")

import requests
import json
import sys
from datetime import date, timedelta

BASE = "http://127.0.0.1:8001"
token = None
candidate_id = None
soldier_id = None
battalion_id = None

PASS = "\033[92m  ✓\033[0m"
FAIL = "\033[91m  ✗\033[0m"
INFO = "\033[94m  ℹ\033[0m"

def divider(title):
    print(f"\n{'─'*55}")
    print(f"  {title}")
    print(f"{'─'*55}")

def check(label, res, expect=None):
    ok = res.status_code in (expect or [200, 201])
    icon = PASS if ok else FAIL
    print(f"{icon} [{res.status_code}] {label}")
    if not ok:
        try:
            body = res.json()
            snippet = json.dumps(body)[:200]
        except Exception:
            snippet = res.text[:200]
        print(f"       \033[91m✗ {snippet}\033[0m")
    return ok

def get(path, auth=False, params=None):
    h = {"Authorization": f"Bearer {token}"} if auth and token else {}
    return requests.get(BASE + path, headers=h, params=params, timeout=10)

def post(path, body=None, auth=False, form=False, params=None):
    h = {"Authorization": f"Bearer {token}"} if auth and token else {}
    if form:
        h["Content-Type"] = "application/x-www-form-urlencoded"
        return requests.post(BASE + path, data=body, headers=h, params=params, timeout=10)
    return requests.post(BASE + path, json=body, headers=h, params=params, timeout=10)

def put(path, body, auth=True):
    h = {"Authorization": f"Bearer {token}"} if auth and token else {}
    return requests.put(BASE + path, json=body, headers=h, timeout=10)

# ─── Test user credentials ────────────────────────────────────────────────────
TEST_EMAIL    = "testuser@agniveer.in"
TEST_USERNAME = "testuser01"
TEST_PASSWORD = "TestPass@123"
TEST_FULLNAME = "Test Agniveer User"

today = date.today().isoformat()

# ─────────────────────────────────────────────────────────────────────────────
# [1] Health Checks
# ─────────────────────────────────────────────────────────────────────────────
divider("[1] Health Checks")
check("GET /health",                      get("/health"))
check("GET /health/ai",                   get("/health/ai"))
check("GET /api/v1/auth/health",          get("/api/v1/auth/health"))
check("GET /api/v1/recruitment/health",   get("/api/v1/recruitment/health"))
check("GET /api/v1/soldier/health",       get("/api/v1/soldier/health"))
check("GET /api/v1/training/health",      get("/api/v1/training/health"))
check("GET /api/v1/notifications/health", get("/api/v1/notifications/health"))
check("GET /api/v1/reports/health",       get("/api/v1/reports/health"))
check("GET /api/v1/ml/health",            get("/api/v1/ml/health"))
check("GET /api/v1/documents/health",     get("/api/v1/documents/health"))
check("GET /api/v1/weather/health",       get("/api/v1/weather/health"))

# ─────────────────────────────────────────────────────────────────────────────
# [2] Auth Service
# ─────────────────────────────────────────────────────────────────────────────
divider("[2] Auth Service")
check("GET /api/v1/auth/ (ping)", get("/api/v1/auth/"))

# Register — 201 fresh, 400/409 already exists — both fine on reruns
res = post("/api/v1/auth/register", {
    "email":     TEST_EMAIL,
    "username":  TEST_USERNAME,
    "full_name": TEST_FULLNAME,
    "password":  TEST_PASSWORD,
    "role":      "candidate"
})
if res.status_code in (201, 200):
    print(f"{PASS} [{res.status_code}] POST /api/v1/auth/register")
elif res.status_code in (400, 409):
    print(f"{INFO} [{res.status_code}] POST /api/v1/auth/register — user already exists, continuing")
else:
    print(f"{FAIL} [{res.status_code}] POST /api/v1/auth/register")
    try:
        print(f"       \033[91m✗ {json.dumps(res.json())[:300]}\033[0m")
    except Exception:
        pass

# Login
res = post("/api/v1/auth/login",
    body={"username": TEST_USERNAME, "password": TEST_PASSWORD, "grant_type": "password"},
    form=True
)
if check("POST /api/v1/auth/login", res):
    data = res.json()
    token = data.get("access_token")
    print(f"{INFO} Token acquired: {token[:40]}...")
else:
    print("\033[91m✗ Cannot proceed without auth token. Aborting.\033[0m")
    sys.exit(1)

check("GET  /api/v1/auth/me",             get("/api/v1/auth/me", auth=True))
check("PUT  /api/v1/auth/me",             put("/api/v1/auth/me", {"full_name": "Updated Test User"}))
check("POST /api/v1/auth/password/change",post("/api/v1/auth/password/change", {
    "current_password": TEST_PASSWORD,
    "new_password":     TEST_PASSWORD
}, auth=True))

# ─────────────────────────────────────────────────────────────────────────────
# [3] Recruitment Service
# ─────────────────────────────────────────────────────────────────────────────
divider("[3] Recruitment Service")
check("GET /api/v1/recruitment/ (ping)",    get("/api/v1/recruitment/"))
check("GET /api/v1/recruitment/exams",      get("/api/v1/recruitment/exams"))
check("GET /api/v1/recruitment/exam-centers",
      get("/api/v1/recruitment/exam-centers", params={"state": "Gujarat"}))

res = post("/api/v1/recruitment/apply", {
    "date_of_birth":  "2000-06-15",
    "gender":         "male",
    "blood_group":    "B+",
    "aadhaar_number": "123456789012",
    "height_cm":      172,
    "weight_kg":      65.5,
    "city":           "Ahmedabad",
    "state":          "Gujarat"
}, auth=True)
if res.status_code in (201, 200):
    print(f"{PASS} [{res.status_code}] POST /api/v1/recruitment/apply")
    candidate_id = res.json().get("id")
elif res.status_code == 400:
    print(f"{INFO} [{res.status_code}] POST /api/v1/recruitment/apply — already applied")
else:
    check("POST /api/v1/recruitment/apply", res, [201])

check("GET /api/v1/recruitment/status",     get("/api/v1/recruitment/status", auth=True))
check("GET /api/v1/recruitment/admit-card", get("/api/v1/recruitment/admit-card", auth=True), [200, 404])

# ─────────────────────────────────────────────────────────────────────────────
# [4] Soldier Service
# ─────────────────────────────────────────────────────────────────────────────
divider("[4] Soldier Service")
check("GET /api/v1/soldier/ (ping)",    get("/api/v1/soldier/"))
check("GET /api/v1/soldier/profile",    get("/api/v1/soldier/profile", auth=True), [200, 404])
check("GET /api/v1/soldier/battalions", get("/api/v1/soldier/battalions"))

res = post("/api/v1/soldier/battalions", {
    "battalion_name": "Alpha Battalion",
    "battalion_code": "ALPHA01",
    "location":       "Sabarmati Cantonment",
    "city":           "Ahmedabad",
    "state":          "Gujarat"
}, auth=True)
if res.status_code in (201, 200):
    print(f"{PASS} [{res.status_code}] POST /api/v1/soldier/battalions")
    battalion_id = res.json().get("id")
elif res.status_code == 400:
    print(f"{INFO} [{res.status_code}] POST /api/v1/soldier/battalions — already exists")
else:
    check("POST /api/v1/soldier/battalions", res, [201])

check("GET /api/v1/soldier/medical-records",  get("/api/v1/soldier/medical-records",  auth=True), [200, 404])
check("GET /api/v1/soldier/training-records", get("/api/v1/soldier/training-records", auth=True), [200, 404])
check("GET /api/v1/soldier/schedule",         get("/api/v1/soldier/schedule", auth=True, params={"date": today}), [200, 404])
check("GET /api/v1/soldier/stipends",         get("/api/v1/soldier/stipends",  auth=True), [200, 404])
check("GET /api/v1/soldier/rankings",         get("/api/v1/soldier/rankings"), [200, 404])
check("GET /api/v1/soldier/equipment",        get("/api/v1/soldier/equipment", auth=True), [200, 404])
check("GET /api/v1/soldier/events",           get("/api/v1/soldier/events",    auth=True), [200, 404])
check("GET /api/v1/soldier/sos/active",       get("/api/v1/soldier/sos/active"))

# ─────────────────────────────────────────────────────────────────────────────
# [5] Training Service
# ─────────────────────────────────────────────────────────────────────────────
divider("[5] Training Service")
check("GET /api/v1/training/ (ping)", get("/api/v1/training/"))
check("GET /api/v1/training/records", get("/api/v1/training/records", auth=True), [200, 404])

# ─────────────────────────────────────────────────────────────────────────────
# [6] Notification Service
# ─────────────────────────────────────────────────────────────────────────────
divider("[6] Notification Service")
check("GET /api/v1/notifications/ (ping)",    get("/api/v1/notifications/"))
check("GET /api/v1/notifications/sos/active", get("/api/v1/notifications/sos/active", auth=True))
check("GET /api/v1/notifications/sos/history",get("/api/v1/notifications/sos/history", auth=True))

# ─────────────────────────────────────────────────────────────────────────────
# [7] ML Service
# ─────────────────────────────────────────────────────────────────────────────
divider("[7] ML Service")
check("GET /api/v1/ml/ (ping)", get("/api/v1/ml/"))

check("POST /api/v1/ml/predict/performance", post("/api/v1/ml/predict/performance", {
    "running_time_minutes": 14.5,
    "pushups_count":        42,
    "pullups_count":        15,
    "endurance_score":      78.0,
    "shooting_accuracy":    85.5,
    "decision_score":       72.0
}, auth=True))

check("POST /api/v1/ml/predict/injury-risk", post("/api/v1/ml/predict/injury-risk", {
    "training_intensity": 7.5,
    "training_frequency": 5,
    "recovery_days":      2,
    "previous_injuries":  1,
    "sleep_hours":        7.0,
    "stress_level":       4.0
}, auth=True))

check("POST /api/v1/ml/analyze/trend", post("/api/v1/ml/analyze/trend", {
    "soldier_id": 1,
    "months":     3
}, auth=True), [200, 404])

check("POST /api/v1/ml/training/optimize",
      post("/api/v1/ml/training/optimize", auth=True, params={"soldier_id": 1}), [200, 404])

check("POST /api/v1/ml/medical/analyze",
      post("/api/v1/ml/medical/analyze", auth=True, params={"soldier_id": 1}), [200, 404])

# ─────────────────────────────────────────────────────────────────────────────
# [8] AI Service  (called AFTER login — token is ready)
# ─────────────────────────────────────────────────────────────────────────────
divider("[8] AI Service")
check("GET  /api/v1/ai/predict/status", get("/api/v1/ai/predict/status", auth=True))

check("POST /api/v1/ai/ask", post("/api/v1/ai/ask", {
    "query": "What is the Agnipath scheme?",
    "top_k": 3
}, auth=True))

check("POST /api/v1/ai/summarize", post("/api/v1/ai/summarize", {
    "text":       "The Agnipath scheme is a short-term military recruitment programme introduced by the Indian government in 2022 for recruiting soldiers into the armed forces for a period of four years.",
    "max_length": 60,
    "min_length": 20
}, auth=True))

check("POST /api/v1/ai/predict", post("/api/v1/ai/predict", {
    "age":           22,
    "bmi":           22.5,
    "pushups":       40,
    "pullups":       12,
    "run_time":      14.5,
    "training_days": 20
}, auth=True))

# ─────────────────────────────────────────────────────────────────────────────
# [9] Weather Service
# ─────────────────────────────────────────────────────────────────────────────
divider("[9] Weather Service")
check("GET /api/v1/weather/ (ping)",      get("/api/v1/weather/"))
check("GET /api/v1/weather/current",      get("/api/v1/weather/current",  auth=True, params={"location": "Ahmedabad"}))
check("GET /api/v1/weather/forecast",     get("/api/v1/weather/forecast", auth=True, params={"location": "Ahmedabad", "days": 3}))
check("POST /api/v1/weather/recommendation",
      post("/api/v1/weather/recommendation", auth=True, params={"location": "Ahmedabad"}))

# ─────────────────────────────────────────────────────────────────────────────
# [10] Reports Service
# ─────────────────────────────────────────────────────────────────────────────
divider("[10] Reports Service")
check("GET /api/v1/reports/ (ping)", get("/api/v1/reports/"))
sid = soldier_id or 1
check("GET daily report",   get(f"/api/v1/reports/soldier/{sid}/daily",
      auth=True, params={"report_date": today}), [200, 404])
check("GET monthly report", get(f"/api/v1/reports/soldier/{sid}/monthly",
      auth=True, params={"month": date.today().month, "year": date.today().year}), [200, 404])
check("GET medical report", get(f"/api/v1/reports/soldier/{sid}/medical", auth=True), [200, 404])
check("GET stipend report", get(f"/api/v1/reports/soldier/{sid}/stipend",
      auth=True, params={"year": date.today().year}), [200, 404])

# ─────────────────────────────────────────────────────────────────────────────
# [11] Logout (always last)
# ─────────────────────────────────────────────────────────────────────────────
divider("[11] Cleanup")
check("POST /api/v1/auth/logout", post("/api/v1/auth/logout", auth=True))

print(f"\n{'─'*55}")
print("  All tests complete.")
print(f"{'─'*55}\n")