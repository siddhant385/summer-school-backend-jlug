# app/middlewares/cors.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.logger import setup_logger

log = setup_logger(__name__)

def setup_cors_middleware(app: FastAPI):
    """Setup CORS middleware for the FastAPI application"""
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:8080",
            "http://localhost:3000", 
            "http://127.0.0.1:8080",
            "http://127.0.0.1:3000",
            "https://*.app.github.dev",  # For GitHub Codespaces
            "https://*.github.dev",      # For GitHub Codespaces
            "*"  # Allow all origins in development (remove in production)
        ],
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
        allow_headers=[
            "Authorization",
            "Content-Type", 
            "Accept",
            "Origin",
            "X-Requested-With",
            "Access-Control-Allow-Headers",
            "Access-Control-Allow-Origin"
        ],
    )
    
    log.debug("✅ CORS middleware configured for development environment")
