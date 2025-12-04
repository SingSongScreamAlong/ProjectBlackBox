"""
BlackBox Monitoring - Prometheus Metrics

Privacy-preserving metrics for system health monitoring.
NO user content, transcripts, or audio - only counts, durations, and status codes.

Usage:
    from backend.monitoring.metrics import metrics, track_request, track_job

    # In FastAPI
    @app.middleware("http")
    async def metrics_middleware(request: Request, call_next):
        return await track_request(request, call_next)

    # In worker
    with track_job("process_audio"):
        # ... do work
        pass
"""

from prometheus_client import (
    Counter,
    Histogram,
    Gauge,
    Summary,
    Info,
    generate_latest,
    CONTENT_TYPE_LATEST,
)
from functools import wraps
import time
import hashlib
import os
from typing import Optional, Callable
from contextlib import contextmanager

# ============================================================================
# Configuration
# ============================================================================

# Secret salt for hashing user IDs (set via environment variable)
USER_ID_SALT = os.getenv("USER_ID_HASH_SALT", "default-salt-change-in-production")

# ============================================================================
# Utility Functions
# ============================================================================

def hash_user_id(user_id: str) -> str:
    """
    Hash user ID for privacy-preserving monitoring.

    Args:
        user_id: Original user ID

    Returns:
        SHA256 hash of user_id + salt
    """
    if not user_id:
        return "anonymous"

    combined = f"{user_id}{USER_ID_SALT}"
    return hashlib.sha256(combined.encode()).hexdigest()[:16]  # First 16 chars

# ============================================================================
# Application Info
# ============================================================================

app_info = Info('blackbox_app', 'BlackBox application information')
app_info.info({
    'version': os.getenv('APP_VERSION', 'dev'),
    'environment': os.getenv('ENVIRONMENT', 'development'),
    'region': os.getenv('DO_REGION', 'unknown')
})

# ============================================================================
# HTTP Request Metrics
# ============================================================================

# Request counter
http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

# Request duration histogram
http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP request latency',
    ['method', 'endpoint'],
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]
)

# Requests in progress
http_requests_in_progress = Gauge(
    'http_requests_in_progress',
    'HTTP requests currently being processed',
    ['method', 'endpoint']
)

# Request size
http_request_size_bytes = Summary(
    'http_request_size_bytes',
    'HTTP request size in bytes',
    ['method', 'endpoint']
)

# Response size
http_response_size_bytes = Summary(
    'http_response_size_bytes',
    'HTTP response size in bytes',
    ['method', 'endpoint']
)

# ============================================================================
# Worker Job Metrics
# ============================================================================

# Job counter
worker_jobs_total = Counter(
    'worker_jobs_total',
    'Total worker jobs processed',
    ['job_type', 'status']  # status: success, failure, timeout
)

# Job failures
worker_jobs_failed_total = Counter(
    'worker_jobs_failed_total',
    'Total worker job failures',
    ['job_type', 'error_type']
)

# Job duration
worker_job_duration_seconds = Histogram(
    'worker_job_duration_seconds',
    'Worker job processing time',
    ['job_type'],
    buckets=[0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0, 120.0]
)

# Queue length
worker_queue_length = Gauge(
    'worker_queue_length',
    'Number of jobs in queue',
    ['queue_name']
)

# Jobs in progress
worker_jobs_in_progress = Gauge(
    'worker_jobs_in_progress',
    'Jobs currently being processed',
    ['job_type']
)

# ============================================================================
# Voice Session Metrics (Privacy-Preserving)
# ============================================================================

# Voice session counter (NO audio or transcripts)
voice_sessions_total = Counter(
    'voice_sessions_total',
    'Total voice sessions',
    ['status']  # status: completed, failed, timeout
)

# Voice session duration
voice_session_duration_seconds = Histogram(
    'voice_session_duration_seconds',
    'Voice session duration',
    buckets=[1.0, 5.0, 10.0, 30.0, 60.0, 120.0, 300.0]
)

# PTT activations
ptt_activations_total = Counter(
    'ptt_activations_total',
    'Push-to-talk activations'
)

# ============================================================================
# External API Metrics
# ============================================================================

# OpenAI requests
openai_requests_total = Counter(
    'openai_requests_total',
    'OpenAI API requests',
    ['model', 'status']  # status: success, error, timeout
)

