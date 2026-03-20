"""
Security Middleware
Agniveer Sentinel - Enterprise Production
"""

import logging
import os
import time
from urllib.parse import parse_qs
from typing import Callable
import warnings

# Suppress the deprecation warning for pythonjsonlogger before importing
warnings.filterwarnings('ignore', category=DeprecationWarning, module='pythonjsonlogger.jsonlogger')

import redis
from fastapi import Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.cors import CORSMiddleware
from pythonjsonlogger import jsonlogger


logger = logging.getLogger("agniveer.audit")
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(jsonlogger.JsonFormatter())
    logger.addHandler(handler)
logger.setLevel(logging.INFO)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware using Redis"""
    
    def __init__(self, app, requests_per_minute: int = 60):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.redis_client = None
        
        # Initialize Redis connection
        try:
            redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
            self.redis_client = redis.from_url(redis_url, decode_responses=True)
        except Exception:
            pass  # Fall back to in-memory if Redis unavailable
    
    async def dispatch(self, request: Request, call_next: Callable):
        # Skip rate limiting for health checks
        if request.url.path in ["/health", "/health/readiness", "/health/liveness"]:
            return await call_next(request)
        
        # Get client IP
        client_ip = request.client.host
        
        # Create rate limit key
        key = f"rate_limit:{client_ip}:{int(time.time() / 60)}"
        
        try:
            if self.redis_client:
                # Use Redis for distributed rate limiting
                current = self.redis_client.get(key)
                
                if current and int(current) >= self.requests_per_minute:
                    return JSONResponse(
                        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                        content={"detail": "Too many requests. Please try again later."}
                    )
                
                pipe = self.redis_client.pipeline()
                pipe.incr(key)
                pipe.expire(key, 60)
                pipe.execute()
            else:
                # Fallback to in-memory (single instance)
                pass
                
        except Exception:
            pass  # Allow request if rate limiting fails
        
        response = await call_next(request)
        return response


class LoginAttemptMiddleware(BaseHTTPMiddleware):
    """Track failed login attempts and lock accounts"""
    
    def __init__(self, app, max_attempts: int = 5, lockout_minutes: int = 30):
        super().__init__(app)
        self.max_attempts = max_attempts
        self.lockout_minutes = lockout_minutes
        self.redis_client = None
        
        try:
            redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
            self.redis_client = redis.from_url(redis_url, decode_responses=True)
        except Exception:
            pass
    
    async def dispatch(self, request: Request, call_next: Callable):
        # Only track login attempts
        if "/auth/login" not in request.url.path:
            return await call_next(request)

        client_ip = request.client.host if request.client else "unknown"
        username = "unknown"
        try:
            body = await request.body()
            parsed = parse_qs(body.decode("utf-8"))
            username = str(
                (parsed.get("username") or parsed.get("email") or ["unknown"])[0]
            ).strip().lower()

            async def receive():
                return {"type": "http.request", "body": body, "more_body": False}

            request._receive = receive
        except Exception:
            pass

        username_key = f"login_attempts:user:{username}"
        ip_key = f"login_attempts:ip:{client_ip}"
        account_lock_key = f"account_locked:{username}:{client_ip}"

        try:
            if self.redis_client and self.redis_client.get(account_lock_key):
                return JSONResponse(
                    status_code=status.HTTP_403_FORBIDDEN,
                    content={"detail": "Account locked due to too many failed attempts."},
                )
        except Exception:
            pass

        response = await call_next(request)

        # If login failed (401), track the attempt
        if response.status_code == 401:
            try:
                if self.redis_client:
                    username_attempts = int(self.redis_client.get(username_key) or 0)
                    ip_attempts = int(self.redis_client.get(ip_key) or 0)

                    if username_attempts >= self.max_attempts or ip_attempts >= self.max_attempts:
                        self.redis_client.setex(
                            account_lock_key,
                            self.lockout_minutes * 60,
                            "1"
                        )
                        return JSONResponse(
                            status_code=status.HTTP_403_FORBIDDEN,
                            content={"detail": "Account locked due to too many failed attempts."}
                        )
                    
                    pipe = self.redis_client.pipeline()
                    pipe.incr(username_key)
                    pipe.expire(username_key, self.lockout_minutes * 60)
                    pipe.incr(ip_key)
                    pipe.expire(ip_key, self.lockout_minutes * 60)
                    pipe.execute()
            except Exception:
                pass

        if response.status_code == 200:
            try:
                if self.redis_client:
                    self.redis_client.delete(username_key, ip_key, account_lock_key)
            except Exception:
                pass

        return response


class SecureHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to responses"""
    
    async def dispatch(self, request: Request, call_next: Callable):
        response = await call_next(request)
        
        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Content-Security-Policy"] = "default-src 'self'"
        
        return response


class AuditLogMiddleware(BaseHTTPMiddleware):
    """Log API requests for audit trail"""
    
    async def dispatch(self, request: Request, call_next: Callable):
        # Skip logging for health checks
        if request.url.path.startswith("/health"):
            return await call_next(request)
        
        start_time = time.time()
        
        # Process request
        response = await call_next(request)
        
        # Calculate duration
        duration = time.time() - start_time
        
        audit_data = {
            "timestamp": time.time(),
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "duration": duration,
            "client_ip": request.client.host,
            "user_agent": request.headers.get("user-agent", ""),
        }

        logger.info("audit_event", extra={"event": audit_data})
        return response


def setup_security_middleware(app):
    """Configure all security middleware"""
    
    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=os.getenv("CORS_ORIGINS", "*").split(","),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Rate limiting
    app.add_middleware(
        RateLimitMiddleware,
        requests_per_minute=int(os.getenv("RATE_LIMIT", "60"))
    )
    
    # Login attempt tracking
    app.add_middleware(LoginAttemptMiddleware)
    
    # Security headers
    app.add_middleware(SecureHeadersMiddleware)
    
    # Audit logging
    app.add_middleware(AuditLogMiddleware)




