# Prompt Trends Automation — Backend

Prompt Trends Automation is an enterprise-grade modular monolith backend built with **Python 3.12+ and FastAPI**. It manages the end-to-end lifecycle of trend intelligence, raw signal ingestion, normalization, deduplication, AI-driven analysis, deterministic multi-signal scoring, multimodal prompt generation, human approval/audit workflows, and omnichannel social media automation.

---

## 🏛️ Architecture Overview

The backend is architected as a **Domain-Driven Modular Monolith** designed for scalability, testability, and clear separation of concerns:

- **Module-First Organization**: Each business domain is isolated in `app/modules/<domain>/` with its own models, schemas, repositories, services, dependencies, enums, and API routers.
- **Contract-Driven Decoupling**: Services adhere to abstract base contracts (`contracts.py`), enabling clean decoupling, dependency inversion, and straightforward unit/mock testing.
- **Dependency Injection**: Loose coupling and request scoping powered by FastAPI `Depends()` providers (`dependencies.py`).
- **Standardized API Envelope**: All API endpoints return a uniform response envelope:
  ```json
  {
    "message": "Operation successful",
    "data": { ... }
  }
  ```
- **Centralized Exception Handling**: Application exceptions (`AppException`, `NotFoundException`, `ForbiddenException`, `ValidationException`) are caught by global exception handlers and translated into structured JSON errors.
- **Role-Based Access Control (RBAC)**: Strict role enforcement (`admin`, `trend_manager`, `reviewer`, `viewer`) via reusable route dependencies (`require_roles`).
- **Multi-Provider AI Engine with SSE Streaming**: Decoupled LLM provider layer supporting DeepSeek, OpenAI, Claude, Gemini, Groq, Mistral, and Ollama with automatic fallback, singleton HTTP connection pooling, and real-time Server-Sent Events (SSE) streaming (`/api/v1/ai/generate/stream`).
- **Deterministic Scoring & LangGraph Pipeline**: Ingested candidates pass through normalization, deduplication, evidence verification, weighted deterministic scoring (summing to 100), structured prompt generation, and safety validation before entering `pending_review`.
- **Distributed Celery & Redis Task Architecture**: Asynchronous workload isolated across 7 dedicated Redis queues (`trend.collect`, `trend.process`, `trend.ai`, `trend.integration`, `social.generate`, `social.publish`, `social.analytics`).

---

## 📁 Directory Structure

