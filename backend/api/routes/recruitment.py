"""
Recruitment Endpoints
Agniveer Sentinel - Phase 1: Recruitment System
"""

from fastapi import APIRouter, Depends, HTTPException, Request, status, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, date
from typing import Optional
import uuid
import random
import string

from core.database import get_db
from core.audit import log_security_event
from core.authorization import admin_required
from core.security import get_current_user
from core.storage import storage
from models.base import UserRole, ApplicationStatus
from models.user import User
from models.recruitment import (
    Candidate, CandidateDocument, Application, ExamCenter, Exam,
    ExamRegistration, AdmitCard
)
from schemas.recruitment import (
    CandidateCreate, CandidateUpdate, CandidateResponse,
    ApplicationCreate, ApplicationResponse, ExamCenterResponse,
    ExamResponse, ExamRegistrationResponse, AdmitCardResponse,
    ApplicationStatusResponse, ApplicationVerificationRequest, DocumentUploadResponse
)
from services.recruitment_service.services.admit_card_service import (
    admit_card_generator,
    notification_service,
)


router = APIRouter()

@router.get("/")
async def recruitment_service_test():
    return {"message": "recruitment service working"}


@router.get("/health")
async def recruitment_health():
    return {"status": "healthy", "service": "recruitment"}


def generate_registration_id() -> str:
    """Generate unique registration ID"""
    timestamp = datetime.utcnow().strftime("%Y%m%d")
    random_str = ''.join(random.choices(string.digits, k=6))
    return f"AGN{timestamp}{random_str}"


# ==================== Candidate Endpoints ====================

@router.post("/apply", response_model=CandidateResponse, status_code=status.HTTP_201_CREATED)
async def create_application(
    candidate_data: CandidateCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create new recruitment application"""
    # Check if user already has an application
    result = await db.execute(select(Candidate).where(Candidate.user_id == current_user.id))
    existing = result.scalar_one_or_none()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Application already exists"
        )
    
    # Create candidate
    candidate = Candidate(
        user_id=current_user.id,
        registration_id=generate_registration_id(),
        date_of_birth=candidate_data.date_of_birth,
        gender=candidate_data.gender,
        blood_group=candidate_data.blood_group,
        aadhaar_number=candidate_data.aadhaar_number,
        pan_number=candidate_data.pan_number,
        address=candidate_data.address,
        city=candidate_data.city,
        state=candidate_data.state,
        pincode=candidate_data.pincode,
        father_name=candidate_data.father_name,
        mother_name=candidate_data.mother_name,
        emergency_contact_name=candidate_data.emergency_contact_name,
        emergency_contact_phone=candidate_data.emergency_contact_phone,
        education_qualification=candidate_data.education_qualification,
        passing_year=candidate_data.passing_year,
        marks_percentage=candidate_data.marks_percentage,
        height_cm=candidate_data.height_cm,
        weight_kg=candidate_data.weight_kg,
        chest_cm=candidate_data.chest_cm,
    )
    
    db.add(candidate)
    await db.flush()
    
    # Update user role to candidate
    current_user.role = UserRole.CANDIDATE
    
    await db.commit()
    await db.refresh(candidate)
    
    return candidate


@router.get("/status", response_model=ApplicationStatusResponse)
async def get_application_status(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get application status"""
    result = await db.execute(select(Candidate).where(Candidate.user_id == current_user.id))
    candidate = result.scalar_one_or_none()
    
    if not candidate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found"
        )
    
    # Get admit card
    admit_card = None
    if candidate.admit_card:
        admit_card = candidate.admit_card
    
    # Get exam registration
    exam_registration = None
    if candidate.admit_card and candidate.admit_card.exam_registration:
        exam_registration = candidate.admit_card.exam_registration
    
    return ApplicationStatusResponse(
        registration_id=candidate.registration_id,
        application_status=candidate.application_status,
        admit_card=admit_card,
        exam_registration=exam_registration
    )


