# app/routers/assignments.py
from fastapi import APIRouter
from app.core.logger import setup_logger

log = setup_logger(__name__)
router = APIRouter(prefix="/assignments", tags=["assignments"])

# TODO: Implement assignment-related endpoints