```text
backend/
├── app/
│   ├── main.py                        # FastAPI application factory, lifespan, and router aggregation
│   ├── core/                          # Cross-cutting infrastructure & settings
│   │   ├── config.py                  # Pydantic Settings (environment variable validation)
│   │   ├── database.py                # Async SQLAlchemy engine & scoped session factory
│   │   ├── redis.py                   # Async Redis client connection management
│   │   ├── security.py                # Password hashing (Argon2/Bcrypt) & JWT token handling
│   │   ├── exceptions.py             # Custom domain exceptions & global exception handlers
│   │   ├── middleware.py              # X-Request-ID propagation & structured request logging
│   │   ├── responses.py              # Standard API response envelopes & helpers
│   │   ├── oauth_manager.py           # OAuth 2.0 PKCE token exchange & refresh engine
│   │   ├── proxy_manager.py           # Rotating proxy manager for external collectors
│   │   └── rate_limit.py              # Redis-backed sliding window rate limiter
│   ├── shared/                        # Shared base classes and models
│   │   ├── base_model.py              # BaseModel with UUID primary key, timestamps, and soft-delete
│   │   ├── base_repository.py         # Generic async CRUD repository pattern
│   │   ├── base_schemas.py            # Reusable pagination, sorting, and metadata schemas
│   │   └── enums.py                  # Cross-domain enums (Platform, MediaType, TrendStatus)
│   ├── modules/                       # Domain Business Modules
│   │   ├── auth/                      # Authentication, User Management, and RBAC
│   │   ├── trend_sources/             # Data sources configuration (Instagram, TikTok, YT, X, Google Trends)
│   │   ├── trend_runs/                # Async discovery execution tracking (202 Accepted)
│   │   ├── trend_candidates/          # Raw ingested signals & normalization (JSONB payload)
│   │   ├── trends/                    # Canonical trends, evidence junction & state machine
│   │   ├── scoring/                   # Configurable weighted scoring engine (weights sum = 100)
│   │   ├── prompt_generation/         # 6-modality structured prompt packages & regeneration
│   │   ├── approvals/                 # Human review decision audit log (approve/reject/regenerate)
│   │   ├── ai/                        # Multi-provider LLM abstraction layer
│   │   │   ├── agents/                # Trend discovery agent & LangGraph state workflow
│   │   │   ├── contracts/             # AI provider and service contracts
│   │   │   ├── controllers/           # AI studio, sandbox, and streaming endpoints
│   │   │   ├── providers/             # DeepSeek, OpenAI, Claude, Gemini, Groq, Ollama implementations
│   │   │   └── services/              # AI execution logging, prompt templates, and HTTP connection pooling
│   │   ├── social_media/              # Omnichannel Social Media AI Agent
│   │   │   ├── controllers/           # Accounts, Campaigns, Content, Publishing, Brand Kit, Webhooks
│   │   │   ├── providers/             # Meta Graph API, TikTok API, X API v2, YouTube Data API
│   │   │   └── services/              # Modular sub-services:
│   │   │       ├── brand_kit.py       # Brand identity tokens, typography, colors, guidelines
│   │   │       ├── campaigns.py       # Social campaign goals, briefs, and targeting
│   │   │       ├── connections.py     # OAuth token management & secure account linking
│   │   │       ├── generation.py      # Multi-platform content variant generator
│   │   │       ├── media_assets.py    # Cloudflare/Supabase asset storage & signed URLs
│   │   │       ├── performance.py     # Engagement and reach analytics synchronization
│   │   │       ├── publishing.py      # Idempotent scheduling & dispatching to social networks
│   │   │       └── service.py         # Social media facade unifying sub-services
│   │   ├── integrations/              # Sarah Agent & external webhook adapters
│   │   └── settings/                  # Dynamic system runtime settings API
│   ├── collectors/                    # External platform scrapers/collectors
│   ├── pipeline/                      # Deduplication, Normalization, and Verification pipeline
│   └── workers/                       # Celery tasks & scheduled cron workers
│       ├── celery_app.py              # Celery worker configuration & task routing
│       ├── beat_schedule.py           # Celery Beat cron schedule (periodic discovery & retries)
│       ├── collect_tasks.py           # Platform ingestion tasks (`trend.collect` queue)
│       ├── process_tasks.py           # Deduplication & scoring tasks (`trend.process` queue)
│       ├── ai_tasks.py                # Prompt generation & LLM tasks (`trend.ai` queue)
│       └── integration_tasks.py       # Webhook & downstream dispatch tasks (`trend.integration` queue)
├── migrations/                        # Alembic async migration files
│   ├── env.py                         # Alembic migration runner
│   └── versions/                      # Migration version scripts
├── tests/                             # Automated test suite (134+ tests)
│   ├── conftest.py                    # Pytest fixtures & async SQLite/PostgreSQL setup
│   ├── unit/                          # Unit tests (scoring, dedup, prompts, RBAC)
│   └── api/                           # Integration API route tests
├── Dockerfile                         # Production Python 3.12 slim container
├── docker-compose.yml                 # Local multi-container orchestrator
├── alembic.ini                        # Alembic database configuration
├── requirements.txt                   # Production dependencies
└── .env.example                       # Environment configuration template
```

---

## 🗄️ Database Entities & Data Models

1. **`User`**: Accounts with hashed credentials and roles (`admin`, `trend_manager`, `reviewer`, `viewer`).
2. **`TrendSource`**: Discovery source configurations (Instagram, TikTok, YouTube, X, Google Trends). API tokens and client secrets are encrypted.
3. **`TrendRun`**: Execution record of automated or manual discovery runs (status, duration, item count, trigger type).
4. **`TrendCandidate`**: Raw incoming signals preserving full original JSONB payloads alongside normalized metrics.
5. **`Trend`**: Canonical deduplicated trend entity tracking overall score, risk tier, lifecycle status (`discovered` → `analyzed` → `scored` → `prompt_generated` → `pending_review` → `approved` / `rejected` → `archived`), and category.
6. **`TrendEvidence`**: Junction linking multiple platform candidates to a single canonical Trend concept.
7. **`ScoringConfiguration`**: Versioned database-driven scoring weights:
   - Freshness & Velocity
   - Cross-Platform Engagement
   - Winsta Brand Relevance
   - Visual Generatability & Aesthetic Appeal
   - Novelty & Virality Potential
