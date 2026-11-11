"""
Logging filter for sanitizing credentials, API keys, and authorization headers.
"""
import re
import logging

SECRET_PATTERNS = [
    re.compile(r'sk-[a-zA-Z0-9_-]{20,}', re.IGNORECASE),
    re.compile(r'AIza[a-zA-Z0-9_-]{35}', re.IGNORECASE),
    re.compile(r'sk-ant-[a-zA-Z0-9_-]{20,}', re.IGNORECASE),
    re.compile(r'together_[a-zA-Z0-9_-]{20,}', re.IGNORECASE),
    re.compile(r'Bearer\s+[a-zA-Z0-9_.-]{20,}', re.IGNORECASE),
]

class LogSanitizerFilter(logging.Filter):
    """Filters API keys and bearer tokens from application logs."""

    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            for pattern in SECRET_PATTERNS:
                record.msg = pattern.sub("[REDACTED_API_KEY]", record.msg)
        return True

def configure_sanitized_logging():
    """Attaches sanitizer filter to root logger."""
    root = logging.getLogger()
    sanitizer = LogSanitizerFilter()
    for handler in root.handlers:
        handler.addFilter(sanitizer)
