import json
import os
from typing import Dict, Any
from fastapi import APIRouter, Depends

from app.evaluation.run_safety_eval import run_safety_evaluation
from app.models.domain import User, RoleEnum
from app.core.dependencies import require_roles

router = APIRouter()

@router.post("/run", response_model=Dict[str, Any])
async def trigger_safety_evaluation(
    current_user: User = Depends(require_roles([RoleEnum.PLATFORM_ADMIN, RoleEnum.HOSPITAL_ADMIN]))
):
    report = await run_safety_evaluation()
    return report
