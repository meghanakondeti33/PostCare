import pytest
from httpx import AsyncClient
from app.rag.protocol_rag import ProtocolRAGService
from tests.conftest import TestingSessionLocal

@pytest.mark.asyncio
async def test_tenant_isolation_patient_access(async_client: AsyncClient, seed_test_data):
    # Manager A requests patients list -> Should only retrieve Hospital A patients
    headers_a = {"Authorization": f"Bearer {seed_test_data['mgr_a_token']}"}
    res_a = await async_client.get("/api/v1/patients/", headers=headers_a)
    assert res_a.status_code == 200
    patients_a = res_a.json()
    assert all(p["hospital_id"] == "hosp-a" for p in patients_a)
    assert not any(p["mrn"] == "MRN-B1" for p in patients_a)

    # Manager B requests patients list -> Should only retrieve Hospital B patients
    headers_b = {"Authorization": f"Bearer {seed_test_data['mgr_b_token']}"}
    res_b = await async_client.get("/api/v1/patients/", headers=headers_b)
    assert res_b.status_code == 200
    patients_b = res_b.json()
    assert all(p["hospital_id"] == "hosp-b" for p in patients_b)
    assert not any(p["mrn"] == "MRN-A1" for p in patients_b)

@pytest.mark.asyncio
async def test_tenant_isolation_timeline_denied(async_client: AsyncClient, seed_test_data):
    # Manager A trying to access Hospital B patient's timeline should fail with 404
    headers_a = {"Authorization": f"Bearer {seed_test_data['mgr_a_token']}"}
    res = await async_client.get("/api/v1/patients/pat-b-1/timeline", headers=headers_a)
    assert res.status_code == 404

@pytest.mark.asyncio
async def test_tenant_rag_isolation(seed_test_data):
    async with TestingSessionLocal() as db:
        rag_a = ProtocolRAGService(db, "hosp-a")
        rag_b = ProtocolRAGService(db, "hosp-b")

        await rag_a.ingest_protocol_document("Cardiac Protocol A", "Cardiology", "Severe chest pain requires urgent nurse call.")
        await rag_b.ingest_protocol_document("Orthopedic Protocol B", "Orthopedics", "Knee swelling requires elevation.")

        # Query RAG A -> Should ONLY return Hospital A protocol evidence
        evidence_a = await rag_a.retrieve_protocol_evidence("chest pain")
        assert len(evidence_a) > 0
        assert all(e["hospital_id"] == "hosp-a" for e in evidence_a)

        # Query RAG B -> Should NOT return Hospital A protocol
        evidence_b = await rag_b.retrieve_protocol_evidence("chest pain")
        assert not any(e["hospital_id"] == "hosp-a" for e in evidence_b)

@pytest.mark.asyncio
async def test_rag_functional_retrieval_and_metadata(seed_test_data):
    async with TestingSessionLocal() as db:
        rag_a = ProtocolRAGService(db, "hosp-a")
        rag_b = ProtocolRAGService(db, "hosp-b")

        doc_a_id = await rag_a.ingest_protocol_document(
            title="Metro Cardiac Outreach Guidelines",
            category="Cardiology",
            content="Patients with acute chest pain, dyspnea, or lower extremity swelling must be escalated to the triage nurse immediately."
        )
        await rag_b.ingest_protocol_document(
            title="Cedar Orthopedic Standard",
            category="Orthopedics",
            content="Post-op knee swelling should be treated with ice pack and leg elevation above heart level."
        )

        # Query Hospital A for 'chest pain dyspnea'
        evidence_a = await rag_a.retrieve_protocol_evidence("acute chest pain dyspnea", top_k=3)
        assert len(evidence_a) > 0
        
        match = evidence_a[0]
        assert match["document_id"] == doc_a_id
        assert "chunk_id" in match
        assert match["title"] == "Metro Cardiac Outreach Guidelines"
        assert match["category"] == "Cardiology"
        assert match["hospital_id"] == "hosp-a"
        assert match["score"] > 0.0
        assert "acute chest pain" in match["text"]
        
        # Verify Hospital B evidence is never present in Hospital A retrieval
        assert not any(e["title"] == "Cedar Orthopedic Standard" for e in evidence_a)

@pytest.mark.asyncio
async def test_rag_clinical_concept_mapping_william_miller_regression(seed_test_data):
    """
    Regression test ensuring 'mild pain' query maps via concept_cardiac_pain
    to protocol chunk containing 'angina' with a non-zero relevance score (>0.0).
    """
    async with TestingSessionLocal() as db:
        rag_a = ProtocolRAGService(db, "hosp-a")

        await rag_a.ingest_protocol_document(
            title="Cardiac Red Flags",
            category="Cardiology",
            content="Red Flag Criteria: Any report of new or worsening angina, dyspnea at rest, or edema MUST be escalated immediately."
        )

        # Query mimicking William Miller's response
        query = "I'm feeling ok, but I have some mild pain."
        evidence = await rag_a.retrieve_protocol_evidence(query, top_k=3)

        assert len(evidence) > 0
        match = evidence[0]
        # Score must be non-zero due to concept_cardiac_pain mapping between 'pain' and 'angina'
        assert match["score"] > 0.0
        assert match["score"] >= 0.5
        assert "angina" in match["text"]
