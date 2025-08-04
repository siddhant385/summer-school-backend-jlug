# app/routers/users.py
from fastapi import APIRouter
from app.core.logger import setup_logger

log = setup_logger(__name__)
router = APIRouter(prefix="/users", tags=["users"])

# TODO: Implement user-related endpoints
