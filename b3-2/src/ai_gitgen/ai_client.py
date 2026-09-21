"""AI API client definitions."""

GROQ_API_ENDPOINT = "https://api.groq.com/openai/v1/chat/completions"
DEFAULT_MODEL = "openai/gpt-oss-20b"
QUALITY_MODEL = "openai/gpt-oss-120b"


class AIClientError(Exception):
    """Base exception for AI client failures."""


class MissingAPIKeyError(AIClientError):
    """Raised when the API key is missing."""


class GroqAIClient:
    """GroqCloud Chat Completions API client."""

    def __init__(
        self,
        api_key: str,
        endpoint: str = GROQ_API_ENDPOINT,
    ) -> None:
        if not api_key.strip():
            raise MissingAPIKeyError("AI_API_KEY 환경변수가 설정되지 않았습니다.")

        self._api_key = api_key
        self.endpoint = endpoint
