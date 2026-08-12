import re


SENSITIVE_PATTERNS = [
    re.compile(r"sk-[A-Za-z0-9_-]+"),
    re.compile(r"Bearer\s+[A-Za-z0-9._-]+", re.IGNORECASE),
    re.compile(r"postgresql(?:\+asyncpg)?://[^\s]+", re.IGNORECASE),
    re.compile(r"redis://[^\s]+", re.IGNORECASE),
]


def sanitize_error_message(message: str, max_length: int = 1000) -> str:
    sanitized = message
    for pattern in SENSITIVE_PATTERNS:
        sanitized = pattern.sub("[REDACTED]", sanitized)
    return sanitized[:max_length]