8. **`TrendSignal`**: Individual computed signal score breakdown per trend.
9. **`PromptPackage`**: Versioned multimodal prompt generation output (text-to-image, text-to-video, voiceover scripts, negative prompts, tags, quality assessment).
10. **`TrendReview`**: Immutable audit log of review decisions (`approve`, `reject`, `request_regeneration`) with author ID and notes.
11. **`AIExecution`**: Full observability record of LLM calls (provider, model, token usage, latency, cost estimate, prompt/response payloads).
12. **`SocialAccount`**: Encrypted OAuth 2.0 connected accounts (Meta, TikTok, X, YouTube, LinkedIn).
13. **`SocialCampaign` & `ContentBrief`**: Campaign briefs linking approved trends to marketing goals and target audiences.
14. **`ContentItem` & `ContentVariant`**: Multi-platform copy, hashtags, media attachments, and approval state per channel.
15. **`PublishJob`**: Idempotent scheduling and dispatch record tracking publishing status and remote platform post IDs.
16. **`BrandKit`**: Organization tokens, primary/secondary colors, logo assets, banned phrases, and brand tone guidelines.

---

## 🔌 API Reference (Prefix: `/api/v1`)

### Authentication & RBAC
- `POST /api/v1/auth/register` — Register a new internal user.
- `POST /api/v1/auth/login` — Authenticate user and issue JWT access and refresh tokens.
- `POST /api/v1/auth/refresh` — Refresh expired access token.
- `GET  /api/v1/auth/me` — Retrieve current authenticated user profile and permissions.

### Trend Discovery & Runs
- `POST /api/v1/trend-runs` — Trigger on-demand discovery run (**returns `202 Accepted`**; Celery handles async execution).
- `GET  /api/v1/trend-runs` — List discovery runs with pagination and status filters.
- `GET  /api/v1/trend-runs/{id}` — Retrieve discovery run execution details and progress metrics.
- `POST /api/v1/trend-runs/{id}/cancel` — Abort an active discovery run.

### Trend Sources
- `GET   /api/v1/trend-sources` — List all registered trend sources.
- `GET   /api/v1/trend-sources/{id}` — Get source details (sensitive tokens are masked).
- `PATCH /api/v1/trend-sources/{id}` — Update source parameters, scraping frequency, or categories.
- `POST  /api/v1/trend-sources/{id}/enable` — Enable data collection for a source.
- `POST  /api/v1/trend-sources/{id}/disable` — Pause data collection for a source.

### Canonical Trends & Evidence
- `GET /api/v1/trends` — Query canonical trends with filters (`status`, `category`, `source`, `minimum_score`, `search`, `page`, `page_size`).
- `GET /api/v1/trends/{id}` — Get trend detail with signals, candidate evidence, prompt packages, and review audit trail.
- `GET /api/v1/trends/{id}/evidence` — List all cross-platform evidence items linked to this trend.

### Scoring Configuration
- `GET /api/v1/scoring/settings` — Get active scoring weights and current configuration version.
- `PUT /api/v1/scoring/settings` — Update scoring weights (validates that total weight equals exactly 100).

### Multimodal Prompt Studio
- `GET  /api/v1/trends/{id}/prompt-packages` — List all generated prompt package versions.
- `GET  /api/v1/trends/{id}/prompt-packages/latest` — Get the latest active prompt package.
- `POST /api/v1/trends/{id}/regenerate` — Request prompt regeneration with custom guidance (**returns `202 Accepted`**).

### Review & Approvals
- `POST /api/v1/trends/{id}/review` — Submit review decision (`approve`, `reject`, `request_regeneration`). Triggers automated downstream delivery on approval.

### AI Engine & Real-Time Streaming
- `POST /api/v1/ai/generate` — Execute unified AI prompt generation across configured providers.
- `POST /api/v1/ai/generate/stream` — **Server-Sent Events (SSE)** endpoint streaming LLM tokens in real-time.
- `GET  /api/v1/ai/providers` — List supported AI providers, active models, and health status.
- `POST /api/v1/ai/test` — Test connectivity and latency to a selected LLM provider.

### Omnichannel Social Media Hub
- `GET    /api/v1/social/accounts` — List connected social media channels and token expiry status.
- `POST   /api/v1/social/accounts/oauth/authorize` — Generate OAuth 2.0 authorization URL for a platform.
- `POST   /api/v1/social/campaigns` — Create a new marketing campaign brief.
- `GET    /api/v1/social/campaigns` — List active campaigns and content variants.
- `POST   /api/v1/social/content/{id}/approve` — Approve or reject generated social content variant.
- `POST   /api/v1/social/content/{id}/schedule` — Schedule approved content for publication.
- `GET    /api/v1/social/brand-kit` — Retrieve organization brand kit guidelines and visual tokens.
- `PUT    /api/v1/social/brand-kit` — Update organization brand identity tokens.

