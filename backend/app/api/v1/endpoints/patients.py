from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.schemas.patient import PatientCreate, PatientResponse, DPDPErasureRequest
from app.crud.patient import create_patient, get_patient_by_id, get_patients_by_village, dpdp_erase_patient
from app.api.v1.endpoints.auth import get_current_user
from app.models.user import User

router = APIRouter()


@router.post("/", response_model=PatientResponse, status_code=status.HTTP_201_CREATED)
async def register_new_patient(
    patient_in: PatientCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Register a patient with encrypted PII and voice/written consent.
    Automatically assigns a deterministic pseudonym_id.
    """
    patient = await create_patient(
        db=db,
        patient_in=patient_in,
        actor_id=str(current_user.id),
        actor_role=current_user.role
    )
    # Return decrypted PII for the registering frontline health worker
    pii_dict = patient_in.pii.model_dump()
    resp = PatientResponse.model_validate(patient)
    resp.pii = pii_dict
    return resp


@router.get("/", response_model=List[PatientResponse])
async def list_patients(
    village_id: Optional[str] = Query(None, description="Filter by village"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List patients scoped to health worker's assigned village or filtered by village_id.
    """
    target_village = village_id or current_user.assigned_village_id
    if not target_village and current_user.role not in ["ADMIN", "DOCTOR", "OFFICER"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Village ID must be provided or assigned to health worker"
        )
    
    if target_village:
        patients = await get_patients_by_village(db, village_id=target_village, skip=skip, limit=limit)
    else:
        # Doctor / Admin global view
        patients = await get_patients_by_village(db, village_id=village_id, skip=skip, limit=limit)

    return [PatientResponse.model_validate(p) for p in patients]


@router.get("/{patient_id}", response_model=PatientResponse)
async def get_patient_profile(
    patient_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Fetch patient record. Authorized healthcare workers and doctors receive decrypted PII.
    """
    result = await get_patient_by_id(db, patient_id=patient_id, include_pii=True)
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found")

    patient, decrypted_pii = result
    resp = PatientResponse.model_validate(patient)
    resp.pii = decrypted_pii
    return resp


@router.delete("/{patient_id}", status_code=status.HTTP_200_OK)
async def request_dpdp_erasure(
    patient_id: UUID,
    request: DPDPErasureRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Execute DPDP Act 2023 Right to Erasure / Right to be Forgotten.
    Irreversibly redacts PII and revokes consent with an immutable audit entry.
    """
    success = await dpdp_erase_patient(
        db=db,
        patient_id=patient_id,
        reason=request.reason,
        actor_id=str(current_user.id),
        actor_role=current_user.role
    )
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found")

    return {"message": "Patient data successfully erased in compliance with DPDP Act 2023"}
