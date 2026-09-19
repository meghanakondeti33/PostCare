import uuid
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, update

from app.models.domain import (
    OutreachTask, Campaign, CampaignStatusEnum, Patient, Discharge, Call, Hospital, TaskStateEnum,
    Event, AuditLog, Notification
)
from app.core.config import settings

logger = logging.getLogger(__name__)

class QueueEngine:
    """
    Intelligent Capacity-Aware Outbound Queue & Scheduling Engine.
    Implements centralized concurrency control, dynamic multi-factor prioritization,
    starvation prevention, exponential backoff retries, explicit callback handling,
    and crashed worker recovery.
    """
    
    def __init__(self, db: AsyncSession, hospital_id: str):
        self.db = db
        self.hospital_id = hospital_id

    def calculate_priority_score(
        self,
        risk_tier: str,
        created_at: datetime,
        clinical_cutoff_at: Optional[datetime],
        scheduled_callback_at: Optional[datetime],
        campaign_priority: int,
        attempt_count: int
    ) -> float:
        now = datetime.utcnow()
        
        # 1. Base Clinical Risk Score
        risk_scores = {"URGENT": 40.0, "HIGH": 30.0, "MEDIUM": 15.0, "LOW": 5.0}
        score = risk_scores.get(risk_tier.upper(), 10.0)
        
        # 2. Deadline Pressure (Surges as clinical cutoff approaches)
        if clinical_cutoff_at:
            hours_remaining = (clinical_cutoff_at - now).total_seconds() / 3600.0
            if hours_remaining <= 0:
                score += 50.0  # Overdue cutoff
            elif hours_remaining <= 6:
                score += 40.0
            elif hours_remaining <= 12:
                score += 25.0
            elif hours_remaining <= 24:
                score += 10.0
                
        # 3. Callback Urgency
        if scheduled_callback_at:
            time_diff = (now - scheduled_callback_at).total_seconds() / 60.0
            if time_diff >= 0:
                score += 45.0  # Callback due or overdue
                
        # 4. Campaign Priority Weight (0 - 50)
        score += float(campaign_priority * 5)
        
        # 5. Waiting Time Aging (Prevents Starvation: +2 points per waiting hour)
        hours_waiting = (now - created_at).total_seconds() / 3600.0
        score += min(hours_waiting * 2.0, 30.0)
        
        # 6. Retry Penalty (-5 points per failed attempt to prioritize fresh calls)
        score -= float(attempt_count * 5.0)
        
        return round(score, 2)

    async def get_active_calling_count(self) -> int:
        stmt = select(func.count(OutreachTask.id)).where(
            OutreachTask.hospital_id == self.hospital_id,
            OutreachTask.state == TaskStateEnum.CALLING
        )
        res = await self.db.execute(stmt)
        return res.scalar() or 0

    async def get_hospital_capacity_limit(self) -> int:
        stmt = select(Hospital).where(Hospital.id == self.hospital_id)
        res = await self.db.execute(stmt)
        hospital = res.scalar_one_or_none()
        if hospital:
            return hospital.max_concurrent_calls
        return settings.DEFAULT_HOSPITAL_CAPACITY

    async def recover_stale_tasks(self, timeout_minutes: int = 5) -> int:
        """
        Worker Crash Recovery: Detects tasks stuck in CALLING state for longer than timeout_minutes,
        releases capacity, and resets task to RETRY_SCHEDULED or MANUAL_FOLLOW_UP.
        """
        cutoff = datetime.utcnow() - timedelta(minutes=timeout_minutes)
        stmt = select(OutreachTask).where(
            OutreachTask.hospital_id == self.hospital_id,
            OutreachTask.state == TaskStateEnum.CALLING,
            OutreachTask.locked_at < cutoff
        )
        res = await self.db.execute(stmt)
        stale_tasks = res.scalars().all()
        
        recovered_count = 0
        for task in stale_tasks:
            logger.warning(f"Recovering stale task {task.id} locked by worker {task.worker_id}")
            task.attempt_count += 1
            if task.attempt_count >= task.max_attempts:
                task.state = TaskStateEnum.MANUAL_FOLLOW_UP
            else:
                task.state = TaskStateEnum.RETRY_SCHEDULED
                task.next_attempt_at = datetime.utcnow() + timedelta(minutes=10)
            task.worker_id = None
            task.locked_at = None
            recovered_count += 1
            
        if recovered_count > 0:
            await self.db.flush()
        return recovered_count

    async def reserve_next_task(self, worker_id: str) -> Optional[OutreachTask]:
        """
        Safely reserves the highest priority eligible task using FOR UPDATE SKIP LOCKED
        while respecting hospital concurrency limits.
        """
        # 1. Recover stale tasks first
        await self.recover_stale_tasks()
        
        # 2. Check current capacity
        active_count = await self.get_active_calling_count()
        limit = await self.get_hospital_capacity_limit()
        if active_count >= limit:
            logger.info(f"Hospital {self.hospital_id} capacity reached ({active_count}/{limit})")
            return None
            
        now = datetime.utcnow()
        
        # 3. Query candidate tasks: PENDING, RETRY_SCHEDULED, CALLBACK_SCHEDULED where campaign is RUNNING and next_attempt_at <= now
        stmt = select(OutreachTask).join(Campaign, OutreachTask.campaign_id == Campaign.id).where(
            OutreachTask.hospital_id == self.hospital_id,
            Campaign.status == CampaignStatusEnum.RUNNING,
            OutreachTask.state.in_([
                TaskStateEnum.PENDING,
                TaskStateEnum.RETRY_SCHEDULED,
                TaskStateEnum.CALLBACK_SCHEDULED
            ]),
            or_(OutreachTask.next_attempt_at.is_(None), OutreachTask.next_attempt_at <= now)
        ).order_by(OutreachTask.priority_score.desc()).with_for_update(skip_locked=True).limit(1)
        
        res = await self.db.execute(stmt)
        task = res.scalar_one_or_none()
        
        if task:
            task.state = TaskStateEnum.CALLING
            task.worker_id = worker_id
            task.locked_at = now
            await self.db.flush()
            logger.info(f"Worker {worker_id} successfully reserved task {task.id} (Priority: {task.priority_score})")
            return task
            
        return None

    async def record_task_outcome(
        self,
        task_id: str,
        outcome: str,
        conversation_context: Optional[Dict[str, Any]] = None,
        requested_callback_iso: Optional[str] = None
    ) -> OutreachTask:
        """
        Processes call completion, retries with backoff, callbacks, dropped calls, or manual follow-ups.
        """
        stmt = select(OutreachTask).where(OutreachTask.id == task_id, OutreachTask.hospital_id == self.hospital_id)
        res = await self.db.execute(stmt)
        task = res.scalar_one_or_none()
        if not task:
            raise ValueError(f"OutreachTask {task_id} not found")
            
        now = datetime.utcnow()
        task.worker_id = None
        task.locked_at = None
        
        if conversation_context:
            merged = task.partial_context or {}
            merged.update(conversation_context)
            task.partial_context = merged

        if outcome == "COMPLETED":
            task.state = TaskStateEnum.COMPLETED
        elif outcome == "CALLBACK_REQUESTED" and requested_callback_iso:
            task.state = TaskStateEnum.CALLBACK_SCHEDULED
            callback_dt = datetime.fromisoformat(requested_callback_iso.replace("Z", "+00:00"))
            task.scheduled_callback_at = callback_dt
            task.next_attempt_at = callback_dt
        elif outcome in ["NO_ANSWER", "BUSY", "VOICEMAIL", "DROPPED"]:
            task.attempt_count += 1
            if task.attempt_count >= task.max_attempts:
                task.state = TaskStateEnum.MANUAL_FOLLOW_UP
                # Create notification for staff
                notif = Notification(
                    id=str(uuid.uuid4()),
                    hospital_id=self.hospital_id,
                    type="MAX_RETRIES_EXHAUSTED",
                    title="Manual Follow-Up Required",
                    message=f"Task {task.id} for patient {task.patient_id} reached maximum retries ({task.max_attempts}).",
                    channel="dashboard",
                    created_at=now
                )
                self.db.add(notif)
            else:
                task.state = TaskStateEnum.RETRY_SCHEDULED
                # Exponential Backoff Strategy
                delays = {1: 15, 2: 60, 3: 240} # minutes
                delay_minutes = delays.get(task.attempt_count, 120)
                task.next_attempt_at = now + timedelta(minutes=delay_minutes)
        else:
            task.state = TaskStateEnum.FAILED
            
        await self.db.flush()
        return task

    async def get_queue_summary(self) -> Dict[str, Any]:
        limit = await self.get_hospital_capacity_limit()
        active = await self.get_active_calling_count()
        
        # Queue depth (PENDING, RETRY_SCHEDULED, CALLBACK_SCHEDULED)
        stmt = select(func.count(OutreachTask.id)).where(
            OutreachTask.hospital_id == self.hospital_id,
            OutreachTask.state.in_([TaskStateEnum.PENDING, TaskStateEnum.RETRY_SCHEDULED, TaskStateEnum.CALLBACK_SCHEDULED])
        )
        res = await self.db.execute(stmt)
        depth = res.scalar() or 0
        
        # State breakdown
        stmt = select(OutreachTask.state, func.count(OutreachTask.id)).where(
            OutreachTask.hospital_id == self.hospital_id
        ).group_by(OutreachTask.state)
        res = await self.db.execute(stmt)
        breakdown = {row[0].value if hasattr(row[0], 'value') else str(row[0]): row[1] for row in res.all()}
        
        # Cutoff risk count (cutoff within 6 hours)
        six_hours_later = datetime.utcnow() + timedelta(hours=6)
        stmt = select(func.count(OutreachTask.id)).where(
            OutreachTask.hospital_id == self.hospital_id,
            OutreachTask.state.in_([TaskStateEnum.PENDING, TaskStateEnum.RETRY_SCHEDULED, TaskStateEnum.CALLBACK_SCHEDULED]),
            OutreachTask.clinical_cutoff_at <= six_hours_later
        )
        res = await self.db.execute(stmt)
        cutoff_risk = res.scalar() or 0
        
        return {
            "hospital_id": self.hospital_id,
            "active_capacity": active,
            "capacity_limit": limit,
            "queue_depth": depth,
            "cutoff_risk_count": cutoff_risk,
            "state_breakdown": breakdown
        }
