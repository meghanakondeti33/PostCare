from fastapi import APIRouter
from app.api.v1 import (
    auth, hospitals, patients, campaigns, queue, calls, escalations,
    protocols, ehr, analytics, observability, evaluation
)

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["Auth"])
api_router.include_router(hospitals.router, prefix="/hospitals", tags=["Hospitals"])
api_router.include_router(patients.router, prefix="/patients", tags=["Patients"])
api_router.include_router(campaigns.router, prefix="/campaigns", tags=["Campaigns"])
api_router.include_router(queue.router, prefix="/queue", tags=["Queue"])
api_router.include_router(calls.router, prefix="/calls", tags=["Calls"])
api_router.include_router(escalations.router, prefix="/escalations", tags=["Escalations"])
api_router.include_router(protocols.router, prefix="/protocols", tags=["Protocols"])
api_router.include_router(ehr.router, prefix="/ehr", tags=["EHR"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["Analytics"])
api_router.include_router(observability.router, prefix="/observability", tags=["Observability"])
api_router.include_router(evaluation.router, prefix="/evaluation", tags=["Evaluation"])
