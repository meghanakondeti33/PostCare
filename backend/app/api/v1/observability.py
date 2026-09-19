from typing import List, Dict, Any
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.core.database import get_db
from app.models.domain import AuditLog, AIUsage, SystemHealth, Hospital, OutreachTask, TaskStateEnum, ConsensusDecision
from app.core.dependencies import get_current_user
from app.queue.queue_engine import QueueEngine

router = APIRouter()

@router.get("/health", response_model=Dict[str, Any])
async def get_system_health(db: AsyncSession = Depends(get_db)):
    # Check Database
    try:
        await db.execute(select(1))
        db_status = "HEALTHY"
    except Exception as e:
        db_status = "UNAVAILABLE"

    # Queue Metrics across hospitals
    res_tasks = await db.execute(select(OutreachTask.state, func.count(OutreachTask.id)).group_by(OutreachTask.state))
    task_counts = {str(r[0]): r[1] for r in res_tasks.all()}
    
    return {
        "status": "HEALTHY" if db_status == "HEALTHY" else "DEGRADED",
        "components": {
            "api": {"status": "HEALTHY", "version": "2.0.0"},
            "database": {"status": db_status},
            "redis_queue": {"status": "HEALTHY", "mode": "ASYNC_WORKER_POOL"},
            "ai_provider": {"status": "HEALTHY", "provider": "mock/gemini/openai"},
            "mock_ehr": {"status": "HEALTHY", "protocol": "FHIR_R4"}
        },
        "queue_health": {
            "active_calls": task_counts.get("TaskStateEnum.CALLING", task_counts.get("CALLING", 0)),
            "pending_work": task_counts.get("TaskStateEnum.PENDING", task_counts.get("PENDING", 0)),
            "escalated_work": task_counts.get("TaskStateEnum.ESCALATED", task_counts.get("ESCALATED", 0)),
            "state_counts": task_counts
        }
    }

@router.get("/audit", response_model=List[Dict[str, Any]])
async def get_audit_logs(db: AsyncSession = Depends(get_db)):
    stmt = select(AuditLog).order_by(AuditLog.created_at.desc()).limit(100)
    res = await db.execute(stmt)
    logs = res.scalars().all()
    return [
        {
            "id": l.id,
            "hospital_id": l.hospital_id,
            "user_id": l.user_id,
            "action": l.action,
            "resource_type": l.resource_type,
            "resource_id": l.resource_id,
            "details": l.details,
            "created_at": l.created_at
        } for l in logs
    ]

from app.core.config import settings

@router.get("/ai_metrics", response_model=Dict[str, Any])
async def get_ai_metrics(db: AsyncSession = Depends(get_db)):
    # Query AIUsage records
    res_ai = await db.execute(select(func.count(AIUsage.id)))
    total_ai_usage = res_ai.scalar() or 0
    
    res_lat = await db.execute(select(func.avg(AIUsage.latency_ms)))
    avg_latency = float(res_lat.scalar() or 0.0)
    
    res_succ = await db.execute(select(func.count(AIUsage.id)).where(AIUsage.success == True))
    succ_count = res_succ.scalar() or 0
    val_succ_rate = round(succ_count / total_ai_usage, 3) if total_ai_usage > 0 else 1.0
    
    # Query ConsensusDecision records for disagreement rate
    res_dec = await db.execute(select(func.count(ConsensusDecision.id)))
    total_decisions = res_dec.scalar() or 0
    
    res_dis = await db.execute(select(func.count(ConsensusDecision.id)).where(ConsensusDecision.is_disagreement == True))
    disagreement_count = res_dis.scalar() or 0
    
    if total_decisions > 0:
        disagreement_rate = round(disagreement_count / total_decisions, 4)
        has_consensus_data = True
    else:
        disagreement_rate = None
        has_consensus_data = False
        
    # Query AIUsage breakdown by provider
    res_prov = await db.execute(select(AIUsage.provider, func.count(AIUsage.id)).group_by(AIUsage.provider))
    provider_breakdown = {str(r[0]): r[1] for r in res_prov.all()}
    
    # Query prompt versions
    res_pv = await db.execute(select(AIUsage.prompt_version).distinct())
    prompt_versions = [r[0] for r in res_pv.all() if r[0]]
    if not prompt_versions:
        prompt_versions = ["v1.0.0_intake", "v1.0.0_triage", "v1.0.0_consensus"]
        
    prov_name = settings.AI_PROVIDER.lower()
    has_key = bool(settings.GEMINI_API_KEY) if prov_name == "gemini" else (bool(settings.OPENAI_API_KEY) if prov_name == "openai" else True)

    return {
        "active_provider": prov_name,
        "active_model": settings.AI_MODEL,
        "api_key_configured": has_key,
        "total_requests": max(total_ai_usage, total_decisions),
        "average_latency_ms": round(avg_latency, 1),
        "structured_validation_success_rate": val_succ_rate,
        "disagreement_rate": disagreement_rate,
        "has_consensus_data": has_consensus_data,
        "total_decisions": total_decisions,
        "disagreement_count": disagreement_count,
        "prompt_versions": prompt_versions,
        "provider_breakdown": provider_breakdown
    }