@router.put("/profile", response_model=CandidateResponse)
async def update_candidate(
    candidate_data: CandidateUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update candidate information"""
    result = await db.execute(select(Candidate).where(Candidate.user_id == current_user.id))
    candidate = result.scalar_one_or_none()
    
    if not candidate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found"
        )
    
    # Update fields
    for field, value in candidate_data.model_dump(exclude_unset=True).items():
        setattr(candidate, field, value)
    
    await db.commit()
    await db.refresh(candidate)
    
    return candidate


@router.post("/documents", status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    document_type: str = Form(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Upload candidate documents"""
    # Get candidate
    result = await db.execute(select(Candidate).where(Candidate.user_id == current_user.id))
    candidate = result.scalar_one_or_none()
    
    if not candidate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found"
        )
    
    file_content = await file.read()
    object_key = f"recruitment/{candidate.registration_id}/{document_type}_{uuid.uuid4()}_{file.filename}"
    object_uri = storage.upload_bytes(object_key, file_content, file.content_type or "application/octet-stream")
    
    # Create document record
    document = CandidateDocument(
        candidate_id=candidate.id,
        document_type=document_type,
        file_url=object_uri,
        file_name=file.filename,
        file_size=len(file_content),
        mime_type=file.content_type
    )
    
    db.add(document)
    await db.flush()
    await db.commit()
    
    return DocumentUploadResponse(
        document_id=document.id,
        document_type=document_type,
        file_url=storage.generate_presigned_url(object_uri),
        file_name=file.filename
    )


# ==================== Exam Center Endpoints ====================

@router.get("/exam-centers", response_model=list[ExamCenterResponse])
async def list_exam_centers(
    city: Optional[str] = None,
    state: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """List available exam centers"""
    query = select(ExamCenter).where(ExamCenter.is_active == True)
    
    if city:
        query = query.where(ExamCenter.city == city)
    if state:
        query = query.where(ExamCenter.state == state)
    
    result = await db.execute(query)
    return result.scalars().all()


# ==================== Exam Endpoints ====================

@router.get("/exams", response_model=list[ExamResponse])
async def list_exams(
    db: AsyncSession = Depends(get_db)
):
    """List available exams"""
    result = await db.execute(
        select(Exam).where(Exam.is_published == True)
    )
    return result.scalars().all()


@router.get("/exams/{exam_id}", response_model=ExamResponse)
async def get_exam(
    exam_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get exam details"""
    result = await db.execute(select(Exam).where(Exam.id == exam_id))
    exam = result.scalar_one_or_none()
    
    if not exam:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Exam not found"
        )
    
    return exam


@router.post("/exams/register", response_model=ExamRegistrationResponse)
async def register_for_exam(
    exam_id: int,
    exam_center_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Register for an exam"""
    # Get candidate
    result = await db.execute(select(Candidate).where(Candidate.user_id == current_user.id))
    candidate = result.scalar_one_or_none()
    
    if not candidate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found"
        )
    
    # Check if already registered
    existing = await db.execute(
        select(ExamRegistration).where(
            ExamRegistration.candidate_id == candidate.id,
            ExamRegistration.exam_id == exam_id
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Already registered for this exam"
        )
    
    # Check exam center availability
    result = await db.execute(select(ExamCenter).where(ExamCenter.id == exam_center_id))
    exam_center = result.scalar_one_or_none()
    
    if not exam_center:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Exam center not found"
        )
    
    if exam_center.current_booked >= exam_center.capacity:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Exam center is full"
        )
    
    # Get exam
    result = await db.execute(select(Exam).where(Exam.id == exam_id))
    exam = result.scalar_one_or_none()
    
    if not exam:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Exam not found"
        )
    
    # Create registration
    registration_number = f"REG{exam.exam_code}{candidate.registration_id[-6:]}"
    registration = ExamRegistration(
        candidate_id=candidate.id,
        exam_id=exam_id,
        registration_number=registration_number,
        status="registered"
    )
    
    db.add(registration)
    exam_center.current_booked += 1
    
    await db.commit()
    await db.refresh(registration)
    
    return registration


# ==================== Admit Card Endpoints ====================

