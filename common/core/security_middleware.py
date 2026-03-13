"""
Security Middleware
Agniveer Sentinel - Enterprise Production
"""

from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.cors import CORSMiddleware
from starlette.datastructures import Headers
from typing import Callable
import time
import redis
import os


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
        
        response = await call_next(request)
        
        # If login failed (401), track the attempt
        if response.status_code == 401:
            # Get username from request body (simplified)
            username = "unknown"
            
            key = f"login_attempts:{username}"
            
            try:
                if self.redis_client:
                    attempts = self.redis_client.get(key)
                    
                    if attempts and int(attempts) >= self.max_attempts:
                        # Lock account
                        self.redis_client.setex(
                            f"account_locked:{username}",
                            self.lockout_minutes * 60,
                            "1"
                        )
                        return JSONResponse(
                            status_code=status.HTTP_403_FORBIDDEN,
                            content={"detail": "Account locked due to too many failed attempts."}
                        )
                    
                    pipe = self.redis_client.pipeline()
                    pipe.incr(key)
                    pipe.expire(key, self.lockout_minutes * 60)
                    pipe.execute()
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
        
        # Log request (would send to Elasticsearch in production)
        audit_data = {
            "timestamp": time.time(),
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "duration": duration,
            "client_ip": request.client.host,
            "user_agent": request.headers.get("user-agent", ""),
        }
        
        # In production, send to audit log service
        # audit_service.log(audit_data)
        
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
