"""
BlackBox Monitoring - Sentry Integration

Error tracking with Sentry (free tier: 5,000 events/month).
Privacy-preserving: NO user content, transcripts, or audio.

Free Tier: https://sentry.io/pricing/
- 5,000 events/month
- 1 project
- 30-day retention
- Basic features

Usage:
    from backend.monitoring.sentry_setup import initialize_sentry

    # At app startup
    initialize_sentry(
        service_name="blackbox-api",
        environment="production"
    )
"""

import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.starlette import StarletteIntegration
from sentry_sdk.integrations.asyncio import AsyncioIntegration
from sentry_sdk.integrations.logging import LoggingIntegration
from sentry_sdk.integrations.redis import RedisIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
import os
import logging
from typing import Optional, Dict, Any

# ============================================================================
# Configuration
# ============================================================================

# Sentry DSN from environment
SENTRY_DSN = os.getenv("SENTRY_DSN")

# Environment
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")

# Release/version
APP_VERSION = os.getenv("APP_VERSION", "dev")

# Sample rate for performance monitoring (0.0 to 1.0)
# Start low to stay within free tier
TRACES_SAMPLE_RATE = float(os.getenv("SENTRY_TRACES_SAMPLE_RATE", "0.1"))

# Sample rate for profiling (0.0 to 1.0)
PROFILES_SAMPLE_RATE = float(os.getenv("SENTRY_PROFILES_SAMPLE_RATE", "0.0"))

# ============================================================================
# Privacy-Preserving Data Scrubbing
# ============================================================================