# OpenAI duration
openai_request_duration_seconds = Histogram(
    'openai_request_duration_seconds',
    'OpenAI API request duration',
    ['model'],
    buckets=[0.5, 1.0, 2.0, 5.0, 10.0, 20.0, 30.0]
)

# OpenAI cost tracking (tokens, not content)
openai_tokens_total = Counter(
    'openai_tokens_total',
    'OpenAI tokens consumed',
    ['model', 'token_type']  # token_type: input, output
)

# ElevenLabs requests
elevenlabs_requests_total = Counter(
    'elevenlabs_requests_total',
    'ElevenLabs API requests',
    ['voice_id', 'status']
)

# ElevenLabs duration
elevenlabs_request_duration_seconds = Histogram(
    'elevenlabs_request_duration_seconds',
    'ElevenLabs API request duration',
    ['voice_id'],
    buckets=[0.5, 1.0, 2.0, 5.0, 10.0, 20.0]
)

# ElevenLabs characters
elevenlabs_characters_total = Counter(
    'elevenlabs_characters_total',
    'ElevenLabs characters processed'
)

# ============================================================================
# Database Metrics
# ============================================================================

# Database query duration
db_query_duration_seconds = Histogram(
    'db_query_duration_seconds',
    'Database query duration',
    ['operation'],  # operation: select, insert, update, delete
    buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0]
)

# Database connections
db_connections = Gauge(
    'db_connections',
    'Database connections',
    ['state']  # state: active, idle
)

# Database errors
db_errors_total = Counter(
    'db_errors_total',
    'Database errors',
    ['error_type']
)

# ============================================================================
# Business Metrics (Privacy-Preserving)
# ============================================================================

# User sessions (hashed IDs only)
user_sessions_active = Gauge(
    'user_sessions_active',
    'Active user sessions'
)

# Subscription events
stripe_subscription_events_total = Counter(
    'stripe_subscription_events_total',
    'Stripe subscription events',
    ['event_type']  # event_type: created, updated, cancelled, renewed
)

# Payment events
stripe_payment_events_total = Counter(
    'stripe_payment_events_total',
    'Stripe payment events',
    ['status']  # status: succeeded, failed, refunded
)

# Failed payments (important for monitoring)
stripe_payment_failed_total = Counter(
    'stripe_payment_failed_total',
    'Failed payment attempts'
)

# Subscription cancellations
stripe_subscription_cancelled_total = Counter(
    'stripe_subscription_cancelled_total',
    'Subscription cancellations'
)

# MRR gauge (updated daily by BizOps script)
stripe_mrr_dollars = Gauge(
    'stripe_mrr_dollars',
    'Monthly Recurring Revenue in dollars'
)

# Active subscriptions
stripe_subscriptions_active = Gauge(
    'stripe_subscriptions_active',
    'Active subscriptions',
    ['tier']  # tier: individual, pro, team, league
)

# ============================================================================
# Helper Functions
# ============================================================================

@contextmanager
def track_request(request, endpoint: Optional[str] = None):
    """
    Context manager to track HTTP request metrics.

    Usage:
        with track_request(request, "/api/telemetry"):
            # ... process request
            pass
    """
    method = request.method
    endpoint = endpoint or request.url.path

    # Normalize endpoint (remove IDs)
    endpoint = normalize_endpoint(endpoint)

    # Start tracking
    http_requests_in_progress.labels(method=method, endpoint=endpoint).inc()
    start_time = time.time()

    try:
        yield
        status = 200  # Default success
    except Exception as e:
        status = 500
        raise
    finally:
        # Record metrics
        duration = time.time() - start_time
        http_request_duration_seconds.labels(
            method=method,
            endpoint=endpoint
        ).observe(duration)

        http_requests_total.labels(
            method=method,
            endpoint=endpoint,
            status=status
        ).inc()

        http_requests_in_progress.labels(method=method, endpoint=endpoint).dec()

def normalize_endpoint(path: str) -> str:
    """
    Normalize API endpoint path to avoid cardinality explosion.

    Examples:
        /api/users/12345 -> /api/users/:id
        /api/sessions/abc123/telemetry -> /api/sessions/:id/telemetry
    """
    import re

    # Replace UUIDs
    path = re.sub(
        r'/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}',
        '/:id',
        path,
        flags=re.IGNORECASE
    )

    # Replace numeric IDs
    path = re.sub(r'/\d+', '/:id', path)

    # Replace common hash patterns
    path = re.sub(r'/[a-zA-Z0-9]{16,}', '/:hash', path)

    return path

