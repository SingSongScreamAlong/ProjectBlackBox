"""
BlackBox Monitoring - Structured JSON Logging

Privacy-preserving structured logging for Loki.
NO user content, transcripts, or audio - only event metadata.

Usage:
    from backend.monitoring.logging import get_logger, add_correlation_id

    logger = get_logger(__name__)
    logger.info("User logged in", user_id_hash=hash_user_id(user_id))

    # With correlation ID for request tracing
    correlation_id = add_correlation_id()
    logger.info("Processing request", correlation_id=correlation_id)
"""

import logging
import json
import sys
import os
import hashlib
import uuid
from datetime import datetime
from typing import Dict, Any, Optional
from contextvars import ContextVar

# ============================================================================
# Configuration
# ============================================================================

# Secret salt for hashing user IDs (set via environment variable)
USER_ID_SALT = os.getenv("USER_ID_HASH_SALT", "default-salt-change-in-production")

# Log level from environment
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

# Service name
SERVICE_NAME = os.getenv("SERVICE_NAME", "blackbox")

# Environment
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")

# ============================================================================
# Context Variables for Request Tracing
# ============================================================================

# Correlation ID for tracing requests across services
correlation_id_var: ContextVar[Optional[str]] = ContextVar('correlation_id', default=None)

# User ID hash for user-specific log filtering
user_id_hash_var: ContextVar[Optional[str]] = ContextVar('user_id_hash', default=None)

# ============================================================================
# Utility Functions
# ============================================================================

def hash_user_id(user_id: str) -> str:
    """
    Hash user ID for privacy-preserving logging.

    Args:
        user_id: Original user ID

    Returns:
        SHA256 hash of user_id + salt (first 16 chars)
    """
    if not user_id:
        return "anonymous"

    combined = f"{user_id}{USER_ID_SALT}"
    return hashlib.sha256(combined.encode()).hexdigest()[:16]

def generate_correlation_id() -> str:
    """Generate a unique correlation ID for request tracing."""
    return str(uuid.uuid4())

def set_correlation_id(correlation_id: str):
    """Set correlation ID in context."""
    correlation_id_var.set(correlation_id)

def get_correlation_id() -> Optional[str]:
    """Get correlation ID from context."""
    return correlation_id_var.get()

def add_correlation_id() -> str:
    """Add a new correlation ID to context and return it."""
    correlation_id = generate_correlation_id()
    set_correlation_id(correlation_id)
    return correlation_id

def set_user_id_hash(user_id: str):
    """Set hashed user ID in context."""
    hashed = hash_user_id(user_id)
    user_id_hash_var.set(hashed)

def get_user_id_hash() -> Optional[str]:
    """Get hashed user ID from context."""
    return user_id_hash_var.get()

# ============================================================================
# JSON Formatter
# ============================================================================

class JSONFormatter(logging.Formatter):
    """
    Custom JSON formatter for structured logging.

    Outputs logs in JSON format compatible with Loki and other log aggregators.
    """

    def format(self, record: logging.LogRecord) -> str:
        """
        Format log record as JSON.

        Args:
            record: Log record

        Returns:
            JSON string
        """
        # Base log structure
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "service": SERVICE_NAME,
            "environment": ENVIRONMENT,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Add correlation ID if available
        correlation_id = get_correlation_id()
        if correlation_id:
            log_data["correlation_id"] = correlation_id

        # Add user ID hash if available
        user_id_hash = get_user_id_hash()
        if user_id_hash:
            log_data["user_id_hash"] = user_id_hash

        # Add extra fields from record
        if hasattr(record, "extra_fields"):
            log_data["context"] = record.extra_fields

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] else None,
                "message": str(record.exc_info[1]) if record.exc_info[1] else None,
                "traceback": self.formatException(record.exc_info) if record.exc_info else None,
            }

        # Add file location
        log_data["location"] = {
            "file": record.pathname,
            "line": record.lineno,
            "function": record.funcName,
        }

        return json.dumps(log_data)

# ============================================================================
# Custom Logger Adapter
# ============================================================================

class StructuredLogger(logging.LoggerAdapter):
    """
    Logger adapter that adds structured context to all log messages.

    Usage:
        logger = StructuredLogger(logging.getLogger(__name__))
        logger.info("User action", action="login", user_id_hash=hash_user_id(user_id))
    """

    def process(self, msg, kwargs):
        """
        Process log message and add structured fields.

        Args:
            msg: Log message
            kwargs: Keyword arguments

        Returns:
            Tuple of (message, kwargs)
        """
        # Extract extra fields
        extra_fields = {}

        # Move custom fields to extra_fields
        for key in list(kwargs.keys()):
            if key not in ['exc_info', 'stack_info', 'stacklevel', 'extra']:
                extra_fields[key] = kwargs.pop(key)

        # Add to extra
        if 'extra' not in kwargs:
            kwargs['extra'] = {}

        kwargs['extra']['extra_fields'] = extra_fields

        return msg, kwargs

