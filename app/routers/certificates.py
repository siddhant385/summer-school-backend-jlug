# app/routers/certificates.py
from fastapi import APIRouter, Depends, HTTPException, status
from uuid import UUID

from app.core.logger import setup_logger
from app.services.certificate import CertificateService
from app.schemas.certificate import CertificateResponse, CertificateListResponse
from app.schemas.response import ResponseModel
from app.schemas.user import User
from app.dependencies.auth import verify_valid_token
from app.dependencies.user_workshop import get_current_registered_user

log = setup_logger(__name__)
router = APIRouter(prefix="/certificates", tags=["Certificates"])

# 📜 Route 1: Get My Certificates
@router.get("/me", response_model=ResponseModel[CertificateListResponse])
async def get_my_certificates(
    current_user: User = Depends(get_current_registered_user)
):
    """
    Get all certificates for current user
    - Requires authentication
    - Returns user's certificates with workshop details
    - Ordered by latest first
    """
    try:
        log.info(f"User {current_user.email} requesting their certificates")
        
        result = await CertificateService.get_user_certificates(current_user.id)
        
        if not result.success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.message
            )
        
        log.info(f"Found {result.data.total_count} certificates for user {current_user.email}")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        log.exception(f"Error fetching certificates for user")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch your certificates"
        )

# 🎯 Route 2: Get Specific Certificate
@router.get("/{certificate_id}", response_model=ResponseModel[CertificateResponse])
async def get_certificate_by_id(
    certificate_id: int,
    current_user: User = Depends(get_current_registered_user)
):
    """
    Get specific certificate by ID
    - Requires authentication
    - Users can only view their own certificates
    - Returns certificate with workshop details
    """
    try:
        log.info(f"User {current_user.email} requesting certificate {certificate_id}")
        
        if certificate_id <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid certificate ID"
            )
        
        result = await CertificateService.get_certificate_by_id(certificate_id, current_user.id)
        
        if not result.success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=result.message
            )
        
        log.info(f"Certificate {certificate_id} retrieved for user {current_user.email}")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        log.exception(f"Error fetching certificate")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch certificate"
        )

# 🏢 Route 3: Check Certificate for Workshop
@router.get("/workshop/{workshop_id}", response_model=ResponseModel[CertificateResponse])
async def get_my_certificate_for_workshop(
    workshop_id: UUID,
    current_user: User = Depends(get_current_registered_user)
):
    """
    Check if current user has certificate for specific workshop
    - Requires authentication
    - Returns certificate if exists for the workshop
    - Useful for checking workshop completion status
    """
    try:
        log.info(f"User {current_user.email} checking certificate for workshop {workshop_id}")
        
        result = await CertificateService.check_user_certificate_for_workshop(
            current_user.id, workshop_id
        )
        
        if not result.success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=result.message
            )
        
        log.info(f"Certificate found for user {current_user.email} in workshop {workshop_id}")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        log.exception(f"Error checking workshop certificate")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to check workshop certificate"
        )

# 👤 Route 4: Verify Certificate (Public - No Auth Required)
@router.get("/verify/{certificate_id}", response_model=ResponseModel[CertificateResponse])
async def verify_certificate_public(
    certificate_id: int
):
    """
    Public certificate verification
    - No authentication required
    - Anyone can verify certificate authenticity
    - Returns basic certificate info for verification
    """
    try:
        log.info(f"Public verification request for certificate {certificate_id}")
        
        if certificate_id <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid certificate ID"
            )
        
        result = await CertificateService.verify_certificate_public(certificate_id)
        
        if not result.success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=result.message
            )
        
        log.info(f"Certificate {certificate_id} verified publicly")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        log.exception(f"Error verifying certificate")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to verify certificate"
        )
