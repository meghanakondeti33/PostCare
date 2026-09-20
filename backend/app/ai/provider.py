import json
import logging
import asyncio
import time
import random
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
import httpx
from app.core.config import settings

logger = logging.getLogger(__name__)

class GeminiRateLimiter:
    """
    Async-compatible, in-memory rate limiter for Gemini API requests.
    Enforces application-side RPM safety limits using a sliding window algorithm.
    """
    def __init__(self, target_rpm: Optional[int] = None, window_seconds: float = 60.0):
        self._target_rpm = target_rpm
        self.window_seconds = window_seconds
        self.timestamps: List[float] = []
        self._lock: Optional[asyncio.Lock] = None

    @property
    def target_rpm(self) -> int:
        if self._target_rpm is not None:
            return self._target_rpm
        return getattr(settings, "GEMINI_RPM_SAFETY_LIMIT", 4)

    def _get_lock(self) -> asyncio.Lock:
        if self._lock is None:
            self._lock = asyncio.Lock()
        return self._lock

    async def acquire(self):
        """
        Acquires permission to send a Gemini API request.
        If current requests in sliding window >= target_rpm, waits asynchronously
        until an available slot opens.
        """
        lock = self._get_lock()
        while True:
            async with lock:
                now = time.time()
                cutoff = now - self.window_seconds
                self.timestamps = [t for t in self.timestamps if t > cutoff]

                rpm_limit = self.target_rpm

                if len(self.timestamps) < rpm_limit:
                    self.timestamps.append(now)
                    return

                oldest = self.timestamps[0]
                wait_time = (oldest + self.window_seconds) - now + 0.1

            if wait_time > 0:
                logger.info(f"Gemini local rate limiter: waiting {wait_time:.2f}s before sending request (RPM safety limit: {rpm_limit})")
                await asyncio.sleep(wait_time)

    def reset(self):
        """Resets the sliding window timestamps and lock (useful for tests)."""
        self.timestamps.clear()
        self._lock = None

_gemini_rate_limiter: Optional[GeminiRateLimiter] = None

def get_gemini_rate_limiter() -> GeminiRateLimiter:
    global _gemini_rate_limiter
    if _gemini_rate_limiter is None:
        _gemini_rate_limiter = GeminiRateLimiter()
    return _gemini_rate_limiter

class AIProviderError(Exception):
    """Base exception for AI provider failures."""
    def __init__(self, message: str, status_code: int = 500, provider: str = "ai"):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.provider = provider

class AIProviderUnavailableError(AIProviderError):
    """Raised when an AI provider is temporarily unavailable (e.g. 503, 429, 500, timeout) after retries."""
    def __init__(self, message: str, provider: str = "gemini", status_code: int = 503):
        super().__init__(message=message, status_code=status_code, provider=provider)

class AIProviderConfigError(AIProviderError):
    """Raised when an AI provider returns a non-retryable 4xx configuration error (e.g. 400, 401, 403, 404)."""
    def __init__(self, message: str, provider: str = "gemini", status_code: int = 400):
        super().__init__(message=message, status_code=status_code, provider=provider)

class AIProviderInterface(ABC):
    @abstractmethod
    async def generate_response(
        self,
        prompt: str,
        system_instruction: str,
        prompt_version: str = "v1.0.0"
    ) -> str:
        pass

    @abstractmethod
    async def generate_structured(
        self,
        prompt: str,
        system_instruction: str,
        response_schema: Dict[str, Any],
        prompt_version: str = "v1.0.0"
    ) -> Dict[str, Any]:
        pass