def before_send(event: Dict[str, Any], hint: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Filter and scrub sensitive data before sending to Sentry.

    This is the LAST LINE OF DEFENSE to prevent PII from reaching Sentry.

    Args:
        event: Sentry event data
        hint: Additional context

    Returns:
        Modified event or None to drop it
    """
    # Remove request body if it exists
    if "request" in event and "data" in event["request"]:
        event["request"]["data"] = "[REDACTED]"

    # Remove query parameters that might contain sensitive data
    if "request" in event and "query_string" in event["request"]:
        # Keep the structure but redact values
        event["request"]["query_string"] = "[REDACTED]"

    # Scrub user data
    if "user" in event:
        # Keep only hashed user ID
        user_data = event["user"]

        # Remove email, username, etc.
        scrubbed_user = {}
        if "id" in user_data:
            # Keep ID if it's already hashed
            if len(str(user_data["id"])) <= 16:  # Our hash length
                scrubbed_user["id"] = user_data["id"]

        event["user"] = scrubbed_user

    # Remove breadcrumbs with sensitive data
    if "breadcrumbs" in event:
        for breadcrumb in event["breadcrumbs"]:
            if "data" in breadcrumb:
                # Remove specific sensitive keys
                sensitive_keys = [
                    "password",
                    "api_key",
                    "secret",
                    "token",
                    "audio",
                    "transcript",
                    "prompt",
                    "response",
                ]
                for key in sensitive_keys:
                    if key in breadcrumb["data"]:
                        breadcrumb["data"][key] = "[REDACTED]"

    # Extra: scrub extra context
    if "extra" in event:
        sensitive_keys = [
            "audio_data",
            "transcript",
            "prompt",
            "response",
            "api_key",
            "password",
        ]
        for key in sensitive_keys:
            if key in event["extra"]:
                event["extra"][key] = "[REDACTED]"

    return event

def before_breadcrumb(crumb: Dict[str, Any], hint: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Filter breadcrumbs before adding to Sentry.

    Args:
        crumb: Breadcrumb data
        hint: Additional context

    Returns:
        Modified breadcrumb or None to drop it
    """
    # Drop HTTP request bodies
    if crumb.get("category") == "httplib" and "data" in crumb:
        if "body" in crumb["data"]:
            crumb["data"]["body"] = "[REDACTED]"

    return crumb

# ============================================================================
# Sentry Initialization
# ============================================================================

def initialize_sentry(
    service_name: str = "blackbox",
    environment: str = ENVIRONMENT,
    dsn: Optional[str] = None,
    enable_tracing: bool = True,
    enable_profiling: bool = False,
) -> bool:
    """
    Initialize Sentry error tracking.

    Args:
        service_name: Name of the service (api, worker, etc.)
        environment: Environment name (development, staging, production)
        dsn: Sentry DSN (defaults to SENTRY_DSN env var)
        enable_tracing: Enable performance monitoring
        enable_profiling: Enable profiling (uses more quota)

    Returns:
        True if initialized successfully, False otherwise
    """
    dsn = dsn or SENTRY_DSN

    if not dsn:
        logging.warning("Sentry DSN not configured. Error tracking disabled.")
        return False

    # Skip in development unless explicitly enabled
    if environment == "development" and not os.getenv("SENTRY_ENABLE_IN_DEV"):
        logging.info("Skipping Sentry in development environment")
        return False

    try:
        sentry_sdk.init(
            dsn=dsn,
            # Release tracking
            release=f"{service_name}@{APP_VERSION}",
            environment=environment,
            # Integrations
            integrations=[
                FastApiIntegration(),
                StarletteIntegration(),
                AsyncioIntegration(),
                LoggingIntegration(
                    level=logging.INFO,  # Capture info and above
                    event_level=logging.ERROR,  # Create events for errors
                ),
                RedisIntegration(),
                SqlalchemyIntegration(),
            ],
            # Sampling rates
            traces_sample_rate=TRACES_SAMPLE_RATE if enable_tracing else 0.0,
            profiles_sample_rate=PROFILES_SAMPLE_RATE if enable_profiling else 0.0,
            # Privacy functions
            before_send=before_send,
            before_breadcrumb=before_breadcrumb,
            # Tags
            default_integrations=True,
            # Send default PII (we'll filter it ourselves)
            send_default_pii=False,
            # Max breadcrumbs
            max_breadcrumbs=50,
            # Attach stacktrace to messages
            attach_stacktrace=True,
            # Debug mode
            debug=False,
        )

        # Set service tag
        sentry_sdk.set_tag("service", service_name)

        logging.info(
            f"Sentry initialized for {service_name} in {environment} environment"
        )
        return True

    except Exception as e:
        logging.error(f"Failed to initialize Sentry: {e}")
        return False

# ============================================================================
# Helper Functions
# ============================================================================

def capture_exception(
    error: Exception,
    context: Optional[Dict[str, Any]] = None,
    level: str = "error",
    tags: Optional[Dict[str, str]] = None,
):
    """
    Manually capture an exception to Sentry.

    Args:
        error: Exception to capture
        context: Additional context (will be scrubbed)
        level: Severity level (fatal, error, warning, info, debug)
        tags: Additional tags
    """
    with sentry_sdk.push_scope() as scope:
        # Set level
        scope.level = level

        # Add tags
        if tags:
            for key, value in tags.items():
                scope.set_tag(key, value)

        # Add context
        if context:
            for key, value in context.items():
                scope.set_extra(key, value)

        # Capture
        sentry_sdk.capture_exception(error)

def capture_message(
    message: str,
    level: str = "info",
    tags: Optional[Dict[str, str]] = None,
    context: Optional[Dict[str, Any]] = None,
):
    """
    Manually capture a message to Sentry.

    Args:
        message: Message to capture
        level: Severity level
        tags: Additional tags
        context: Additional context
    """
    with sentry_sdk.push_scope() as scope:
        # Set level
        scope.level = level

        # Add tags
        if tags:
            for key, value in tags.items():
                scope.set_tag(key, value)

        # Add context
        if context:
            for key, value in context.items():
                scope.set_extra(key, value)

        # Capture
        sentry_sdk.capture_message(message, level=level)

def set_user_context(user_id_hash: str):
    """
    Set user context (hashed ID only).

    Args:
        user_id_hash: Hashed user ID (NOT the original ID!)
    """
    sentry_sdk.set_user({"id": user_id_hash})

def add_breadcrumb(
    message: str,
    category: str = "default",
    level: str = "info",
    data: Optional[Dict[str, Any]] = None,
):
    """
    Add a breadcrumb for debugging.

    Args:
        message: Breadcrumb message
        category: Category (http, db, ui, etc.)
        level: Severity level
        data: Additional data (will be scrubbed)
    """
    sentry_sdk.add_breadcrumb(
        message=message,
        category=category,
        level=level,
        data=data or {},
    )

# ============================================================================
# FastAPI Integration Example
# ============================================================================

"""
Example FastAPI integration:

from fastapi import FastAPI, Request
from backend.monitoring.sentry_setup import (
    initialize_sentry,
    capture_exception,
    set_user_context,
    add_breadcrumb
)
from backend.monitoring.logging import hash_user_id

app = FastAPI()

@app.on_event("startup")
async def startup_event():
    # Initialize Sentry
    initialize_sentry(
        service_name="blackbox-api",
        environment="production"
    )

@app.middleware("http")
async def sentry_middleware(request: Request, call_next):
    # Add breadcrumb for request
    add_breadcrumb(
        message=f"{request.method} {request.url.path}",
        category="http",
        level="info",
        data={
            "method": request.method,
            "url": request.url.path,
            "query": "[REDACTED]",  # Don't log query params
        }
    )

    response = await call_next(request)
    return response

@app.post("/api/voice/command")
async def process_voice_command(user_id: str, command: str):
    # Set user context (hashed)
    set_user_context(hash_user_id(user_id))

    try:
        result = process_command(command)
        return result

    except ValueError as e:
        # Capture specific error
        capture_exception(
            e,
            context={
                "feature": "voice_command",
                "command_length": len(command)  # Length, not content!
            },
            level="warning",
            tags={
                "error_type": "validation_error",
                "service": "voice"
            }
        )
        raise

    except Exception as e:
        # Capture unexpected error
        capture_exception(
            e,
            context={
                "feature": "voice_command"
            },
            level="error",
            tags={
                "error_type": "processing_error",
                "service": "voice"
            }
        )
        raise
"""

# ============================================================================
# Testing
# ============================================================================

if __name__ == "__main__":
    # Test Sentry initialization (requires SENTRY_DSN env var)
    success = initialize_sentry(
        service_name="blackbox-test",
        environment="development",
        enable_tracing=True,
    )

    if success:
        # Test error capture
        try:
            raise ValueError("Test error for Sentry")
        except Exception as e:
            capture_exception(
                e,
                context={"test": "value"},
                tags={"test_tag": "test_value"},
            )

        # Test message capture
        capture_message(
            "Test message for Sentry",
            level="info",
            tags={"test": "true"},
        )

        print("Sentry test complete. Check your Sentry dashboard.")
    else:
        print("Sentry not initialized. Check SENTRY_DSN environment variable.")
