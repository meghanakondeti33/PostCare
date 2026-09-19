import pytest
import uuid
from datetime import datetime
from app.ai.provider import MockAIProvider
from app.ai.consensus import ConsensusEngine
from app.tools.controlled_tools import ControlledTools
from app.models.domain import Event, TaskStateEnum
from tests.conftest import TestingSessionLocal

@pytest.mark.asyncio
async def test_ai_structured_output_validation():
    provider = MockAIProvider()
    res = await provider.generate_structured(
        prompt="I have severe chest pain and shortness of breath",
        system_instruction="Analyze transcript",
        response_schema={"classification": "string"}
    )
    assert res["classification"] == "URGENT"
    assert res["escalation_recommendation"] is True

@pytest.mark.asyncio
async def test_consensus_disagreement_and_conservative_escalation(seed_test_data):
    async with TestingSessionLocal() as db:
        ce = ConsensusEngine(db, "hosp-a")
        transcript = "I'm having severe crushing chest tightness and I can't catch my breath."
        consensus = await ce.evaluate_consensus(
            call_id="call-test-1",
            patient_id="pat-a-1",
            campaign_id="camp-a-1",
            transcript=transcript,
            protocol_red_flags=["chest pain"]
        )
        assert consensus.consensus_classification.value == "URGENT"
        assert consensus.final_escalation_recommendation is True

@pytest.mark.asyncio
async def test_controlled_ai_tools_and_mock_ehr(seed_test_data):
    async with TestingSessionLocal() as db:
        tools = ControlledTools(db, "hosp-a", user_id="user-rev-a")

        # 1. Get Patient Context
        ctx = await tools.get_patient_context("pat-a-1")
        assert ctx is not None
        assert ctx["mrn"] == "MRN-A1"

        # 2. Search Protocol
        matches = await tools.search_protocol("chest pain")
        assert len(matches) > 0

        # 3. Create Escalation
        esc_res = await tools.create_escalation(
            patient_id="pat-a-1",
            call_id="call-test-1",
            campaign_id="camp-a-1",
            priority="URGENT",
            trigger_reason="Chest pain reported",
            clinical_indicators=["CHEST_PAIN"],
            evidence=["Patient statement"]
        )
        assert esc_res["status"] == "SUCCESS"

        # 4. Update Mock EHR
        ehr_res = await tools.update_mock_ehr(
            patient_id="pat-a-1",
            resource_type="Communication",
            resource_id="COMM-TEST-1",
            data={"summary": "Escalation recorded"}
        )
        assert ehr_res["status"] == "SUCCESS"

@pytest.mark.asyncio
async def test_idempotency_and_event_processing(seed_test_data):
    async with TestingSessionLocal() as db:
        idempotency_key = f"evt-key-{uuid.uuid4().hex}"
        
        event1 = Event(
            id=str(uuid.uuid4()),
            hospital_id="hosp-a",
            event_type="PATIENT_IMPORTED",
            payload={"patient_id": "pat-a-1"},
            idempotency_key=idempotency_key,
            processed=True,
            processed_at=datetime.utcnow()
        )
        db.add(event1)
        await db.commit()

        # Duplicate event insertion with same idempotency key should raise integrity constraint or be safely skipped
        event2 = Event(
            id=str(uuid.uuid4()),
            hospital_id="hosp-a",
            event_type="PATIENT_IMPORTED",
            payload={"patient_id": "pat-a-1"},
            idempotency_key=idempotency_key
        )
        db.add(event2)
        with pytest.raises(Exception):
            await db.commit()
