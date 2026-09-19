import asyncio
import os
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

# Explicitly import all models so Base.metadata contains all tables
from app.core.database import Base, get_db
import app.models.domain as models
from app.main import app
from app.core.security import get_password_hash, create_access_token
from app.models.domain import (
    Hospital, User, Patient, Encounter, Discharge, Campaign, OutreachTask, Protocol,
    RoleEnum, CampaignStatusEnum, TaskStateEnum, EscalationStateEnum
)

TEST_DB_FILE = "./test_suite.db"
TEST_DATABASE_URL = f"sqlite+aiosqlite:///{TEST_DB_FILE}"

engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
)

TestingSessionLocal = async_sessionmaker(
    bind=engine, class_=AsyncSession, expire_on_commit=False
)

from app.core.config import settings

@pytest_asyncio.fixture(autouse=True)
async def setup_db():
    settings.AI_PROVIDER = "mock"
    async with engine.begin() as conn:
        await conn.run_sync(lambda sync_conn: Base.metadata.drop_all(sync_conn, checkfirst=True))
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(lambda sync_conn: Base.metadata.drop_all(sync_conn, checkfirst=True))

async def override_get_db():
    async with TestingSessionLocal() as session:
        yield session

app.dependency_overrides[get_db] = override_get_db

@pytest_asyncio.fixture
async def async_client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

@pytest_asyncio.fixture
async def seed_test_data():
    async with TestingSessionLocal() as db:
        # Hospitals
        hosp_a = Hospital(id="hosp-a", name="Hospital A", code="HOSPA", max_concurrent_calls=2)
        hosp_b = Hospital(id="hosp-b", name="Hospital B", code="HOSPB", max_concurrent_calls=5)
        db.add_all([hosp_a, hosp_b])
        await db.flush()

        pwd = get_password_hash("Pass123!")
        # Users
        admin = User(id="user-platform", hospital_id=None, email="admin@platform.test", hashed_password=pwd, full_name="Admin", role=RoleEnum.PLATFORM_ADMIN)
        mgr_a = User(id="user-mgr-a", hospital_id="hosp-a", email="mgr@hospa.test", hashed_password=pwd, full_name="Mgr A", role=RoleEnum.CAMPAIGN_MANAGER)
        rev_a = User(id="user-rev-a", hospital_id="hosp-a", email="rev@hospa.test", hashed_password=pwd, full_name="Rev A", role=RoleEnum.CLINICAL_REVIEWER)
        mgr_b = User(id="user-mgr-b", hospital_id="hosp-b", email="mgr@hospb.test", hashed_password=pwd, full_name="Mgr B", role=RoleEnum.CAMPAIGN_MANAGER)
        db.add_all([admin, mgr_a, rev_a, mgr_b])
        await db.flush()

        # Patients
        pat_a = Patient(id="pat-a-1", hospital_id="hosp-a", mrn="MRN-A1", first_name="John", last_name="Doe")
        pat_b = Patient(id="pat-b-1", hospital_id="hosp-b", mrn="MRN-B1", first_name="Jane", last_name="Smith")
        db.add_all([pat_a, pat_b])
        await db.flush()

        # Campaign
        camp_a = Campaign(id="camp-a-1", hospital_id="hosp-a", name="Campaign A", status=CampaignStatusEnum.RUNNING, priority_score=5)
        db.add(camp_a)
        await db.flush()

        # Protocols
        proto_a = Protocol(id="proto-a-1", hospital_id="hosp-a", name="Protocol A", red_flags=["chest pain"])
        db.add(proto_a)

        await db.commit()

        return {
            "hosp_a": hosp_a,
            "hosp_b": hosp_b,
            "admin_token": create_access_token({"sub": "user-platform", "role": "PLATFORM_ADMIN"}),
            "mgr_a_token": create_access_token({"sub": "user-mgr-a", "role": "CAMPAIGN_MANAGER", "hospital_id": "hosp-a"}),
            "rev_a_token": create_access_token({"sub": "user-rev-a", "role": "CLINICAL_REVIEWER", "hospital_id": "hosp-a"}),
            "mgr_b_token": create_access_token({"sub": "user-mgr-b", "role": "CAMPAIGN_MANAGER", "hospital_id": "hosp-b"}),
        }
