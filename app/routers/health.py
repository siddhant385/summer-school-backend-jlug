# app/routers/health.py
from fastapi import APIRouter
from app.core.config import settings
from app.core.logger import setup_logger
from datetime import datetime
from zoneinfo import ZoneInfo

router = APIRouter(prefix="/health", tags=["Health Check"])
log = setup_logger(__name__)

IST = ZoneInfo("Asia/Kolkata")

@router.get("/")
def health_check():
    """
    Health check endpoint to verify API is running
    
    Returns:
    - API status
    - Current server time in IST
    - Application info
    """
    current_time = datetime.now(IST)
    
    return {
        "status": "healthy",
        "message": f"🚀 {settings.APP_NAME} is running successfully!",
        "app_name": settings.APP_NAME,
        "debug_mode": settings.DEBUG,
        "current_time_ist": current_time.strftime("%d %B %Y, %I:%M:%S %p IST"),
        "timezone": "Asia/Kolkata",
        "api_version": "v1",
        "endpoints": {
            "auth": "/api/v1/auth",
            "workshops": "/api/v1/workshops", 
            "health": "/api/v1/health",
            "docs": "/docs",
            "redoc": "/redoc"
        }
    }

@router.get("/status")
def detailed_status():
    """
    Detailed system status check
    
    Returns comprehensive system information
    """
    current_time = datetime.now(IST)
    
    return {
        "system_status": "operational",
        "uptime_info": "Server is running",
        "server_time": {
            "ist": current_time.strftime("%d %B %Y, %I:%M:%S %p IST"),
            "utc": datetime.utcnow().strftime("%d %B %Y, %I:%M:%S %p UTC"),
            "timestamp": current_time.timestamp()
        },
        "application": {
            "name": settings.APP_NAME,
            "debug": settings.DEBUG,
            "version": "1.0.0"
        },
        "features": {
            "authentication": "✅ Active",
            "workshops": "✅ Active", 
            "cors": "✅ Configured",
            "logging": "✅ Active"
        },
        "environment": "development" if settings.DEBUG else "production"
    }
