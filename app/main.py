# app/main.py

from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from .core.config import settings
from .core.logger import setup_logger
from .routers import auth, users, workshops, assignments, certificates, reviews
# from .middlewares.request_logger import RequestLoggerMiddleware # Example import

# --- Logger Setup ---
log = setup_logger(__name__)

# --- FastAPI App Instance Creation ---
app = FastAPI(
    title=settings.APP_NAME,
    debug=settings.DEBUG,
    # Add other metadata like version, description etc.
)

# --- CORS Middleware Setup ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Middleware Setup ---
# app.add_middleware(RequestLoggerMiddleware)


# --- Router Aggregation ---
# This router will include all your API routes
api_router = APIRouter()

api_router.include_router(auth.router, tags=["Authentication"])
# api_router.include_router(users.router, prefix="/users", tags=["Users"])
# api_router.include_router(workshops.router, prefix="/workshops", tags=["Workshops"])
# api_router.include_router(assignments.router, prefix="/assignments", tags=["Assignments"])
# api_router.include_router(certificates.router, prefix="/certificates", tags=["Certificates"])
# api_router.include_router(reviews.router, prefix="/reviews", tags=["Reviews"])
# ... include other routers here ...

# Include the main router in the FastAPI app
# All routes will be prefixed with /api/v1
app.include_router(api_router, prefix="/api/v1")


# --- Root Endpoint for Health Check ---
@app.get("/", tags=["Health Check"])
def read_root():
    """A simple root endpoint to confirm the app is running."""
    return {"status": "OK", "message": f"Welcome to {settings.APP_NAME}"}

log.info("Application setup complete.")