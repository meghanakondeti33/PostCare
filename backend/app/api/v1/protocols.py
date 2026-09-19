import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.models.domain import Protocol
from app.schemas.domain import ProtocolCreate, ProtocolOut
from app.core.dependencies import get_tenant_hospital_id

router = APIRouter()

@router.get("/", response_model=List[ProtocolOut])
async def list_protocols(
    db: AsyncSession = Depends(get_db),
    hospital_id: str = Depends(get_tenant_hospital_id)
):
    stmt = select(Protocol).where(Protocol.hospital_id == hospital_id)
    res = await db.execute(stmt)
    return res.scalars().all()

@router.post("/", response_model=ProtocolOut)
async def create_protocol(
    data: ProtocolCreate,
    db: AsyncSession = Depends(get_db),
    hospital_id: str = Depends(get_tenant_hospital_id)
):
    p_id = f"proto-{uuid.uuid4().hex[:8]}"
    proto = Protocol(
        id=p_id,
        hospital_id=hospital_id,
        name=data.name,
        category=data.category,
        target_conditions=data.target_conditions,
        red_flags=data.red_flags,
        follow_up_questions=data.follow_up_questions,
        escalation_contacts=data.escalation_contacts,
        is_active=True
    )
    db.add(proto)
    await db.commit()
    await db.refresh(proto)
    return proto
