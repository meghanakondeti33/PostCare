import pytest
from app.ai.voice_agent import VoiceIntakeAgent
from app.ai.provider import MockAIProvider
from app.models.domain import Patient, OutreachTask
from tests.conftest import TestingSessionLocal

@pytest.mark.asyncio
async def test_voice_intake_agent_statement_fidelity(seed_test_data):
    async with TestingSessionLocal() as db:
        agent = VoiceIntakeAgent(db, "hosp-a")
        
        patient = Patient(
            id="pat-test-voice",
            hospital_id="hosp-a",
            first_name="Jane",
            last_name="Doe",
            mrn="MRN-VOICE-1",
            high_risk_flag=True
        )
        task = OutreachTask(
            id="task-test-voice",
            hospital_id="hosp-a",
            patient_id="pat-test-voice",
            campaign_id="camp-a-1"
        )
        
        patient_utterance = "I am having sharp lower abdominal pain and a slight fever."
        
        res = await agent.process_intake(
            patient=patient,
            task=task,
            rag_evidence=[{"title": "Post-Op Guidance", "text": "Watch for fever over 100.4", "score": 0.9}],
            patient_responses=[patient_utterance]
        )
        
        # 1. Statement Preservation Verification
        assert res["transcript_text"] == patient_utterance
        turns = res["transcript_turns"]
        assert len(turns) >= 2
        patient_turn = next(t for t in turns if t["speaker"].startswith("Patient"))
        assert patient_utterance in patient_turn["text"]
        
        # 2. Non-Triage Boundary Verification
        # VoiceIntakeAgent must NOT contain classification keys like ROUTINE/CONCERNING/URGENT
        assert "classification" not in res or res.get("classification") is None
        assert "triage_classification" not in res
        
        # 3. Symptom Extraction Verification
        assert "patient_reported_symptoms" in res
        assert len(res["patient_reported_symptoms"]) > 0

@pytest.mark.asyncio
async def test_voice_intake_agent_no_fabrication(seed_test_data):
    async with TestingSessionLocal() as db:
        agent = VoiceIntakeAgent(db, "hosp-a")
        patient = Patient(
            id="pat-test-voice-2",
            hospital_id="hosp-a",
            first_name="John",
            last_name="Smith",
            mrn="MRN-VOICE-2"
        )
        task = OutreachTask(
            id="task-test-voice-2",
            hospital_id="hosp-a",
            patient_id="pat-test-voice-2",
            campaign_id="camp-a-1"
        )
        
        exact_input = "My leg incision looks clean and I took my prescribed medications."
        res = await agent.process_intake(
            patient=patient,
            task=task,
            patient_responses=[exact_input]
        )
        
        # Ensure exact input is retained without inventing unmentioned symptoms
        assert res["transcript_text"] == exact_input
        for symptom in res.get("patient_reported_symptoms", []):
            assert "chest pain" not in symptom.lower()
            assert "shortness of breath" not in symptom.lower()