class MockAIProvider(AIProviderInterface):
    """Deterministic Mock AI Provider for testing and offline evaluation."""
    
    async def generate_response(
        self,
        prompt: str,
        system_instruction: str,
        prompt_version: str = "v1.0.0"
    ) -> str:
        prompt_lower = prompt.lower()
        if "chest pain" in prompt_lower or "shortness of breath" in prompt_lower:
            return "I hear that you are experiencing chest discomfort or shortness of breath. This is concerning, and I am prioritizing your case for immediate nurse escalation."
        elif "fever" in prompt_lower or "swelling" in prompt_lower or "pain" in prompt_lower:
            return "Thank you for sharing that you have a fever or swelling. I will note this observation for our clinical team to follow up."
        else:
            return "Thank you for taking our call. I've recorded that your recovery is progressing as expected with no acute symptoms reported."

    async def generate_structured(
        self,
        prompt: str,
        system_instruction: str,
        response_schema: Dict[str, Any],
        prompt_version: str = "v1.0.0"
    ) -> Dict[str, Any]:
        prompt_lower = prompt.lower()
        
        # Check if this is a Voice Intake Agent structured request
        if "transcript_turns" in json.dumps(response_schema) or "voice intake" in system_instruction.lower():
            patient_utterance = "I am recovering as expected."
            if 'AUTHORITATIVE PATIENT UTTERANCES (DO NOT ALTER OR FABRICATE):\n"' in prompt:
                try:
                    patient_utterance = prompt.split('AUTHORITATIVE PATIENT UTTERANCES (DO NOT ALTER OR FABRICATE):\n"')[1].split('"')[0]
                except Exception:
                    patient_utterance = prompt
            elif "Patient statement:" in prompt:
                patient_utterance = prompt

            symptoms = []
            if "chest" in prompt_lower or "shortness of breath" in prompt_lower:
                symptoms.append("Chest discomfort / shortness of breath")
            elif "fever" in prompt_lower or "swelling" in prompt_lower:
                symptoms.append("Fever / swelling")
            elif "pain" in prompt_lower:
                symptoms.append("Pain")

            return {
                "transcript_turns": [
                    {"speaker": "AI Voice Agent", "text": "Hello, this is Post-Discharge Outreach checking on your recovery."},
                    {"speaker": "Patient", "text": patient_utterance},
                    {"speaker": "AI Voice Agent", "text": "Thank you for providing that update. I am logging your observations."}
                ],
                "transcript_text": patient_utterance,
                "patient_reported_symptoms": symptoms,
                "observations": symptoms or ["Recovery progressing as expected"],
                "clarification_questions": [],
                "callback_preference": None,
                "completion_status": "COMPLETED",
                "structured_intake_evidence": [f"Patient statement: '{patient_utterance}'"],
                "prompt_version": prompt_version
            }

        # Pre-process text to remove common negated symptom phrases before checking red flags
        negation_phrases = [
            "no fever or shortness of breath", "no shortness of breath", "no fever",
            "no chest pain", "pain is mild", "incision is clean", "no issues",
            "without any problem", "no acute symptoms"
        ]
        clean_text = prompt_lower
        for neg in negation_phrases:
            clean_text = clean_text.replace(neg, "")
        
        urgent_keywords = [
            "chest pain", "shortness of breath", "severe bleeding", "coughing up blood",
            "faint", "burst open", "catch my breath", "slurred", "thunderclap",
            "headache", "blood spurting", "crushing chest", "spine surgery", "chest pressure"
        ]
        
        concerning_keywords = [
            "fever", "swelling", "dizziness", "dizzy", "vomiting", "vomited",
            "red and warm", "incision", "swollen", "bowel movement", "ran out of",
            "medication", "worse instead of better"
        ]
        
        ambiguous_keywords = [
            "unsure", "maybe", "confused", "funny", "weird", "feels wrong", "kinda"
        ]
        
        adversarial_keywords = [
            "ignore previous instructions", "system override", "i am a doctor"
        ]
        
        # Check for urgent symptoms
        if any(k in clean_text for k in urgent_keywords):
            return {
                "classification": "URGENT",
                "observations": ["Acute symptom detected", "High risk indicator"],
                "red_flags": ["RED_FLAG_ACUTE_SYMPTOM"],
                "evidence": [f"Patient statement: '{prompt[:100]}...'"],
                "protocol_references": ["Post-Discharge Protocol Section 4.2"],
                "confidence": 0.98,
                "uncertainty": [],
                "escalation_recommendation": True,
                "prompt_version": prompt_version
            }
        # Check for concerning symptoms
        elif any(k in clean_text for k in concerning_keywords):
            return {
                "classification": "CONCERNING",
                "observations": ["Unexpected symptom reported"],
                "red_flags": ["POTENTIAL_COMPLICATION"],
                "evidence": ["Patient reported concerning symptom"],
                "protocol_references": ["Post-Op Guidance Section 3.1"],
                "confidence": 0.89,
                "uncertainty": [],
                "escalation_recommendation": True,
                "prompt_version": prompt_version
            }
        # Check for ambiguous/uncertain or adversarial symptoms
        elif any(k in prompt_lower for k in ambiguous_keywords + adversarial_keywords):
            return {
                "classification": "UNCERTAIN",
                "observations": ["Incomplete or ambiguous symptom description"],
                "red_flags": ["UNCERTAINTY_SAFETY_TRIGGER"],
                "evidence": ["Patient statement ambiguous or adversarial attempt"],
                "protocol_references": ["Standard Post-Discharge Guidance v1.0"],
                "confidence": 0.50,
                "uncertainty": ["Unclear clinical state - conservative escalation triggered"],
                "escalation_recommendation": True, # Conservative policy escalates uncertain cases
                "prompt_version": prompt_version
            }
        # Routine
        else:
            return {
                "classification": "ROUTINE",
                "observations": ["Patient feels well", "Recovery on track"],
                "red_flags": [],
                "evidence": ["No acute symptoms reported"],
                "protocol_references": ["Standard Post-Discharge Guidance v1.0"],
                "confidence": 0.95,
                "uncertainty": [],
                "escalation_recommendation": False,
                "prompt_version": prompt_version
            }

