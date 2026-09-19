import pytest
import json
import httpx
from unittest.mock import AsyncMock, patch, MagicMock

from app.ai.provider import (
    GeminiProvider,
    AIProviderError,
    AIProviderUnavailableError,
    AIProviderConfigError
)

@pytest.mark.asyncio
async def test_gemini_successful_structured_response():
    """Verify GeminiProvider succeeds on 200 OK structured response."""
    provider = GeminiProvider(api_key="test-secret-key-12345", max_retries=2, initial_backoff=0.01)
    
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "candidates": [
            {
                "content": {
                    "parts": [
                        {
                            "text": json.dumps({
                                "classification": "ROUTINE",
                                "observations": ["Patient is doing well"],
                                "red_flags": [],
                                "confidence": 0.95,
                                "escalation_recommendation": False
                            })
                        }
                    ]
                }
            }
        ]
    }
    
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_response
        
        res = await provider.generate_structured(
            prompt="I am feeling good today",
            system_instruction="Analyze patient symptom status",
            response_schema={"classification": "string"}
        )
        
        assert res["classification"] == "ROUTINE"
        assert res["escalation_recommendation"] is False
        assert mock_post.call_count == 1
        
        # Verify API Key was sent in header x-goog-api-key, NOT in URL
        args, kwargs = mock_post.call_args
        assert "key=" not in args[0]
        assert kwargs["headers"]["x-goog-api-key"] == "test-secret-key-12345"

@pytest.mark.asyncio
async def test_gemini_503_then_successful_retry():
    """Verify GeminiProvider retries 503 Service Unavailable and succeeds on second attempt."""
    provider = GeminiProvider(api_key="test-secret-key-12345", max_retries=2, initial_backoff=0.01)
    
    resp_503 = MagicMock(spec=httpx.Response)
    resp_503.status_code = 503
    resp_503.text = "This model is currently experiencing high demand"
    resp_503.headers = {}
    
    resp_200 = MagicMock(spec=httpx.Response)
    resp_200.status_code = 200
    resp_200.json.return_value = {
        "candidates": [
            {
                "content": {
                    "parts": [
                        {
                            "text": json.dumps({
                                "classification": "CONCERNING",
                                "observations": ["Mild fever reported"],
                                "red_flags": ["FEVER"],
                                "confidence": 0.88,
                                "escalation_recommendation": True
                            })
                        }
                    ]
                }
            }
        ]
    }
    
    with patch("httpx.AsyncClient.post", side_effect=[resp_503, resp_200]) as mock_post:
        res = await provider.generate_structured(
            prompt="I have a mild fever",
            system_instruction="Analyze transcript",
            response_schema={"classification": "string"}
        )
        
        assert res["classification"] == "CONCERNING"
        assert mock_post.call_count == 2

@pytest.mark.asyncio
async def test_gemini_repeated_503_exhaustion():
    """Verify GeminiProvider raises AIProviderUnavailableError when max retries are exhausted."""
    provider = GeminiProvider(api_key="test-secret-key-12345", max_retries=2, initial_backoff=0.01)
    
    resp_503 = MagicMock(spec=httpx.Response)
    resp_503.status_code = 503
    resp_503.text = "Service Unavailable"
    resp_503.headers = {}
    
    with patch("httpx.AsyncClient.post", return_value=resp_503) as mock_post:
        with pytest.raises(AIProviderUnavailableError) as exc_info:
            await provider.generate_structured(
                prompt="Hello",
                system_instruction="System",
                response_schema={}
            )
            
        assert exc_info.value.status_code == 503
        assert exc_info.value.provider == "gemini"
        assert mock_post.call_count == 3  # 1 initial + 2 retries

@pytest.mark.asyncio
async def test_gemini_429_retry():
    """Verify GeminiProvider retries 429 Too Many Requests."""
    provider = GeminiProvider(api_key="test-secret-key-12345", max_retries=2, initial_backoff=0.01)
    
    resp_429 = MagicMock(spec=httpx.Response)
    resp_429.status_code = 429
    resp_429.text = "Rate limit exceeded"
    resp_429.headers = {"Retry-After": "0.01"}
    
    resp_200 = MagicMock(spec=httpx.Response)
    resp_200.status_code = 200
    resp_200.json.return_value = {
        "candidates": [{"content": {"parts": [{"text": "Hello response"}]}}]
    }
    
    with patch("httpx.AsyncClient.post", side_effect=[resp_429, resp_200]) as mock_post:
        res = await provider.generate_response(
            prompt="Hello",
            system_instruction="System"
        )
        assert res == "Hello response"
        assert mock_post.call_count == 2

@pytest.mark.asyncio
async def test_gemini_404_no_retry():
    """Verify GeminiProvider does NOT retry 404 (or other 4xx config errors) and immediately raises AIProviderConfigError."""
    provider = GeminiProvider(api_key="test-secret-key-12345", max_retries=2, initial_backoff=0.01)
    
    resp_404 = MagicMock(spec=httpx.Response)
    resp_404.status_code = 404
    resp_404.text = "models/gemini-3.5-flash is not found for API version v1beta"
    resp_404.headers = {}
    
    with patch("httpx.AsyncClient.post", return_value=resp_404) as mock_post:
        with pytest.raises(AIProviderConfigError) as exc_info:
            await provider.generate_structured(
                prompt="Test prompt",
                system_instruction="System",
                response_schema={}
            )
            
        assert exc_info.value.status_code == 404
        assert exc_info.value.provider == "gemini"
        assert mock_post.call_count == 1  # Retried 0 times

@pytest.mark.asyncio
async def test_gemini_api_key_redaction():
    """Verify that error messages redact the API key if it appears in error text."""
    secret = "secret_api_key_9999"
    provider = GeminiProvider(api_key=secret, max_retries=0)
    
    resp_400 = MagicMock(spec=httpx.Response)
    resp_400.status_code = 400
    resp_400.text = f"Invalid request with key {secret} in error body"
    resp_400.headers = {}
    
    with patch("httpx.AsyncClient.post", return_value=resp_400):
        with pytest.raises(AIProviderConfigError) as exc_info:
            await provider.generate_structured("test", "sys", {})
            
        err_text = str(exc_info.value)
        assert secret not in err_text
        assert "[REDACTED_API_KEY]" in err_text