@contextmanager
def track_job(job_type: str):
    """
    Context manager to track worker job metrics.

    Usage:
        with track_job("process_audio"):
            # ... do work
            pass
    """
    worker_jobs_in_progress.labels(job_type=job_type).inc()
    start_time = time.time()
    status = "success"
    error_type = None

    try:
        yield
    except Exception as e:
        status = "failure"
        error_type = type(e).__name__
        worker_jobs_failed_total.labels(
            job_type=job_type,
            error_type=error_type
        ).inc()
        raise
    finally:
        duration = time.time() - start_time

        worker_job_duration_seconds.labels(job_type=job_type).observe(duration)
        worker_jobs_total.labels(job_type=job_type, status=status).inc()
        worker_jobs_in_progress.labels(job_type=job_type).dec()

def track_external_api_call(
    provider: str,
    duration: float,
    status: str,
    **labels
):
    """
    Track external API call metrics.

    Args:
        provider: "openai" or "elevenlabs"
        duration: Request duration in seconds
        status: "success", "error", or "timeout"
        **labels: Additional labels (model, voice_id, etc.)
    """
    if provider == "openai":
        model = labels.get("model", "unknown")
        openai_requests_total.labels(model=model, status=status).inc()
        openai_request_duration_seconds.labels(model=model).observe(duration)

        if status == "success":
            # Track tokens (if available)
            input_tokens = labels.get("input_tokens", 0)
            output_tokens = labels.get("output_tokens", 0)

            if input_tokens:
                openai_tokens_total.labels(
                    model=model,
                    token_type="input"
                ).inc(input_tokens)

            if output_tokens:
                openai_tokens_total.labels(
                    model=model,
                    token_type="output"
                ).inc(output_tokens)

    elif provider == "elevenlabs":
        voice_id = labels.get("voice_id", "unknown")
        elevenlabs_requests_total.labels(voice_id=voice_id, status=status).inc()
        elevenlabs_request_duration_seconds.labels(voice_id=voice_id).observe(duration)

        if status == "success":
            characters = labels.get("characters", 0)
            if characters:
                elevenlabs_characters_total.inc(characters)

# ============================================================================
# Metrics Endpoint
# ============================================================================

def get_metrics():
    """
    Generate Prometheus metrics in text format.

    Returns:
        tuple: (metrics_text, content_type)
    """
    return generate_latest(), CONTENT_TYPE_LATEST

# ============================================================================
# FastAPI Integration Example
# ============================================================================

"""
Example FastAPI integration:

from fastapi import FastAPI, Request, Response
from backend.monitoring.metrics import (
    get_metrics,
    http_requests_total,
    http_request_duration_seconds,
    track_external_api_call,
    hash_user_id
)
import time

app = FastAPI()

# Metrics endpoint
@app.get("/metrics")
async def metrics():
    metrics_text, content_type = get_metrics()
    return Response(content=metrics_text, media_type=content_type)

# Middleware for automatic request tracking
@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    method = request.method
    path = request.url.path

    # Skip metrics endpoint
    if path == "/metrics":
        return await call_next(request)

    # Normalize path
    from backend.monitoring.metrics import normalize_endpoint
    endpoint = normalize_endpoint(path)

    # Track request
    start_time = time.time()

    try:
        response = await call_next(request)
        status = response.status_code
    except Exception as e:
        status = 500
        raise
    finally:
        duration = time.time() - start_time

        http_request_duration_seconds.labels(
            method=method,
            endpoint=endpoint
        ).observe(duration)

        http_requests_total.labels(
            method=method,
            endpoint=endpoint,
            status=status
        ).inc()

    return response

# Example: Track external API call
@app.post("/api/voice/synthesize")
async def synthesize_voice(text: str):
    start_time = time.time()

    try:
        # Call ElevenLabs
        result = await call_elevenlabs_api(text)

        # Track success
        track_external_api_call(
            provider="elevenlabs",
            duration=time.time() - start_time,
            status="success",
            voice_id="engineer",
            characters=len(text)
        )

        return result

    except Exception as e:
        # Track failure
        track_external_api_call(
            provider="elevenlabs",
            duration=time.time() - start_time,
            status="error",
            voice_id="engineer"
        )
        raise
"""
