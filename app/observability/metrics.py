"""
Prometheus metrics definitions.

Instruments:
- DB query latency, errors, pool utilisation, circuit breaker state, retries
- HTTP request count & latency
- Message broker event counters
- AI / LLM token usage
"""

from prometheus_client import Counter, Gauge, Histogram

# ── Database ───────────────────────────────────────────────────────────
DB_QUERY_DURATION = Histogram(
    "db_query_duration_seconds",
    "Time spent executing a single database query",
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0),
)

DB_QUERY_ERRORS_TOTAL = Counter(
    "db_query_errors_total",
    "Total database query errors by exception type",
    ["error_type"],
)

DB_POOL_SIZE = Gauge(
    "db_pool_size",
    "Current number of connections in the asyncpg pool",
)

DB_POOL_FREE_SIZE = Gauge(
    "db_pool_free_size",
    "Number of free (idle) connections in the asyncpg pool",
)

DB_CIRCUIT_BREAKER_STATE = Gauge(
    "db_circuit_breaker_state",
    "Circuit breaker state: 0=closed, 1=half-open, 2=open",
)

DB_RETRY_TOTAL = Counter(
    "db_retry_total",
    "Total number of DB query retries",
)

# ── HTTP ───────────────────────────────────────────────────────────────
HTTP_REQUESTS_TOTAL = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "path", "status"],
)

HTTP_REQUEST_DURATION = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency",
    ["method", "path"],
    buckets=(0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
)

# ── Messaging ──────────────────────────────────────────────────────────
EVENTS_PUBLISHED_TOTAL = Counter(
    "events_published_total",
    "Total events published to message brokers",
    ["broker", "topic"],
)

EVENTS_CONSUMED_TOTAL = Counter(
    "events_consumed_total",
    "Total events consumed from message brokers",
    ["broker", "topic"],
)

EVENTS_FAILED_TOTAL = Counter(
    "events_failed_total",
    "Total events that failed processing",
    ["broker", "topic"],
)

# ── AI / LLM ──────────────────────────────────────────────────────────
LLM_REQUEST_DURATION = Histogram(
    "llm_request_duration_seconds",
    "Time spent on LLM API calls",
    ["model"],
    buckets=(0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0),
)

LLM_TOKENS_USED = Counter(
    "llm_tokens_used_total",
    "Total tokens consumed by LLM calls",
    ["model", "type"],
)