class GeminiProvider(AIProviderInterface):
    """Google Gemini API Provider with strict error reporting, retry handling, and key redaction."""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        max_retries: int = 2,
        initial_backoff: float = 0.5,
        max_backoff: float = 5.0,
        timeout: float = 30.0
    ):
        self.api_key = api_key or settings.GEMINI_API_KEY
        self.max_retries = max_retries
        self.initial_backoff = initial_backoff
        self.max_backoff = max_backoff
        self.timeout = timeout

    def _sanitize_string(self, text: str) -> str:
        """Sanitizes text to prevent API key exposure in logs or tracebacks."""
        if self.api_key and self.api_key in text:
            text = text.replace(self.api_key, "[REDACTED_API_KEY]")
        return text

    def _get_retry_after(self, response: Optional[httpx.Response]) -> Optional[float]:
        if not response:
            return None
        retry_header = response.headers.get("Retry-After") or response.headers.get("retry-after")
        if retry_header:
            try:
                return min(float(retry_header), self.max_backoff)
            except (ValueError, TypeError):
                pass
        return None

    def _is_daily_quota_error(self, body_text: str) -> bool:
        text_lower = body_text.lower()
        daily_keywords = [
            "generaterequestsperdayperproject",
            "requests per day",
            "per day",
            "rpd",
            "daily quota",
            "quota exceeded for quota metric 'requests per day'"
        ]
        return any(k in text_lower for k in daily_keywords)

    async def _post_with_retry(self, url: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        if not self.api_key:
            err_msg = "GEMINI_API_KEY is not configured in environment settings."
            raise AIProviderConfigError(err_msg, provider="gemini", status_code=401)

        # Acquire rate limiter slot before sending API request
        limiter = get_gemini_rate_limiter()
        await limiter.acquire()

        headers = {
            "x-goog-api-key": self.api_key,
            "Content-Type": "application/json"
        }
        
        last_exception: Optional[Exception] = None
        attempt = 0
        total_attempts = self.max_retries + 1  # 1 initial + max_retries

        while attempt < total_attempts:
            attempt += 1
            t0 = time.time()
            resp: Optional[httpx.Response] = None
            try:
                async with httpx.AsyncClient() as client:
                    resp = await client.post(url, headers=headers, json=payload, timeout=self.timeout)
                    lat_ms = int((time.time() - t0) * 1000)

                    if resp.status_code == 200:
                        logger.info(f"Gemini API call succeeded (attempt {attempt}/{total_attempts}, {lat_ms}ms)")
                        return resp.json()

                    status = resp.status_code
                    body_text = self._sanitize_string(resp.text)
                    err_msg = f"Gemini API returned status HTTP {status}: {body_text}"

                    # Daily quota exhaustion check (RPD) - DO NOT RETRY
                    if status == 429 and self._is_daily_quota_error(body_text):
                        logger.error(f"Gemini daily quota exhausted (non-retryable): {err_msg}")
                        raise AIProviderUnavailableError(
                            f"Gemini daily/project quota exhausted (RPD limit reached): {err_msg}",
                            provider="gemini",
                            status_code=429
                        )

                    # 4xx Configuration Errors (400, 401, 403, 404, etc.) - DO NOT RETRY
                    if 400 <= status < 500 and status != 429:
                        logger.error(f"Non-retryable Gemini configuration error (HTTP {status}): {err_msg}")
                        raise AIProviderConfigError(err_msg, provider="gemini", status_code=status)

                    # 429 Temporary Rate-Limit or 5xx Transient Server Error - RETRYABLE
                    logger.warning(f"Transient Gemini API error (attempt {attempt}/{total_attempts}, HTTP {status}): {err_msg}")
                    last_exception = AIProviderUnavailableError(
                        err_msg, provider="gemini", status_code=503 if status >= 500 else 429
                    )

            except (httpx.TimeoutException, httpx.TransportError) as net_err:
                lat_ms = int((time.time() - t0) * 1000)
                sanitized_err = self._sanitize_string(str(net_err))
                err_msg = f"Gemini API network transport error: {sanitized_err}"
                logger.warning(f"Gemini network error (attempt {attempt}/{total_attempts}, {lat_ms}ms): {err_msg}")
                last_exception = AIProviderUnavailableError(err_msg, provider="gemini", status_code=503)

            except AIProviderConfigError:
                raise

            except AIProviderUnavailableError as pe:
                if 'status' in locals() and status == 429 and self._is_daily_quota_error(body_text if 'body_text' in locals() and body_text else ""):
                    raise
                last_exception = pe

            except AIProviderError as pe:
                last_exception = pe

            # Determine delay for retry if attempts remain
            if attempt < total_attempts:
                retry_after = self._get_retry_after(resp)
                if retry_after is not None:
                    backoff = retry_after
                else:
                    jitter = random.uniform(0.1, 0.5)
                    backoff = min(self.initial_backoff * (2 ** (attempt - 1)) + jitter, self.max_backoff)

                logger.info(f"Retrying Gemini API request in {backoff:.2f}s (attempt {attempt}/{total_attempts})...")
                await asyncio.sleep(backoff)

        # All retries exhausted
        logger.error(f"Gemini API retries exhausted ({total_attempts} attempts failed).")
        if last_exception:
            raise last_exception
        raise AIProviderUnavailableError("Gemini API is currently unavailable after multiple retries.", provider="gemini", status_code=503)

    async def generate_response(
        self,
        prompt: str,
        system_instruction: str,
        prompt_version: str = "v1.0.0"
    ) -> str:
        if not self.api_key:
            if settings.AI_FALLBACK_TO_MOCK:
                logger.warning("Gemini API key missing. Falling back to MockAIProvider.")
                return await MockAIProvider().generate_response(prompt, system_instruction, prompt_version)
            raise AIProviderConfigError("GEMINI_API_KEY is not configured in environment settings.", provider="gemini", status_code=401)
            
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{settings.AI_MODEL}:generateContent"
        payload = {
            "contents": [
                {"role": "user", "parts": [{"text": f"System: {system_instruction}\n\nUser Prompt:\n{prompt}"}]}
            ]
        }
        try:
            data = await self._post_with_retry(url, payload)
            return data["candidates"][0]["content"]["parts"][0]["text"]
        except Exception as e:
            if settings.AI_FALLBACK_TO_MOCK:
                logger.warning(f"Gemini API request failed, falling back to MockAIProvider: {e}")
                return await MockAIProvider().generate_response(prompt, system_instruction, prompt_version)
            raise

    async def generate_structured(
        self,
        prompt: str,
        system_instruction: str,
        response_schema: Dict[str, Any],
        prompt_version: str = "v1.0.0"
    ) -> Dict[str, Any]:
        if not self.api_key:
            if settings.AI_FALLBACK_TO_MOCK:
                return await MockAIProvider().generate_structured(prompt, system_instruction, response_schema, prompt_version)
            raise AIProviderConfigError("GEMINI_API_KEY is not configured in environment settings.", provider="gemini", status_code=401)
            
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{settings.AI_MODEL}:generateContent"
        payload = {
            "contents": [
                {"role": "user", "parts": [{"text": f"System: {system_instruction}\nRespond ONLY in JSON format matching this schema:\n{json.dumps(response_schema)}\n\nPrompt:\n{prompt}"}]}
            ],
            "generationConfig": {"responseMimeType": "application/json"}
        }
        try:
            data = await self._post_with_retry(url, payload)
            text = data["candidates"][0]["content"]["parts"][0]["text"]
            clean_text = text.strip()
            if clean_text.startswith("```"):
                lines = clean_text.splitlines()
                if lines[0].startswith("```"):
                    lines = lines[1:]
                if lines and lines[-1].startswith("```"):
                    lines = lines[:-1]
                clean_text = "\n".join(lines).strip()
            return json.loads(clean_text)
        except Exception as e:
            if settings.AI_FALLBACK_TO_MOCK:
                logger.warning(f"Gemini API request failed, falling back to MockAIProvider: {e}")
                return await MockAIProvider().generate_structured(prompt, system_instruction, response_schema, prompt_version)
            raise

class OpenAIProvider(AIProviderInterface):
    """OpenAI API Compatible Provider with strict error reporting."""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.OPENAI_API_KEY
        
    async def generate_response(
        self,
        prompt: str,
        system_instruction: str,
        prompt_version: str = "v1.0.0"
    ) -> str:
        if not self.api_key:
            if settings.AI_FALLBACK_TO_MOCK:
                return await MockAIProvider().generate_response(prompt, system_instruction, prompt_version)
            raise ValueError("OPENAI_API_KEY is not configured in environment settings.")
            
        url = "https://api.openai.com/v1/chat/completions"
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        payload = {
            "model": settings.AI_MODEL,
            "messages": [
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": prompt}
            ]
        }
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(url, headers=headers, json=payload, timeout=30.0)
                if resp.status_code == 200:
                    return resp.json()["choices"][0]["message"]["content"]
                else:
                    err_msg = f"OpenAI API call failed with status HTTP {resp.status_code}: {resp.text}"
                    logger.error(err_msg)
                    if settings.AI_FALLBACK_TO_MOCK:
                        return await MockAIProvider().generate_response(prompt, system_instruction, prompt_version)
                    raise RuntimeError(err_msg)
        except Exception as e:
            logger.error(f"OpenAI API request failed: {e}")
            if settings.AI_FALLBACK_TO_MOCK:
                return await MockAIProvider().generate_response(prompt, system_instruction, prompt_version)
            raise RuntimeError(f"OpenAI API request failed: {e}")

    async def generate_structured(
        self,
        prompt: str,
        system_instruction: str,
        response_schema: Dict[str, Any],
        prompt_version: str = "v1.0.0"
    ) -> Dict[str, Any]:
        if not self.api_key:
            if settings.AI_FALLBACK_TO_MOCK:
                return await MockAIProvider().generate_structured(prompt, system_instruction, response_schema, prompt_version)
            raise ValueError("OPENAI_API_KEY is not configured in environment settings.")
            
        url = "https://api.openai.com/v1/chat/completions"
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        payload = {
            "model": settings.AI_MODEL,
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": f"{system_instruction}\nRespond in JSON matching schema:\n{json.dumps(response_schema)}"},
                {"role": "user", "content": prompt}
            ]
        }
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(url, headers=headers, json=payload, timeout=30.0)
                if resp.status_code == 200:
                    return json.loads(resp.json()["choices"][0]["message"]["content"])
                else:
                    err_msg = f"OpenAI API call failed with status HTTP {resp.status_code}: {resp.text}"
                    logger.error(err_msg)
                    if settings.AI_FALLBACK_TO_MOCK:
                        return await MockAIProvider().generate_structured(prompt, system_instruction, response_schema, prompt_version)
                    raise RuntimeError(err_msg)
        except Exception as e:
            logger.error(f"OpenAI API request failed: {e}")
            if settings.AI_FALLBACK_TO_MOCK:
                return await MockAIProvider().generate_structured(prompt, system_instruction, response_schema, prompt_version)
            raise RuntimeError(f"OpenAI API request failed: {e}")


def get_ai_provider() -> AIProviderInterface:
    provider = settings.AI_PROVIDER.lower()
    if provider == "gemini":
        return GeminiProvider()
    elif provider == "openai":
        return OpenAIProvider()
    else:
        return MockAIProvider()
