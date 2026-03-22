# FastAPI Production Template

Production-ready async **FastAPI** template with **PostgreSQL** (PgBouncer), **circuit breakers**, **RabbitMQ**, **Kafka**, **ELK stack**, **Prometheus/Grafana**, and **LangChain/LangGraph** support — all containerised with Docker Compose.

---

## Architecture

```
                                    ┌──────────────┐
                                    │   Kibana      │ :5601
                                    │   (Logs UI)   │
                                    └──────┬───────┘
                                           │
┌──────────┐     ┌──────────────┐   ┌──────┴───────┐     ┌──────────────┐
│  Client   │───▶│   FastAPI     │──▶│ Elasticsearch │◀────│   Logstash   │
│           │    │  (uvicorn)    │   │    :9200      │     │    :5044     │
└──────────┘     └──────┬───────┘   └──────────────┘     └──────────────┘
                        │
           ┌────────────┼────────────┐
           ▼            ▼            ▼
    ┌────────────┐ ┌──────────┐ ┌──────────┐
    │ PgBouncer  │ │ RabbitMQ │ │  Kafka   │
    │   :6432    │ │  :5672   │ │  :9092   │
    └─────┬──────┘ └──────────┘ └──────────┘
          ▼
    ┌────────────┐   ┌────────────┐   ┌──────────┐
    │ PostgreSQL │   │ Prometheus │──▶│ Grafana  │
    │   :5432    │   │   :9090    │   │  :3000   │
    └────────────┘   └────────────┘   └──────────┘
```

### Key Patterns

| Pattern                | Library / Tool     | Purpose                                             |
| ---------------------- | ------------------ | --------------------------------------------------- |
| Async DB Pool          | asyncpg            | Small app-side pool (2-10); PgBouncer multiplexes   |
| Connection Pooler      | PgBouncer          | Transaction-mode pooling for high concurrency       |
| Circuit Breaker        | aiobreaker         | Fast-fail when PostgreSQL is unhealthy              |
| Retry + Backoff        | tenacity           | Exponential backoff for transient failures          |
| Message Queue          | RabbitMQ / Kafka   | Event-driven async processing                       |
| Observability          | Prometheus/Grafana | Request latency, DB query duration, pool gauges     |
| Centralized Logging    | ELK Stack          | Structured JSON logs → Logstash → Elasticsearch     |
| GenAI                  | LangChain/LangGraph| LLM chains, agent graphs, tool integrations         |
| Global Error Handling  | Custom middleware   | Consistent JSON error envelope across all endpoints |

---

## Project Structure

