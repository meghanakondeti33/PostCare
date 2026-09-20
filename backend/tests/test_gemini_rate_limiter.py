import pytest
import asyncio
import time
from httpx import Response
from app.ai.provider import GeminiRateLimiter, GeminiProvider, AIProviderUnavailableError, AIProviderConfigError, get_gemini_rate_limiter
from app.core.config import settings

@pytest.mark.asyncio
async def test_gemini_rate_limiter_acquires_within_limit():
    limiter = GeminiRateLimiter(target_rpm=4, window_seconds=60.0)
    limiter.reset()

    t0 = time.time()
    for _ in range(4):
        await limiter.acquire()
    elapsed = time.time() - t0

    # 4 requests within limit should acquire without waiting 60s
    assert elapsed < 2.0
    assert len(limiter.timestamps) == 4

@pytest.mark.asyncio
async def test_gemini_rate_limiter_waits_when_limit_reached(monkeypatch):
    # Set a tiny window and 2 RPM limit for test speed
    limiter = GeminiRateLimiter(target_rpm=2, window_seconds=0.5)
    limiter.reset()

    await limiter.acquire()
    await limiter.acquire()

    t0 = time.time()
    await limiter.acquire()  # Should wait for 0.5s window to clear
    elapsed = time.time() - t0

    assert elapsed >= 0.45
    assert len(limiter.timestamps) >= 1

@pytest.mark.asyncio
async def test_gemini_provider_daily_quota_exhaustion_fails_fast(monkeypatch):
    provider = GeminiProvider(api_key="test-key", max_retries=2)
    limiter = get_gemini_rate_limiter()
    limiter.reset()

    daily_quota_response_body = """
    {
      "error": {
        "code": 429,
        "message": "Quota exceeded for quota metric 'Generate Content requests per day' at 'GenerateRequestsPerDayPerProject-FreeTier'.",
        "status": "RESOURCE_EXHAUSTED"
      }
    }
    """

    attempts_made = 0

    async def mock_post(*args, **kwargs):
        nonlocal attempts_made
        attempts_made += 1
        return Response(status_code=429, text=daily_quota_response_body)

    import httpx
    monkeypatch.setattr(httpx.AsyncClient, "post", mock_post)

    settings.AI_FALLBACK_TO_MOCK = False
    with pytest.raises(AIProviderUnavailableError) as excinfo:
        await provider._post_with_retry("http://test-url", {})

    assert "daily/project quota exhausted" in str(excinfo.value).lower()
    # Should fail fast on attempt 1 without exhausting all 3 attempts
    assert attempts_made == 1

@pytest.mark.asyncio
async def test_gemini_provider_temporary_429_retries_bounded(monkeypatch):
    provider = GeminiProvider(api_key="test-key", max_retries=2, initial_backoff=0.01, max_backoff=0.05)
    limiter = get_gemini_rate_limiter()
    limiter.reset()

    temp_429_body = """
    {
      "error": {
        "code": 429,
        "message": "Resource has been exhausted (e.g. check quota / RPM).",
        "status": "RESOURCE_EXHAUSTED"
      }
    }
    """

    attempts_made = 0

    async def mock_post(*args, **kwargs):
        nonlocal attempts_made
        attempts_made += 1
        return Response(status_code=429, text=temp_429_body)

    import httpx
    monkeypatch.setattr(httpx.AsyncClient, "post", mock_post)

    settings.AI_FALLBACK_TO_MOCK = False
    with pytest.raises(AIProviderUnavailableError) as excinfo:
        await provider._post_with_retry("http://test-url", {})

    # Should exhaust all 3 attempts (1 initial + 2 retries)
    assert attempts_made == 3

@pytest.mark.asyncio
async def test_ai_fallback_to_mock_behavior(monkeypatch):
    monkeypatch.setattr(settings, "GEMINI_API_KEY", None)
    provider = GeminiProvider(api_key=None)

    # When fallback is False, missing key raises error
    settings.AI_FALLBACK_TO_MOCK = False
    with pytest.raises(AIProviderConfigError):
        await provider.generate_response("test", "test")

    # When fallback is True, missing key returns mock response
    settings.AI_FALLBACK_TO_MOCK = True
    resp = await provider.generate_response("I have severe chest pain", "test")
    assert "chest discomfort" in resp.lower() or "concerning" in resp.lower()
