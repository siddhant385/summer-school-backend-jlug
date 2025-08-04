# app/middlewares/request_logger.py
import time
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.logger import setup_logger

log = setup_logger(__name__)

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to log HTTP requests and responses"""
    
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        # Log request
        log.debug(f"→ {request.method} {request.url.path} - {request.client.host if request.client else 'Unknown'}")
        
        response = await call_next(request)
        
        # Calculate processing time
        process_time = time.time() - start_time
        
        # Log response
        log.debug(f"← {response.status_code} {request.method} {request.url.path} - {process_time:.3f}s")
        
        # Add processing time header
        response.headers["X-Process-Time"] = str(process_time)
        
        return response

def setup_request_logging_middleware(app):
    """Setup request logging middleware"""
    app.add_middleware(RequestLoggingMiddleware)
    log.debug("✅ Request logging middleware configured")
