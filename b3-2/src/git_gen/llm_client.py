"""LLM API client definitions."""

from __future__ import annotations

import json
from typing import Any

import requests

DEFAULT_MODEL = "openai/gpt-oss-20b"


class LLMClientError(Exception):
    """Base exception for LLM client failures."""


class MissingAPIKeyError(LLMClientError):
    """Raised when the API key is missing."""


class MissingAPIEndpointError(LLMClientError):
    """Raised when the API endpoint is missing."""


class AuthenticationError(LLMClientError):
    """Raised when API authentication fails."""


class RateLimitError(LLMClientError):
    """Raised when the API rate limit is exceeded."""


class NetworkError(LLMClientError):
    """Raised when a network request fails."""


class InvalidResponseError(LLMClientError):
    """Raised when the API response cannot be parsed."""


class APIRequestError(LLMClientError):
    """Raised for other API request failures."""


class LLMClient:
    """LLM Chat Completions API client."""

    def __init__(
        self,
        api_key: str,
        endpoint: str,
        timeout: float = 30.0,
        session: requests.Session | None = None,
    ) -> None:
        if not api_key.strip():
            raise MissingAPIKeyError(
                "LLM_API_KEY 환경변수가 설정되지 않았습니다."
            )
        if not endpoint.strip():
            raise MissingAPIEndpointError(
                "LLM_API_ENDPOINT 환경변수가 설정되지 않았습니다."
            )

        self._api_key = api_key
        self.endpoint = endpoint
        self.timeout = timeout
        self._session = session or requests.Session()
        self.request_count = 0

    def generate(
        self,
        *,
        messages: list[dict[str, str]],
        schema_name: str,
        schema: dict[str, Any],
        model: str,
        temperature: float,
        max_tokens: int,
    ) -> dict[str, Any]:
        """Request one schema-constrained chat completion."""
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_completion_tokens": max_tokens,
            "response_format": {
                "type": "json_schema",
                "json_schema": {
                    "name": schema_name,
                    "strict": True,
                    "schema": schema,
                },
            },
        }
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }

        self.request_count += 1

        try:
            response = self._session.post(
                self.endpoint,
                headers=headers,
                json=payload,
                timeout=self.timeout,
            )
        except requests.RequestException as error:
            raise NetworkError(
                f"LLM API 네트워크 오류: {error}"
            ) from error

        if response.status_code in {401, 403}:
            raise AuthenticationError(
                "LLM API 인증에 실패했습니다. LLM_API_KEY를 확인해 주세요."
            )

        if response.status_code == 429:
            raise RateLimitError(
                "LLM API 요청 한도를 초과했습니다. 잠시 후 다시 시도해 주세요."
            )

        if response.status_code >= 400:
            message = self._extract_error_message(response)
            raise APIRequestError(
                f"LLM API 요청 실패 (HTTP {response.status_code}): {message}"
            )

        try:
            response_data = response.json()
            content = response_data["choices"][0]["message"]["content"]
            result = json.loads(content) if isinstance(content, str) else content
        except (ValueError, KeyError, IndexError, TypeError) as error:
            raise InvalidResponseError(
                "LLM API 응답 JSON 형식이 올바르지 않습니다."
            ) from error

        if not isinstance(result, dict):
            raise InvalidResponseError(
                "LLM API 응답 JSON 형식이 올바르지 않습니다."
            )

        return result

    @staticmethod
    def _extract_error_message(response: requests.Response) -> str:
        try:
            payload = response.json()
            message = payload.get("error", {}).get("message")
            if isinstance(message, str) and message:
                return message[:200]
        except (ValueError, AttributeError):
            pass

        return "알 수 없는 오류"
