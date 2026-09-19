import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.models.domain import Campaign, CampaignStatusEnum, User
from app.schemas.domain import CampaignCreate, CampaignUpdate, CampaignOut
from app.core.dependencies import get_current_user, get_tenant_hospital_id

router = APIRouter()

@router.get("/", response_model=List[CampaignOut])
async def list_campaigns(
    db: AsyncSession = Depends(get_db),
    hospital_id: str = Depends(get_tenant_hospital_id)
):
    stmt = select(Campaign).where(Campaign.hospital_id == hospital_id).order_by(Campaign.created_at.desc())
    res = await db.execute(stmt)
    return res.scalars().all()

@router.post("/", response_model=CampaignOut)
async def create_campaign(
    data: CampaignCreate,
    db: AsyncSession = Depends(get_db),
    hospital_id: str = Depends(get_tenant_hospital_id)
):
    c_id = f"camp-{uuid.uuid4().hex[:8]}"
    campaign = Campaign(
        id=c_id,
        hospital_id=hospital_id,
        name=data.name,
        description=data.description,
        status=CampaignStatusEnum.READY,
        eligibility_rules=data.eligibility_rules,
        follow_up_window_hours=data.follow_up_window_hours,
        calling_start_hour=data.calling_start_hour,
        calling_end_hour=data.calling_end_hour,
        priority_score=data.priority_score,
        retry_limit=data.retry_limit,
        max_concurrent_calls=data.max_concurrent_calls
    )
    db.add(campaign)
    await db.commit()
    await db.refresh(campaign)
    return campaign

@router.post("/{campaign_id}/status", response_model=CampaignOut)
async def update_campaign_status(
    campaign_id: str,
    status_str: str,
    db: AsyncSession = Depends(get_db),
    hospital_id: str = Depends(get_tenant_hospital_id)
):
    stmt = select(Campaign).where(Campaign.id == campaign_id, Campaign.hospital_id == hospital_id)
    res = await db.execute(stmt)
    campaign = res.scalar_one_or_none()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
        
    try:
        new_status = CampaignStatusEnum(status_str.upper())
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid status: {status_str}")
        
    campaign.status = new_status
    await db.commit()
    await db.refresh(campaign)
    return campaign
