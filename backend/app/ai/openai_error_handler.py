from openai import (
    APIConnectionError,
    APIError,
    APITimeoutError,
    AuthenticationError,
    InternalServerError,
    RateLimitError,
)

from app.common.exceptions import (
    AIProviderAuthException,
    AIProviderQuotaException,
    AIProviderRateLimitException,
    AIProviderTimeoutException,
    AIProviderUnavailableException,
    AIProviderUnknownException,
)


def handle_openai_error(exc: Exception) -> None:
    if isinstance(exc, AuthenticationError):
        raise AIProviderAuthException() from exc

    if isinstance(exc, APITimeoutError):
        raise AIProviderTimeoutException() from exc

    if isinstance(exc, RateLimitError):
        if getattr(exc, "code", None) == "insufficient_quota":
            raise AIProviderQuotaException() from exc

        body = getattr(exc, "body", None)
        if isinstance(body, dict):
            error = body.get("error", body)
            if isinstance(error, dict) and error.get("code") == "insufficient_quota":
                raise AIProviderQuotaException() from exc

        raise AIProviderRateLimitException() from exc

    if isinstance(exc, (InternalServerError, APIConnectionError)):
        raise AIProviderUnavailableException() from exc

    if isinstance(exc, APIError):
        raise AIProviderUnknownException() from exc

    raise AIProviderUnknownException() from exc