# ============================================================================
# Logger Setup
# ============================================================================

def setup_logging(
    service_name: str = SERVICE_NAME,
    log_level: str = LOG_LEVEL,
    log_file: Optional[str] = None
):
    """
    Setup structured JSON logging.

    Args:
        service_name: Name of the service
        log_level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional log file path
    """
    global SERVICE_NAME
    SERVICE_NAME = service_name

    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level))

    # Remove existing handlers
    root_logger.handlers = []

    # JSON formatter
    formatter = JSONFormatter()

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # File handler (if specified)
    if log_file:
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

    # Silence noisy third-party loggers
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("websockets").setLevel(logging.WARNING)

def get_logger(name: str) -> StructuredLogger:
    """
    Get a structured logger for a module.

    Args:
        name: Logger name (typically __name__)

    Returns:
        StructuredLogger instance
    """
    logger = logging.getLogger(name)
    return StructuredLogger(logger, {})

# ============================================================================
# FastAPI Integration
# ============================================================================

"""
Example FastAPI integration:

from fastapi import FastAPI, Request
from backend.monitoring.logging import (
    setup_logging,
    get_logger,
    add_correlation_id,
    set_user_id_hash,
    hash_user_id
)

# Setup logging at app startup
app = FastAPI()

@app.on_event("startup")
async def startup_event():
    setup_logging(
        service_name="blackbox-api",
        log_level="INFO",
        log_file="/app/logs/api-{date}.log"  # Rotated by date
    )

# Middleware to add correlation ID to all requests
@app.middleware("http")
async def logging_middleware(request: Request, call_next):
    # Generate correlation ID
    correlation_id = add_correlation_id()

    # Add to response headers
    response = await call_next(request)
    response.headers["X-Correlation-ID"] = correlation_id

    return response

# Use in endpoints
logger = get_logger(__name__)

@app.post("/api/voice/command")
async def process_voice_command(user_id: str, command: str):
    # Set user context (hashed)
    set_user_id_hash(user_id)

    # Log without sensitive data
    logger.info(
        "Processing voice command",
        event_type="voice_command_received",
        command_length=len(command)  # Length, not content!
    )

    try:
        result = process_command(command)

        logger.info(
            "Voice command processed successfully",
            event_type="voice_command_success",
            processing_time_ms=result.duration
        )

        return result

    except Exception as e:
        logger.error(
            "Voice command processing failed",
            event_type="voice_command_error",
            error_type=type(e).__name__,
            exc_info=True  # Includes stack trace
        )
        raise
"""

# ============================================================================
# Privacy-Safe Log Filters
# ============================================================================

class PIIFilter(logging.Filter):
    """
    Filter to prevent accidental logging of PII/sensitive data.

    Blocks logs containing suspicious patterns.
    """

    # Patterns that might indicate PII
    SUSPICIOUS_PATTERNS = [
        "email",
        "password",
        "ssn",
        "credit_card",
        "api_key",
        "secret",
        "token",
    ]

    def filter(self, record: logging.LogRecord) -> bool:
        """
        Filter log record.

        Args:
            record: Log record

        Returns:
            True to allow, False to block
        """
        message = record.getMessage().lower()

        # Check for suspicious patterns
        for pattern in self.SUSPICIOUS_PATTERNS:
            if pattern in message:
                # Log a warning about blocked log
                print(
                    f"WARNING: Blocked log that may contain PII (pattern: {pattern})",
                    file=sys.stderr
                )
                return False

        return True

def add_pii_filter():
    """Add PII filter to all loggers."""
    pii_filter = PIIFilter()
    for handler in logging.root.handlers:
        handler.addFilter(pii_filter)

# ============================================================================
# Example Usage
# ============================================================================

if __name__ == "__main__":
    # Setup logging
    setup_logging(
        service_name="blackbox-example",
        log_level="DEBUG",
        log_file="logs/example.log"
    )

    # Get logger
    logger = get_logger(__name__)

    # Add correlation ID
    correlation_id = add_correlation_id()
    print(f"Correlation ID: {correlation_id}")

    # Set user context
    set_user_id_hash("user_12345")

    # Log various events
    logger.debug("Debug message", detail="extra info")
    logger.info("User action", action="login", method="oauth")
    logger.warning("Rate limit approaching", remaining_requests=10)

    # Log error with exception
    try:
        raise ValueError("Something went wrong")
    except Exception:
        logger.error("Error occurred", error_context="processing data", exc_info=True)

    # Log without correlation ID
    correlation_id_var.set(None)
    user_id_hash_var.set(None)

    logger.info("System event", event_type="startup_complete")
