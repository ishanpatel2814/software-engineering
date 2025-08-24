"""
OpenAI API client for generating educational scripts.
Compatible with openai>=1.0.0 (uses OpenAI().chat.completions.create).
"""
from __future__ import annotations

import os
import logging
from typing import Any, Dict, Optional, Union

logger = logging.getLogger("edu_video_pipeline")

try:
    # New-style client (openai>=1.x)
    from openai import OpenAI
except Exception as e:
    raise RuntimeError(
        "The OpenAI Python client (>=1.0.0) is required. Install/upgrade with:\n"
        "  pip install -U openai"
    ) from e


class OpenAIClient:
    """Client for the OpenAI API to generate educational scripts."""

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the OpenAI client.

        Args:
            config: Configuration dictionary
                Expected keys (if present):
                  - OPENAI_API_KEY (required)
                  - OPENAI_MODEL (default: 'gpt-4')
                  - OPENAI_MAX_TOKENS (default: 2000)
                  - OPENAI_TEMPERATURE (default: 0.7)
                  - OPENAI_BASE_URL (optional; for proxies/self-hosted gateways)
        """
        self.config = config
        self.api_key: str = (
            config.get("OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY") or ""
        )
        if not self.api_key:
            raise ValueError("OpenAI API key is required (OPENAI_API_KEY).")

        self.model: str = (
            config.get("OPENAI_MODEL")
            or os.getenv("OPENAI_MODEL")
            or "gpt-4"
        )
        self.max_tokens: int = int(config.get("OPENAI_MAX_TOKENS", 2000))
        self.temperature: float = float(config.get("OPENAI_TEMPERATURE", 0.7))
        self.base_url: Optional[str] = config.get("OPENAI_BASE_URL") or os.getenv("OPENAI_BASE_URL")

        # Initialize OpenAI client
        self.initialize_client()

    def initialize_client(self) -> None:
        """Initialize the OpenAI client with API key (and optional base URL)."""
        if self.base_url:
            self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)
        else:
            self.client = OpenAI(api_key=self.api_key)

        logger.info(f"Initialized OpenAI client with model: {self.model}")

    def generate_completion(self, prompt: str, **kwargs) -> Any:
        """
        Generate a completion from the OpenAI API (chat.completions).

        Args:
            prompt: The prompt to send to the API
            **kwargs: Additional parameters to pass to the API (e.g., top_p, stop)

        Returns:
            The raw response object from OpenAI (ChatCompletion).
            Use `handle_response()` to extract the message text.
        """
        try:
            # Default params (compatible with chat.completions.create)
            params: Dict[str, Any] = {
                "model": self.model,
                "temperature": self.temperature,
                "max_tokens": self.max_tokens,
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "You are an expert educational content creator specializing in "
                            "creating natural, conversational teaching scripts from educational materials."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
            }

            # Allow overrides via kwargs (e.g., presence_penalty, frequency_penalty, stop, top_p, etc.)
            params.update(kwargs or {})

            logger.debug(f"Calling OpenAI chat.completions with model: {params['model']}")
            resp = self.client.chat.completions.create(**params)
            return resp

        except Exception as e:
            logger.error(f"Error generating completion from OpenAI API: {e}")
            raise

    def handle_response(self, response: Union[Dict[str, Any], Any]) -> str:
        """
        Handle the response from the OpenAI API and return the assistant text.

        Accepts either:
          - the new ChatCompletion object (openai>=1.x), or
          - a dict with the old 'choices[0].message.content' layout
        """
        try:
            # New-style object (preferred)
            if hasattr(response, "choices") and response.choices:
                choice = response.choices[0]
                # choice.message.content should be a string
                msg = getattr(choice, "message", None)
                content = getattr(msg, "content", None) if msg else None
                if content:
                    return content.strip()

            # Fallback: dict-style (backwards compatibility)
            if isinstance(response, dict):
                choices = response.get("choices") or []
                if choices:
                    message = choices[0].get("message") or {}
                    content = message.get("content")
                    if isinstance(content, str):
                        return content.strip()

            raise ValueError("Invalid response format from OpenAI API")

        except Exception as e:
            logger.error(f"Error handling response from OpenAI API: {e}")
            raise