@router.get("/admit-card", response_model=AdmitCardResponse)
async def get_admit_card(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get admit card"""
    result = await db.execute(select(Candidate).where(Candidate.user_id == current_user.id))
    candidate = result.scalar_one_or_none()
    
    if not candidate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found"
        )
    
    if not candidate.admit_card:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Admit card not available"
        )
    
    return candidate.admit_card


# ==================== Admin Endpoints ====================

@router.post("/verify/{candidate_id}")
async def verify_application(
    candidate_id: int,
    payload: ApplicationVerificationRequest,
    request: Request,
    current_user: User = Depends(admin_required),
    db: AsyncSession = Depends(get_db),
):
    """Verify candidate application (Admin)"""
    result = await db.execute(select(Candidate).where(Candidate.id == candidate_id))
    candidate = result.scalar_one_or_none()
    
    if not candidate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Candidate not found"
        )
    
    # Update application
    application = candidate.application
    if not application:
        application = Application(
            candidate_id=candidate.id,
            recruitment_batch=payload.recruitment_batch,
            force_type=payload.force_type,
            trade_category=payload.trade_category,
        )
        db.add(application)
    else:
        application.recruitment_batch = payload.recruitment_batch
        application.force_type = payload.force_type
        application.trade_category = payload.trade_category
    
    application.age_eligible = payload.age_eligible
    application.education_eligible = payload.education_eligible
    application.physical_eligible = payload.physical_eligible
    application.documents_verified = payload.documents_verified
    application.overall_eligible = all(
        [
            payload.age_eligible,
            payload.education_eligible,
            payload.physical_eligible,
            payload.documents_verified,
        ]
    )
    application.verification_notes = payload.verification_notes
    application.verified_by = current_user.id
    application.verified_at = datetime.utcnow()
    
    # Update candidate status
    if application.overall_eligible:
        candidate.application_status = ApplicationStatus.VERIFIED
    else:
        candidate.application_status = ApplicationStatus.REJECTED

    await log_security_event(
        db,
        action="candidate_verified",
        request=request,
        user=current_user,
        resource_type="candidate",
        resource_id=candidate.id,
        details=f"overall_eligible={application.overall_eligible}",
    )

    if application.overall_eligible and candidate.admit_card is None:
        registration_result = await db.execute(
            select(ExamRegistration).where(ExamRegistration.candidate_id == candidate.id)
        )
        registration = registration_result.scalar_one_or_none()
        if registration:
            user_result = await db.execute(select(User).where(User.id == candidate.user_id))
            candidate_user = user_result.scalar_one_or_none()
            exam_result = await db.execute(select(Exam).where(Exam.id == registration.exam_id))
            exam = exam_result.scalar_one_or_none()
            center_result = await db.execute(select(ExamCenter).where(ExamCenter.id == exam.exam_center_id))
            exam_center = center_result.scalar_one_or_none()
            candidate_name = candidate_user.full_name if candidate_user else candidate.registration_id
            qr_key = f"admit-cards/{candidate.registration_id}/qr.png"
            qr_uri = storage.upload_bytes(
                qr_key,
                admit_card_generator.generate_qr_code(registration.registration_number),
                "image/png",
            )
            pdf_bytes, admit_card_number = admit_card_generator.generate_admit_card_pdf(
                candidate_name=candidate_name,
                registration_id=candidate.registration_id,
                exam_center=exam_center.center_name,
                exam_date=str(exam.exam_date),
                exam_time=exam.start_time.strftime("%H:%M"),
                candidate_photo_url=None,
            )
            pdf_key = f"admit-cards/{candidate.registration_id}/{admit_card_number}.pdf"
            pdf_uri = storage.upload_bytes(pdf_key, pdf_bytes, "application/pdf")
            admit_card = AdmitCard(
                candidate_id=candidate.id,
                exam_id=exam.id,
                exam_registration_id=registration.id,
                admit_card_number=admit_card_number,
                exam_venue=exam_center.center_name,
                exam_date=exam.exam_date,
                exam_start_time=exam.start_time.strftime("%H:%M"),
                exam_end_time=exam.end_time.strftime("%H:%M"),
                qr_code_url=qr_uri,
                pdf_url=pdf_uri,
            )
            db.add(admit_card)
            if candidate_user:
                admit_card.email_sent = await notification_service.send_admit_card_email(
                    email=candidate_user.email,
                    candidate_name=candidate_name,
                    admit_card_pdf=pdf_bytes,
                    registration_id=candidate.registration_id,
                )
                if candidate_user.phone_number:
                    admit_card.sms_sent = await notification_service.send_admit_card_sms(
                        phone_number=candidate_user.phone_number,
                        candidate_name=candidate_name,
                        registration_id=candidate.registration_id,
                        exam_date=str(exam.exam_date),
                    )
    
    await db.commit()
    
    return {"message": "Application verified", "overall_eligible": application.overall_eligible}




