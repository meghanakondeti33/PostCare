from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.models.domain import EHRRecord
from app.core.dependencies import get_tenant_hospital_id

router = APIRouter()

@router.get("/records", response_model=List[Dict[str, Any]])
async def list_ehr_records(
    db: AsyncSession = Depends(get_db),
    hospital_id: str = Depends(get_tenant_hospital_id)
):
    stmt = select(EHRRecord).where(EHRRecord.hospital_id == hospital_id).order_by(EHRRecord.synced_at.desc()).limit(100)
    res = await db.execute(stmt)
    records = res.scalars().all()
    return [
        {
            "id": r.id,
            "hospital_id": r.hospital_id,
            "patient_id": r.patient_id,
            "encounter_id": r.encounter_id,
            "resource_type": r.resource_type,
            "resource_id": r.resource_id,
            "data": r.data,
            "synced_at": r.synced_at
        } for r in records
    ]
