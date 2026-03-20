"""Live API smoke test for Agniveer backend.

Run this after starting the API server:
    uvicorn main:app --reload
Then:
    python test_agniveer.py
"""

from __future__ import annotations

import os
import sys
import time
from datetime import datetime, timezone

import requests


BASE_URL = os.getenv("AGNIVEER_BASE_URL", "http://127.0.0.1:8000")
TIMEOUT = 15
STARTUP_WAIT_SECONDS = 90


def _print_ok(message: str) -> None:
    print(f"[OK] {message}")


def _print_fail(message: str) -> None:
    print(f"[FAIL] {message}")


def _unwrap(json_data: dict) -> dict:
    if isinstance(json_data, dict) and {"success", "data", "message"}.issubset(json_data.keys()):
        return json_data["data"] or {}
    return json_data


def _request(method: str, path: str, **kwargs) -> requests.Response:
    return requests.request(method, f"{BASE_URL}{path}", timeout=TIMEOUT, **kwargs)


def _expect_status(resp: requests.Response, allowed: set[int], label: str) -> bool:
    if resp.status_code not in allowed:
        _print_fail(f"{label} -> {resp.status_code} {resp.text[:300]}")
        return False
    _print_ok(f"{label} -> {resp.status_code}")
    return True


def main() -> int:
    timestamp = int(datetime.now(timezone.utc).timestamp())
    test_user = {
        "email": f"smoke{timestamp}@example.com",
        "username": f"smoke{timestamp}",
        "full_name": "Smoke Test User",
        "password": "SmokePass@123",
        "role": "candidate",
    }

    # Health checks (wait for startup readiness)
    started = False
    deadline = time.time() + STARTUP_WAIT_SECONDS
    while time.time() < deadline:
        try:
            r = _request("GET", "/health")
            if r.status_code == 200:
                started = True
                break
        except requests.RequestException:
            pass
        time.sleep(2)

    if not started:
        _print_fail(f"server not ready within {STARTUP_WAIT_SECONDS}s at {BASE_URL}")
        return 1
    _print_ok("GET /health -> 200")

    r = _request("GET", "/api/v1/auth/health")
    if not _expect_status(r, {200}, "GET /api/v1/auth/health"):
        return 1

    # Register (idempotent-friendly)
    r = _request("POST", "/api/v1/auth/register", json=test_user)
    if not _expect_status(r, {201, 400}, "POST /api/v1/auth/register"):
        return 1

    # Login
    r = _request(
        "POST",
        "/api/v1/auth/login",
        data={
            "username": test_user["username"],
            "password": test_user["password"],
            "grant_type": "password",
        },
    )
    if not _expect_status(r, {200}, "POST /api/v1/auth/login"):
        return 1
    tokens = _unwrap(r.json())
    access_token = tokens.get("access_token")
    refresh_token = tokens.get("refresh_token")
    if not access_token or not refresh_token:
        _print_fail("login response missing tokens")
        return 1
    _print_ok("access and refresh tokens issued")

    # Me
    headers = {"Authorization": f"Bearer {access_token}"}
    r = _request("GET", "/api/v1/auth/me", headers=headers)
    if not _expect_status(r, {200}, "GET /api/v1/auth/me"):
        return 1

    # Refresh
    r = _request("POST", "/api/v1/auth/refresh", json={"refresh_token": refresh_token})
    if not _expect_status(r, {200}, "POST /api/v1/auth/refresh"):
        return 1
    refreshed = _unwrap(r.json())
    if refreshed.get("token_type") != "bearer":
        _print_fail("refresh response missing token_type=bearer")
        return 1
    _print_ok("refresh token exchange succeeded")

    # Logout + revoke
    r = _request(
        "POST",
        "/api/v1/auth/logout",
        headers=headers,
        json={"refresh_token": refresh_token},
    )
    if not _expect_status(r, {200}, "POST /api/v1/auth/logout"):
        return 1

    r = _request("POST", "/api/v1/auth/refresh", json={"refresh_token": refresh_token})
    if not _expect_status(r, {401}, "POST /api/v1/auth/refresh after logout"):
        return 1

    _print_ok("all smoke checks passed")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except requests.RequestException as exc:
        _print_fail(f"request failed: {exc}")
        _print_fail("start server first: uvicorn main:app --reload")
        raise SystemExit(1)
