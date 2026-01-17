"""
LLM Service for Clinical Intelligence Platform.
Unified interface for Gemini and Azure OpenAI with rate limiting and retries.
"""
import asyncio
import logging
import os
import json
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass
from enum import Enum

import google.generativeai as genai
from openai import AsyncAzureOpenAI
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from app.config import settings
from app.exceptions import LLMServiceError

logger = logging.getLogger(__name__)


class LLMProvider(str, Enum):
    """Available LLM providers."""
    GEMINI = "gemini"
    AZURE_OPENAI = "azure_openai"


@dataclass
class LLMResponse:
    """Response from LLM call."""
    content: str
    model: str
    provider: LLMProvider
    usage: Dict[str, int]
    latency_ms: float


class LLMService:
    """
    Unified LLM interface for Gemini and Azure OpenAI.

    Features:
    - Automatic provider selection based on model name
    - Rate limiting and retry logic
    - Token usage tracking
    - Consensus mode for critical decisions
    """

    # Model mappings - primary: gemini-3-pro-preview
    GEMINI_MODELS = {
        "gemini-3-pro-preview": "gemini-3-pro-preview",
        "gemini-3-pro": "gemini-3-pro-preview",
        "gemini-3-flash-preview": "gemini-3-flash-preview",
        "gemini-3-flash": "gemini-3-flash-preview",
        "gemini-2.5-pro": "gemini-2.5-pro",
        "gemini-2.5-flash": "gemini-2.5-flash",
        "gemini-2.0-flash": "gemini-2.0-flash",
    }

    MAX_TOKENS = {
        "gemini-3-pro-preview": 65536,
        "gemini-3-pro": 65536,
        "gemini-3-flash": 65536,
        "gemini-2.5-pro": 65536,
        "gemini-2.5-flash": 65536,
        "gemini-2.0-flash": 8192,
        "gpt-5-mini": 16384,
        "gpt-4": 16384,
        "gpt-4o": 16384,
    }

    def __init__(self):
        """Initialize LLM service with API keys from environment."""
        # Configure Gemini
        self.gemini_api_key = settings.gemini_api_key
        if self.gemini_api_key:
            genai.configure(api_key=self.gemini_api_key)
            logger.info("Gemini API configured")

        # Configure Azure OpenAI
        self.azure_client: Optional[AsyncAzureOpenAI] = None
        if settings.azure_openai_api_key and settings.azure_openai_endpoint:
            self.azure_client = AsyncAzureOpenAI(
                api_key=settings.azure_openai_api_key,
                api_version=settings.azure_openai_api_version,
                azure_endpoint=settings.azure_openai_endpoint,
            )
            logger.info("Azure OpenAI client configured")

        # Usage tracking
        self.total_input_tokens = 0
        self.total_output_tokens = 0

    def _get_provider(self, model: str) -> LLMProvider:
        """Determine provider based on model name."""
        if model.startswith("gemini") or model in self.GEMINI_MODELS:
            return LLMProvider.GEMINI
        elif model.startswith("gpt"):
            return LLMProvider.AZURE_OPENAI
        else:
            # Default to Gemini
            return LLMProvider.GEMINI

    def _get_max_tokens(self, model: str) -> int:
        """Get maximum output tokens for model."""
        for prefix, max_tokens in self.MAX_TOKENS.items():
            if model.startswith(prefix) or model == prefix:
                return max_tokens
        return 8192  # Default

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=30),
        retry=retry_if_exception_type((Exception,)),
        reraise=True
    )
    async def _call_gemini(
        self,
        prompt: str,
        model: str,
        max_tokens: int,
        temperature: float,
        response_format: Optional[str] = None,
    ) -> LLMResponse:
        """Call Gemini API with retry logic."""
        import time
        start_time = time.time()

        # Resolve model name
        model_id = self.GEMINI_MODELS.get(model, model)

        # Configure generation
        generation_config = genai.GenerationConfig(
            max_output_tokens=max_tokens,
            temperature=temperature,
        )

        # Create model instance
        gemini_model = genai.GenerativeModel(
            model_name=model_id,
            generation_config=generation_config,
        )

        # Generate response
        response = await asyncio.to_thread(
            gemini_model.generate_content,
            prompt
        )

        latency_ms = (time.time() - start_time) * 1000

        # Extract usage if available
        usage = {}
        if hasattr(response, 'usage_metadata'):
            usage = {
                "input_tokens": getattr(response.usage_metadata, 'prompt_token_count', 0),
                "output_tokens": getattr(response.usage_metadata, 'candidates_token_count', 0),
            }
            self.total_input_tokens += usage.get("input_tokens", 0)
            self.total_output_tokens += usage.get("output_tokens", 0)

        return LLMResponse(
            content=response.text,
            model=model_id,
            provider=LLMProvider.GEMINI,
            usage=usage,
            latency_ms=latency_ms,
        )

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=30),
        retry=retry_if_exception_type((Exception,)),
        reraise=True
    )
    async def _call_azure(
        self,
        prompt: str,
        max_tokens: int,
        temperature: float,
        response_format: Optional[str] = None,
    ) -> LLMResponse:
        """Call Azure OpenAI API with retry logic."""
        import time
        start_time = time.time()

        if not self.azure_client:
            raise ValueError("Azure OpenAI client not configured")

        # Build messages
        messages = [{"role": "user", "content": prompt}]

        # Call API
        response = await self.azure_client.chat.completions.create(
            model=settings.azure_openai_deployment,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
        )

        latency_ms = (time.time() - start_time) * 1000

        # Extract usage
        usage = {
            "input_tokens": response.usage.prompt_tokens if response.usage else 0,
            "output_tokens": response.usage.completion_tokens if response.usage else 0,
        }
        self.total_input_tokens += usage.get("input_tokens", 0)
        self.total_output_tokens += usage.get("output_tokens", 0)

        return LLMResponse(
            content=response.choices[0].message.content,
            model=settings.azure_openai_deployment,
            provider=LLMProvider.AZURE_OPENAI,
            usage=usage,
            latency_ms=latency_ms,
        )

    async def generate(
        self,
        prompt: str,
        model: str = "gemini-3-pro-preview",
        max_tokens: Optional[int] = None,
        temperature: float = 0.1,
        response_format: Optional[str] = None,
    ) -> str:
        """
        Generate response from specified model.

        Args:
            prompt: The prompt to send to the LLM
            model: Model identifier (gemini-3-pro-preview, gpt-5-mini, etc.)
            max_tokens: Maximum output tokens (uses model default if None)
            temperature: Sampling temperature (0.0-1.0)
            response_format: Optional format hint ("json" for JSON output)

        Returns:
            Generated text response
        """
        provider = self._get_provider(model)

        if max_tokens is None:
            max_tokens = self._get_max_tokens(model)

        # Check if we have valid credentials for the provider
        if provider == LLMProvider.GEMINI and not self.gemini_api_key:
            logger.error("Gemini API key not configured")
            raise LLMServiceError(
                "Gemini API key not configured. "
                "Set GEMINI_API_KEY environment variable."
            )
        if provider == LLMProvider.AZURE_OPENAI and not self.azure_client:
            logger.error("Azure OpenAI not configured")
            raise LLMServiceError(
                "Azure OpenAI not configured. "
                "Set AZURE_OPENAI_API_KEY, AZURE_OPENAI_ENDPOINT environment variables."
            )

        logger.debug(f"Calling {provider.value} model {model} with {len(prompt)} chars")

        if provider == LLMProvider.GEMINI:
            response = await self._call_gemini(
                prompt, model, max_tokens, temperature, response_format
            )
        elif provider == LLMProvider.AZURE_OPENAI:
            response = await self._call_azure(
                prompt, max_tokens, temperature, response_format
            )
        else:
            raise ValueError(f"Unknown provider: {provider}")

        logger.debug(
            f"LLM response: {response.usage.get('output_tokens', 0)} tokens, "
            f"{response.latency_ms:.0f}ms"
        )

        return response.content

    async def generate_json(
        self,
        prompt: str,
        model: str = "gemini-3-pro-preview",
        max_tokens: Optional[int] = None,
        temperature: float = 0.0,
    ) -> Dict[str, Any]:
        """
        Generate JSON response from LLM.

        Args:
            prompt: Prompt that should result in JSON output
            model: Model identifier
            max_tokens: Maximum output tokens
            temperature: Sampling temperature

        Returns:
            Parsed JSON dictionary
        """
        response = await self.generate(
            prompt=prompt,
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            response_format="json",
        )

        # Try to parse JSON from response
        try:
            # Handle markdown code blocks
            if "```json" in response:
                start = response.find("```json") + 7
                end = response.find("```", start)
                response = response[start:end].strip()
            elif "```" in response:
                start = response.find("```") + 3
                end = response.find("```", start)
                response = response[start:end].strip()

            return json.loads(response)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            logger.debug(f"Response was: {response[:500]}...")
            raise ValueError(f"LLM response was not valid JSON: {e}")

    async def consensus(
        self,
        prompt: str,
        models: List[str] = None,
        temperature: float = 0.1,
    ) -> Tuple[str, float]:
        """
        Get responses from multiple models for consensus.

        Args:
            prompt: The prompt to send
            models: List of models to query (default: gemini + azure)
            temperature: Sampling temperature

        Returns:
            Tuple of (consensus_response, confidence_score)
        """
        if models is None:
            models = ["gemini-3-pro-preview"]
            if self.azure_client:
                models.append("gpt-5-mini")  # Azure OpenAI fallback

        # Get responses in parallel
        responses = await asyncio.gather(*[
            self.generate(prompt, model=m, temperature=temperature)
            for m in models
        ], return_exceptions=True)

        # Filter out failures
        valid_responses = [
            r for r in responses
            if not isinstance(r, Exception)
        ]

        if not valid_responses:
            raise RuntimeError("All LLM calls failed")

        if len(valid_responses) == 1:
            return valid_responses[0], 0.5  # Single response, uncertain

        # For now, return first response with confidence based on agreement
        # TODO: Implement semantic similarity comparison
        confidence = len(valid_responses) / len(models)
        return valid_responses[0], confidence

    def get_usage_stats(self) -> Dict[str, int]:
        """Get cumulative token usage statistics."""
        return {
            "total_input_tokens": self.total_input_tokens,
            "total_output_tokens": self.total_output_tokens,
            "total_tokens": self.total_input_tokens + self.total_output_tokens,
        }

    def reset_usage_stats(self):
        """Reset token usage counters."""
        self.total_input_tokens = 0
        self.total_output_tokens = 0


# Singleton instance
_llm_service: Optional[LLMService] = None


def get_llm_service() -> LLMService:
    """Get singleton LLM service instance."""
    global _llm_service
    if _llm_service is None:
        _llm_service = LLMService()
    return _llm_service
