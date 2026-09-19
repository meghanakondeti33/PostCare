import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.models.domain import Hospital, RoleEnum, User
from app.schemas.domain import HospitalCreate, HospitalOut
from app.core.dependencies import get_current_user, require_roles

router = APIRouter()

@router.get("/", response_model=List[HospitalOut])
async def list_hospitals(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles([RoleEnum.PLATFORM_ADMIN, RoleEnum.HOSPITAL_ADMIN]))
):
    if current_user.role == RoleEnum.PLATFORM_ADMIN:
        stmt = select(Hospital)
    else:
        stmt = select(Hospital).where(Hospital.id == current_user.hospital_id)
        
    res = await db.execute(stmt)
    return res.scalars().all()

@router.post("/", response_model=HospitalOut)
async def create_hospital(
    data: HospitalCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles([RoleEnum.PLATFORM_ADMIN]))
):
    h_id = f"hosp-{uuid.uuid4().hex[:8]}"
    hospital = Hospital(
        id=h_id,
        name=data.name,
        code=data.code.upper(),
        timezone=data.timezone,
        calling_start_hour=data.calling_start_hour,
        calling_end_hour=data.calling_end_hour,
        max_concurrent_calls=data.max_concurrent_calls,
        retry_rules=data.retry_rules or {},
        notification_config=data.notification_config or {},
        ehr_config=data.ehr_config or {}
    )
    db.add(hospital)
    await db.commit()
    await db.refresh(hospital)
    return hospital
