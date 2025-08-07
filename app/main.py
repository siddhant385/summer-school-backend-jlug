# app/main.py

from fastapi import FastAPI, APIRouter
from .core.config import settings
from .core.logger import setup_logger
from .middlewares.cors import setup_cors_middleware
from .routers import auth, users, workshops, assignments, certificates, reviews, health, user_workshop, leaderboard, notificationRouter
# from .middlewares.request_logger import RequestLoggerMiddleware # Example import

# --- Logger Setup ---
log = setup_logger(__name__)

# --- FastAPI App Instance Creation ---
app = FastAPI(
    title=settings.APP_NAME,
    debug=settings.DEBUG,
    description="🎓 Summer School Backend API for JLUG - Workshop Management System",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# --- Middleware Setup ---
setup_cors_middleware(app)
# app.add_middleware(RequestLoggerMiddleware)  # Add custom middlewares here


# --- Router Aggregation ---
# This router will include all your API routes
api_router = APIRouter()

# Include all routers with proper organization
api_router.include_router(auth.router, tags=["Authentication"])
api_router.include_router(users.router, tags=["Users"])  # ✅ Enabled users router
api_router.include_router(workshops.router, tags=["Workshops"])
api_router.include_router(user_workshop.router, tags=["Workshop Registration"])
api_router.include_router(assignments.router, tags=["Assignments"])  # ✅ Enabled assignments router
api_router.include_router(certificates.router, tags=["Certificates"])  # ✅ Enabled certificates router
api_router.include_router(leaderboard.router, tags=["Leaderboard"])  # ✅ Enabled leaderboard router
api_router.include_router(reviews.router, tags=["Reviews"])  # ✅ Enabled reviews router
api_router.include_router(notificationRouter.router, tags=["Notifications"])  # ✅ Enabled notification router
api_router.include_router(health.router, tags=["Health Check"])

# Future routers (uncomment when ready)
# api_router.include_router(certificates.router, prefix="/certificates", tags=["Certificates"])

# Include the main router in the FastAPI app
# All routes will be prefixed with /api/v1
app.include_router(api_router, prefix="/api/v1")


# --- Root Endpoint ---
@app.get("/", tags=["Root"])
def read_root():
    """
    🏠 Welcome endpoint with comprehensive API information
    
    Returns:
    - Welcome message with app details
    - Available API endpoints
    - Quick start guide
    - System status
    """
    from datetime import datetime
    from zoneinfo import ZoneInfo
    
    current_time = datetime.now(ZoneInfo("Asia/Kolkata"))
    
    return {
        "message": f"🎓 Welcome to {settings.APP_NAME}!",
        "description": "Summer School Backend API for JLUG Workshop Management System",
        "status": "🟢 Online",
        "current_time_ist": current_time.strftime("%d %B %Y, %I:%M:%S %p IST"),
        "api_info": {
            "version": "v1",
            "base_url": "/api/v1",
            "documentation": "/docs",
            "alternative_docs": "/redoc"
        },
        "available_endpoints": {
            "🔐 Authentication": "/api/v1/auth",
            "👥 Users": "/api/v1/users",
            "🎪 Workshops": "/api/v1/workshops",
            "📝 Workshop Registration": "/api/v1/user-workshop",
            "📋 Assignments": "/api/v1/assignments",
            "🏆 Certificates": "/api/v1/certificates",
            "🏅 Leaderboard": "/api/v1/leaderboard",
            "⭐ Reviews": "/api/v1/reviews",
            "� Notifications": "/api/v1/notifications",
            "�💓 Health Check": "/api/v1/health",
            "📚 API Docs": "/docs"
        },
        "quick_start": {
            "1": "Visit /docs for interactive API documentation",
            "2": "Use /api/v1/auth/login for authentication",
            "3": "Check /api/v1/health for system status",
            "4": "Explore /api/v1/workshops for workshop management"
        },
        "features": [
            "🔑 JWT Authentication with Supabase", 
            "🎪 Workshop Management System",
            "📝 User Workshop Registration (Guest + Registered)",
            "📋 Assignment Submission & Grading System",
            "🏆 Certificate Management & Verification",
            "🏅 Points-based Leaderboard System",
            "🌏 Indian Timezone Support",
            "📊 Statistics & Analytics",
            "🔒 Admin Role-based Access",
            "⭐ Workshop Review System",
            "📧 Automated Email Notifications & Reminders"
        ]
    }

log.info("Application setup complete.")