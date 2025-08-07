# app/services/certificate.py
from app.core.logger import setup_logger
from app.core.db import get_db
from app.schemas.certificate import (
    Certificate, CertificateResponse, CertificateListResponse
)
from app.schemas.response import ResponseModel
from uuid import UUID
from typing import List, Optional
from fastapi.concurrency import run_in_threadpool
from fastapi import HTTPException, status
from supabase import Client

log = setup_logger(__name__)

class CertificateService:
    """Service for certificate read operations only"""
    
    @staticmethod
    async def get_user_certificates(user_id: UUID) -> ResponseModel[CertificateListResponse]:
        """Get all certificates for a specific user"""
        try:
            db = get_db()
            
            log.debug(f"Fetching certificates for user: {user_id}")
            
            # Get certificates with workshop info for better UX
            result = await run_in_threadpool(
                lambda: db.table("certificates").select("""
                    id,
                    created_at,
                    user_id,
                    workshop_id,
                    certificate_url,
                    workshops:workshop_id (
                        title,
                        conducted_by
                    )
                """).eq("user_id", str(user_id)).order("created_at", desc=True).execute()
            )
            
            if not result.data:
                return ResponseModel(
                    success=True,
                    message="No certificates found for this user",
                    data=CertificateListResponse(
                        certificates=[],
                        total_count=0,
                        user_id=user_id
                    )
                )
            
            # Convert to Certificate objects with workshop info
            certificates = []
            for cert_data in result.data:
                workshop_info = cert_data.get("workshops", {})
                
                certificate = Certificate(
                    id=cert_data["id"],
                    created_at=cert_data["created_at"],
                    user_id=UUID(cert_data["user_id"]),
                    workshop_id=UUID(cert_data["workshop_id"]),
                    certificate_url=cert_data.get("certificate_url"),
                    workshop_title=workshop_info.get("title") if workshop_info else None,
                    workshop_conducted_by=workshop_info.get("conducted_by") if workshop_info else None
                )
                certificates.append(certificate)
            
            log.info(f"Found {len(certificates)} certificates for user {user_id}")
            
            response_data = CertificateListResponse(
                certificates=certificates,
                total_count=len(certificates),
                user_id=user_id
            )
            
            return ResponseModel(
                success=True,
                message=f"Found {len(certificates)} certificates",
                data=response_data
            )
            
        except Exception as e:
            log.error(f"Error fetching certificates for user {user_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to fetch user certificates"
            )
    
    @staticmethod
    async def get_certificate_by_id(certificate_id: int, user_id: UUID) -> ResponseModel[CertificateResponse]:
        """Get specific certificate by ID (user can only view their own)"""
        try:
            db = get_db()
            
            log.debug(f"Fetching certificate {certificate_id} for user {user_id}")
            
            # Get certificate with workshop info
            result = await run_in_threadpool(
                lambda: db.table("certificates").select("""
                    id,
                    created_at,
                    user_id,
                    workshop_id,
                    certificate_url,
                    workshops:workshop_id (
                        title,
                        conducted_by
                    )
                """).eq("id", certificate_id).eq("user_id", str(user_id)).execute()
            )
            
            if not result.data or len(result.data) == 0:
                return ResponseModel(
                    success=False,
                    message="Certificate not found or access denied",
                    data=None
                )
            
            cert_data = result.data[0]  # Get first result
            workshop_info = cert_data.get("workshops", {})
            
            certificate = Certificate(
                id=cert_data["id"],
                created_at=cert_data["created_at"],
                user_id=UUID(cert_data["user_id"]),
                workshop_id=UUID(cert_data["workshop_id"]),
                certificate_url=cert_data.get("certificate_url"),
                workshop_title=workshop_info.get("title") if workshop_info else None,
                workshop_conducted_by=workshop_info.get("conducted_by") if workshop_info else None
            )
            
            log.info(f"Certificate {certificate_id} found for user {user_id}")
            
            response_data = CertificateResponse(
                certificate=certificate
            )
            
            return ResponseModel(
                success=True,
                message="Certificate retrieved successfully",
                data=response_data
            )
            
        except Exception as e:
            log.error(f"Error fetching certificate {certificate_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to fetch certificate"
            )
    
    @staticmethod
    async def check_user_certificate_for_workshop(user_id: UUID, workshop_id: UUID) -> ResponseModel[CertificateResponse]:
        """Check if user has certificate for specific workshop"""
        try:
            db = get_db()
            
            log.debug(f"Checking certificate for user {user_id} in workshop {workshop_id}")
            
            # Get certificate for specific workshop
            result = await run_in_threadpool(
                lambda: db.table("certificates").select("""
                    id,
                    created_at,
                    user_id,
                    workshop_id,
                    certificate_url,
                    workshops:workshop_id (
                        title,
                        conducted_by
                    )
                """).eq("user_id", str(user_id)).eq("workshop_id", str(workshop_id)).execute()
            )
            
            if not result.data or len(result.data) == 0:
                return ResponseModel(
                    success=False,
                    message="No certificate found for this workshop",
                    data=None
                )
            
            cert_data = result.data[0]  # Get first result
            workshop_info = cert_data.get("workshops", {})
            
            certificate = Certificate(
                id=cert_data["id"],
                created_at=cert_data["created_at"],
                user_id=UUID(cert_data["user_id"]),
                workshop_id=UUID(cert_data["workshop_id"]),
                certificate_url=cert_data.get("certificate_url"),
                workshop_title=workshop_info.get("title") if workshop_info else None,
                workshop_conducted_by=workshop_info.get("conducted_by") if workshop_info else None
            )
            
            log.info(f"Certificate found for user {user_id} in workshop {workshop_id}")
            
            response_data = CertificateResponse(
                certificate=certificate,
                message="Certificate found for this workshop"
            )
            
            return ResponseModel(
                success=True,
                message="Certificate found for this workshop",
                data=response_data
            )
            
        except Exception as e:
            log.error(f"Error checking certificate for user {user_id} in workshop {workshop_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to check workshop certificate"
            )
    
    @staticmethod
    async def verify_certificate_public(certificate_id: int) -> ResponseModel[CertificateResponse]:
        """Public certificate verification (no user restrictions)"""
        try:
            db = get_db()
            
            log.debug(f"Public verification for certificate: {certificate_id}")
            
            # Get certificate with workshop info but hide user details
            result = await run_in_threadpool(
                lambda: db.table("certificates").select("""
                    id,
                    created_at,
                    workshop_id,
                    certificate_url,
                    workshops:workshop_id (
                        title,
                        conducted_by
                    )
                """).eq("id", certificate_id).execute()
            )
            
            if not result.data or len(result.data) == 0:
                return ResponseModel(
                    success=False,
                    message="Certificate not found or invalid",
                    data=None
                )
            
            cert_data = result.data[0]  # Get first result
            workshop_info = cert_data.get("workshops", {})
            
            # Create certificate with hidden user_id for privacy
            certificate = Certificate(
                id=cert_data["id"],
                created_at=cert_data["created_at"],
                user_id=UUID("00000000-0000-0000-0000-000000000000"),  # Hidden for privacy
                workshop_id=UUID(cert_data["workshop_id"]),
                certificate_url=cert_data.get("certificate_url"),
                workshop_title=workshop_info.get("title") if workshop_info else None,
                workshop_conducted_by=workshop_info.get("conducted_by") if workshop_info else None
            )
            
            log.info(f"Certificate {certificate_id} verified publicly")
            
            response_data = CertificateResponse(
                certificate=certificate,
                message="Certificate verified successfully"
            )
            
            return ResponseModel(
                success=True,
                message="Certificate is valid and verified",
                data=response_data
            )
            
        except Exception as e:
            log.error(f"Error in public certificate verification {certificate_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to verify certificate"
            )
