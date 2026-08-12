from fastapi import HTTPException, status


class AppException(HTTPException):
    def __init__(
        self,
        status_code: int,
        code: str,
        message: str,
    ):
        self.code = code
        super().__init__(
            status_code=status_code,
            detail={
                "success": False,
                "code": code,
                "message": message,
            },
        )


class NotFoundException(AppException):
    def __init__(self, resource: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            code=f"{resource.upper()}_NOT_FOUND",
            message=f"{resource} not found.",
        )


class DuplicateDocumentFileException(AppException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            code="DUPLICATE_DOCUMENT_FILE",
            message="The same document file has already been registered.",
        )


class AIProviderException(AppException):
    pass


class AIProviderAuthException(AIProviderException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_502_BAD_GATEWAY,
            code="AI_PROVIDER_AUTH_ERROR",
            message="AI provider authentication failed.",
        )


class AIProviderRateLimitException(AIProviderException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            code="AI_PROVIDER_RATE_LIMITED",
            message="AI provider rate limit exceeded.",
        )


class AIProviderQuotaException(AIProviderException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            code="AI_PROVIDER_QUOTA_EXCEEDED",
            message="AI provider quota has been exceeded.",
        )


class AIProviderTimeoutException(AIProviderException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            code="AI_PROVIDER_TIMEOUT",
            message="AI provider request timed out.",
        )


class AIProviderUnavailableException(AIProviderException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            code="AI_PROVIDER_UNAVAILABLE",
            message="AI provider is temporarily unavailable.",
        )


class AIProviderUnknownException(AIProviderException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_502_BAD_GATEWAY,
            code="AI_PROVIDER_ERROR",
            message="AI provider request failed.",
        )
