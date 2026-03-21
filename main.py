"""Root ASGI entrypoint that proxies to backend/main.py."""

from pathlib import Path
import sys
import os

# Bypass slow Paddle ML model hoster connectivity checks on startup
os.environ["PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK"] = "True"

BACKEND_DIR = Path(__file__).resolve().parent / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from backend.main import OPENAPI_REQUIRED_PREFIXES, app