### System & Health Checks
- `GET /health` — Liveness probe (HTTP 200).
- `GET /health/ready` — Readiness probe (checks PostgreSQL and Redis connectivity).
- `GET /api/v1/settings` — Retrieve system configuration flags.

---

## ⚡ Celery Worker & Queue Topology

The platform separates background workloads across 7 isolated Redis queues to ensure high-throughput scraping never starves critical publishing tasks:

| Queue Name | Responsibilities | Dispatched By |
|---|---|---|
| `trend.collect` | Platform collector scraping (Instagram, TikTok, YouTube, X, Google Trends) | Manual run or Celery Beat |
| `trend.process` | Text normalization, candidate deduplication, metadata enrichment, scoring | Collector completion |
| `trend.ai` | Concept extraction, multimodal prompt generation, safety validation, prompt repair | Process completion / Regeneration |
| `trend.integration` | Downstream handoff to Sarah Agent and external webhook dispatch | Human Approval event |
| `social.generate` | Platform-specific content variant copy, hashtag, and image generation | Content brief creation |
| `social.publish` | Idempotent API dispatch to Meta, TikTok, and X Graph APIs | Scheduled publish job |
| `social.analytics` | Social post metrics synchronization (reach, likes, comments, shares) | Periodic Celery Beat |

---

## 🛠️ Local Development & Quick Start

### Prerequisites
- **Python**: `3.12+`
- **PostgreSQL**: `15+` (or Supabase Postgres)
- **Redis**: `7.x+`
- **Docker & Docker Compose** (Optional, recommended)

---

### Method A: Running with Docker Compose (Recommended)

Docker Compose starts the entire stack (FastAPI backend, Celery worker, Celery beat, Redis, and PostgreSQL):

```bash
cd backend

# 1. Prepare environment variables
cp .env.example .env

# 2. Start all containers in the background
docker compose up -d

# 3. Apply database migrations
docker compose exec api alembic upgrade head

# 4. Stream application logs
docker compose logs -f api
```

The API will be accessible at: `http://localhost:8000`
Interactive Swagger Docs: `http://localhost:8000/docs`

---

### Method B: Running Manually (Native Python)

#### 1. Setup Virtual Environment
```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

#### 2. Configure Environment Variables
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
Generate an encryption key for social tokens:
```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```
Place the output in `.env` as `SOCIAL_TOKEN_ENCRYPTION_KEY=<generated-key>`.

Set your database and redis URLs:
```env
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/pta_db
DATABASE_URL_SYNC=postgresql://postgres:postgres@localhost:5432/pta_db
DIRECT_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/pta_db
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/2
```

#### 3. Run Database Migrations
```bash
alembic upgrade head
```

#### 4. Start the FastAPI Application
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

#### 5. Start Celery Worker & Beat (Separate Terminals)
```bash
# Terminal 2: Celery Worker listening to all queues
celery -A app.workers.celery_app worker --loglevel=info -Q trend.collect,trend.process,trend.ai,trend.integration,social.generate,social.publish,social.analytics

# Terminal 3: Celery Beat Scheduler
celery -A app.workers.celery_app beat --loglevel=info
```

---

## 🧪 Running Automated Tests

The test suite covers scoring engines, prompt generation, deduplication logic, RBAC policies, and API endpoints:

```bash
# Run entire test suite
pytest tests/ -v

# Run unit tests only
pytest tests/unit/ -v

# Run API integration tests only
pytest tests/api/ -v
```

---

## 🔒 Security & Best Practices

1. **Credential Encryption**: All connected social media OAuth tokens and external API secrets are encrypted at rest using AES-128-CBC (Fernet) via `SOCIAL_TOKEN_ENCRYPTION_KEY`.
2. **Connection Pooling**: External LLM and social API calls share a singleton asynchronous HTTP connection pool with keep-alive limits to prevent socket starvation.
3. **Database Prepared Statements**: When using Supabase transaction-mode poolers (port 6543), `prepared_statement_cache_size=0` is automatically configured to prevent transaction errors.
4. **Idempotent Publishing**: All social publishing commands utilize unique idempotency keys in `PublishJob` to prevent duplicate posts during retries.
