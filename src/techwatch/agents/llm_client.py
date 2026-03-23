"""OpenAI client wrapper with structured output support and tracing."""

from __future__ import annotations

import json
import logging
import time
from typing import Any, TypeVar

from openai import OpenAI
from pydantic import BaseModel

from techwatch.config import get_settings

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


class LlmClient:
    """Thin wrapper around OpenAI that enforces structured outputs.

    Every call is traced with timing and token usage for debugging.
    """

    def __init__(self) -> None:
        settings = get_settings()
        self._client = OpenAI(
            api_key=settings.openai_api_key.get_secret_value()
        )
        self._model = settings.openai_model
        self._temperature = settings.openai_temperature

    def structured_completion(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        response_model: type[T],
        tools: list[dict[str, Any]] | None = None,
        temperature: float | None = None,
    ) -> T:
        """Get a structured completion that validates against a Pydantic model.

        Uses OpenAI's response_format with json_schema for reliable JSON output.
        Falls back to JSON mode + manual parsing if structured outputs unavailable.
        """
        start = time.time()

        # Build the JSON schema for the response model
        schema = response_model.model_json_schema()

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        try:
            # Try structured output via response_format
            response = self._client.chat.completions.create(
                model=self._model,
                messages=messages,
                temperature=temperature or self._temperature,
                response_format={
                    "type": "json_schema",
                    "json_schema": {
                        "name": response_model.__name__,
                        "schema": schema,
                        "strict": True,
                    },
                },
                tools=tools,
            )
        except Exception:
            # Fallback to JSON mode
            logger.debug("Structured output unavailable, falling back to JSON mode")
            messages[0]["content"] += (
                f"\n\nRespond ONLY with valid JSON matching this schema:\n"
                f"{json.dumps(schema, indent=2)}"
            )
            response = self._client.chat.completions.create(
                model=self._model,
                messages=messages,
                temperature=temperature or self._temperature,
                response_format={"type": "json_object"},
                tools=tools,
            )

        elapsed = time.time() - start
        choice = response.choices[0]
        content = choice.message.content or "{}"

        usage = response.usage
        logger.info(
            "LLM call [%s] %.1fs | %d prompt + %d completion tokens",
            response_model.__name__,
            elapsed,
            usage.prompt_tokens if usage else 0,
            usage.completion_tokens if usage else 0,
        )

        # Validate against Pydantic model (strict)
        result = response_model.model_validate_json(content)
        return result

    def chat(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        temperature: float | None = None,
    ) -> str:
        """Simple unstructured chat completion."""
        response = self._client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=temperature or self._temperature,
        )
        return response.choices[0].message.content or ""

    def close(self) -> None:
        self._client.close()
