# app/routers/reviews.py
from fastapi import APIRouter
from app.core.logger import setup_logger

log = setup_logger(__name__)
router = APIRouter(prefix="/reviews", tags=["reviews"])

# TODO: Implement review-related endpoints
