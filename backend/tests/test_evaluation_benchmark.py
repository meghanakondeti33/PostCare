import pytest
from httpx import AsyncClient
from app.evaluation.run_safety_eval import run_safety_evaluation, SAFETY_TEST_DATASET
from app.ai.provider import MockAIProvider

@pytest.mark.asyncio
async def test_deterministic_safety_benchmark_repeated_runs():
    """Verify that repeated benchmark runs return identical metrics and consume 0 Gemini quota."""
    report1 = await run_safety_evaluation()
    report2 = await run_safety_evaluation()

    assert report1["dataset_size"] == 25
    assert report2["dataset_size"] == 25
    
    # Metrics must be 100% reproducible and identical
    assert report1["metrics"] == report2["metrics"]
    
    metrics = report1["metrics"]
    assert metrics["total_scenarios"] == 25
    assert metrics["true_positives"] == 18
    assert metrics["true_negatives"] == 7
    assert metrics["false_positives"] == 0
    assert metrics["false_negatives"] == 0
    assert metrics["false_negative_rate"] == 0.0
    assert metrics["accuracy"] == 1.0
    assert metrics["recall"] == 1.0
    assert metrics["precision"] == 1.0

@pytest.mark.asyncio
async def test_safety_benchmark_fn_calculation():
    """Verify explicit false negative calculation formula and zero-denominator handling."""
    # Test dataset with intentional FN (Expected Escalate=True, but AI returns ROUTINE)
    custom_dataset = [
        {"id": "TC-FAIL", "category": "URGENT", "transcript": "Severe chest pain", "expected_escalate": True}
    ]

    class FlawedAIProvider:
        async def generate_structured(self, prompt, system_instruction, response_schema, prompt_version="v1.0.0"):
            return {"classification": "ROUTINE", "escalation_recommendation": False}

    report = await run_safety_evaluation(ai_provider=FlawedAIProvider())
    metrics = report["metrics"]
    
    assert metrics["false_negatives"] == 18
    assert metrics["false_negative_rate"] == 1.0
    assert metrics["accuracy"] == 0.28

@pytest.mark.asyncio
async def test_evaluation_endpoint_rbac_and_response(async_client: AsyncClient, seed_test_data):
    """Verify endpoint POST /api/v1/evaluation/run enforces RBAC and returns structured report."""
    # Unauthenticated request -> 401
    res_unauth = await async_client.post("/api/v1/evaluation/run")
    assert res_unauth.status_code == 401

    # Authenticated Admin request -> 200 OK
    headers = {"Authorization": f"Bearer {seed_test_data['admin_token']}"}
    res_admin = await async_client.post("/api/v1/evaluation/run", headers=headers)
    assert res_admin.status_code == 200
    
    data = res_admin.json()
    assert data["dataset_size"] == 25
    assert "metrics" in data
    assert data["metrics"]["total_scenarios"] == 25
    assert "false_negative_rate" in data["metrics"]
    assert "test_results" in data
    assert len(data["test_results"]) == 25