```
ProjectTemplateFastAPI/
├── app/
│   ├── main.py                              # FastAPI entry point + lifespan
│   ├── core/                                # Shared infrastructure
│   │   ├── config.py                        # pydantic-settings (all env vars)
│   │   ├── logging.py                       # Structured JSON logging (ELK-ready)
│   │   ├── exceptions.py                    # Global exception hierarchy + handlers
│   │   └── security.py                      # API key / JWT / auth utilities
│   ├── db/                                  # Database layer
│   │   ├── pool.py                          # asyncpg pool management
│   │   ├── resilience.py                    # Circuit breaker + retry helpers
│   │   └── repository.py                    # Base repository pattern
│   ├── messaging/                           # Event-driven layer
│   │   ├── base.py                          # Abstract broker interface + Event model
│   │   ├── rabbitmq/
│   │   │   ├── producer.py                  # aio-pika producer
│   │   │   └── consumer.py                  # aio-pika consumer
│   │   └── kafka/
│   │       ├── producer.py                  # aiokafka producer
│   │       └── consumer.py                  # aiokafka consumer
│   ├── ai/                                  # GenAI / LLM layer
│   │   ├── llm.py                           # LLM client factory
│   │   ├── chains/
│   │   │   └── example_chain.py             # LangChain LCEL chain example
│   │   ├── graphs/
│   │   │   └── example_graph.py             # LangGraph StateGraph example
│   │   └── tools/
│   │       └── example_tool.py              # Custom LangChain tools
│   ├── observability/                       # Monitoring
│   │   ├── metrics.py                       # Prometheus metric definitions
│   │   └── middleware.py                    # HTTP instrumentation + Request ID
│   ├── api/                                 # API layer (versioned)
│   │   ├── deps.py                          # Shared dependencies (pagination, auth)
│   │   └── v1/
│   │       ├── router.py                    # V1 router aggregator
│   │       ├── health/
│   │       │   └── routes.py                # Liveness + readiness probes
│   │       └── items/                       # Feature module (example)
│   │           ├── routes.py                # HTTP endpoints
│   │           ├── schemas.py               # Pydantic models
│   │           ├── service.py               # Business logic
│   │           └── repository.py            # Data access
│   ├── workers/
│   │   └── event_handlers.py               # Message broker event handlers
│   └── common/
│       └── responses.py                     # Standard response envelopes
├── migrations/                              # Alembic database migrations
│   ├── env.py
│   ├── script.py.mako
│   └── versions/
│       └── 001_create_items_table.py
├── tests/
│   ├── conftest.py                          # Shared fixtures
│   ├── unit/                                # Fast, isolated tests
│   ├── integration/                         # Tests requiring services
│   └── e2e/                                 # End-to-end tests
├── infra/                                   # Infrastructure configs
│   ├── prometheus/prometheus.yml
│   ├── logstash/logstash.conf
│   └── filebeat/filebeat.yml
├── .env.example
├── .gitignore
├── alembic.ini
├── docker-compose.yml                       # Full stack (all services)
├── docker-compose.dev.yml                   # Dev-only (DB + Redis + RabbitMQ)
├── Dockerfile
├── entrypoint.sh
├── pyproject.toml
├── requirements.txt
└── requirements-dev.txt
```

---

## Quick Start

### Prerequisites

- Docker & Docker Compose
- Python 3.11+ (for local development)

### 1. Run Full Stack with Docker Compose

```bash
# Start all services
docker compose up --build

# API:          http://localhost:8000
# Swagger Docs: http://localhost:8000/docs
# Metrics:      http://localhost:8000/metrics
# Prometheus:   http://localhost:9090
# Grafana:      http://localhost:3000  (admin/admin)
# Kibana:       http://localhost:5601
# RabbitMQ UI:  http://localhost:15672 (guest/guest)
```

### 2. Local Development

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements-dev.txt

# Copy environment file
cp .env.example .env

# Start infrastructure only
docker compose -f docker-compose.dev.yml up -d

# Run migrations
alembic upgrade head

# Start the app
uvicorn app.main:app --reload --port 8000
```

### 3. Run Tests

```bash
pytest tests/ -v
```

---

## Adding a New Feature Module

Each feature is self-contained under `app/api/v1/<feature>/`:

```
app/api/v1/orders/
├── __init__.py
├── routes.py       # Endpoints
├── schemas.py      # Pydantic models
├── service.py      # Business logic
└── repository.py   # Data access
```

Then register it in `app/api/v1/router.py`:

```python
from app.api.v1.orders.routes import router as orders_router
v1_router.include_router(orders_router)
```

This structure lets multiple developers work on separate features with **zero merge conflicts**.

---

## API Endpoints

| Method | Path                    | Description              |
| ------ | ----------------------- | ------------------------ |
| GET    | /api/v1/health/         | Liveness probe           |
| GET    | /api/v1/health/ready    | Readiness probe          |
| POST   | /api/v1/items/          | Create an item           |
| GET    | /api/v1/items/          | List items (paginated)   |
| GET    | /api/v1/items/{id}      | Get item by ID           |
| PATCH  | /api/v1/items/{id}      | Update an item           |
| DELETE | /api/v1/items/{id}      | Delete an item           |
| GET    | /metrics                | Prometheus metrics       |

---

## Configuration

All settings are loaded from environment variables (or `.env`) via `pydantic-settings`. See `.env.example` for the full list.

---

## License

MIT
