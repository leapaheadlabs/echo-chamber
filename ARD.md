# 🏗️ ARD — ARCHITECTURE REQUIREMENTS DOCUMENT

> **ECHO CHAMBER v1.0**  
> **Document ID:** EC-ARD-001  
> **Version:** 1.0  
> **Date:** 2026-06-12  
> **Classification:** INTERNAL — COMMANDER EYES ONLY  
> **Depends on:** BRD.md  
> **Supersedes:** BRAIN.md (summary; this is the authoritative architecture spec)

---

## 1. ARCHITECTURE OVERVIEW

### 1.1 Architecture Style

**Event-driven, graph-based autonomous agent system with human-in-the-loop override.**

ECHO CHAMBER is built on LangGraph, a framework for building stateful, multi-agent applications as directed graphs. The system uses a **hub-and-spoke** pattern where a central Cortex (hub) routes signals to platform-specific Ganglia (spokes). Ganglia are autonomous sub-graphs that execute within guardrails and report back.

### 1.2 Architecture Decision Records (ADRs)

| ADR | Decision | Rationale | Alternatives Considered |
|-----|----------|-----------|------------------------|
| **ADR-01** | LangGraph + LangChain as agent framework | StateGraph for Cortex, sub-graphs for ganglia, built-in memory, human-in-the-loop, checkpointer | CrewAI (too rigid), AutoGen (less graph-native), custom (too much build) |
| **ADR-02** | PostgreSQL + pgvector (single DB) | One DB for structured + vector = less infra, simpler ops, transactional consistency | Pinecone (separate infra), Chroma (not production-grade enough), Qdrant (same split) |
| **ADR-03** | Discord as Commander UI | No web app overhead, Larry-already-there, slash commands = structured input, embeds = structured output | Web dashboard (Phase 4+), CLI, Telegram |
| **ADR-04** | Voice injection over fine-tuning | Product-agnostic from day one. Client voice injected at runtime via LLM context. No retraining latency. | Fine-tuned models per client (Phase 4+ for performance, not MVP) |
| **ADR-05** | PRAW API + Playwright fallback for Reddit | API is faster, cheaper, more reliable. Playwright when API is insufficient or account needs browser fingerprint | API-only (limited by Reddit rate limits), browser-only (expensive, slow) |
| **ADR-06** | Residential proxies (rotating) | Platform anti-bot detection flags datacenter IPs. Residential IPs blend with organic users. | Datacenter proxies (cheaper but higher ban risk), VPNs (shared IPs = ban correlation risk) |
| **ADR-07** | Event-driven signal ingestion (Redis/RabbitMQ) | Decouples signal sources from processing. Retry + dead letter support. Backpressure handling. | Polling (wasteful, slow), direct DB writes (tight coupling) |

### 1.3 Key Quality Attributes

| Quality | Target | How We Achieve It |
|---------|--------|-------------------|
| **Scalability** | 10+ clients, 50+ ganglia, linear cost scaling | Stateless ganglia, shared Cortex, pooled accounts, horizontal LLM scaling |
| **Reliability** | 99% Commander uptime, graceful ganglion degradation | PostgreSQL HA, Redis HA, LangGraph checkpointer, dead letter queues |
| **Security** | Credentials never in LLM context, encrypted at rest | HashiCorp Vault / cloud KMS, credential rotation, proxy isolation |
| **Observability** | Full decision trail, real-time Commander dashboard | Structured logging, Prometheus metrics, LangGraph event streaming |
| **Maintainability** | New ganglion in < 1 week | Standardized ganglion interface, sub-graph pattern, shared ToolNode library |
| **Compliance** | Hard guardrails non-overridable, #ad always appended | Pre-flight + post-flight content validators, barrier nodes in graphs |

---

## 2. SYSTEM ARCHITECTURE

### 2.1 High-Level Component Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                     EXTERNAL SIGNALS                          │
│  (Reddit API, Discord events, webhooks, RSS, manual input)    │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                    MESSAGE QUEUE (Redis)                      │
│                  Signal Ingestion + Buffer                    │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                         CORTEX                               │
│                    LangGraph StateGraph                       │
│                                                              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │ Signal   │  │ Signal   │  │ Cortex   │  │ Dispatch │   │
│  │ Ingest   │─▶│ Classify │─▶│ Decide   │─▶│ Router   │   │
│  └──────────┘  └──────────┘  └──────────┘  └─────┬────┘   │
│                                                   │         │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐        │         │
│  │ Learn    │◀─│ Monitor  │◀─│ Escalate │        │         │
│  └──────────┘  └──────────┘  └──────────┘        │         │
└───────────────────────────────────────────────────┼─────────┘
                                                    │
           ┌────────────────────────────────────────┼──────────┐
           │                                        │          │
           ▼                                        ▼          ▼
┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐
│  REDDIT GANGLION │  │ DISCORD GANGLION │  │  TIKTOK GANGLION │
│  (sub-graph)     │  │ (sub-graph)      │  │  (future)        │
│                  │  │                  │  │                  │
│  1. Account Sel  │  │ 1. Server Disc   │  │  ...             │
│  2. Context Load │  │ 2. Join + Lurk   │  │                  │
│  3. Content Gen  │  │ 3. Participation │  │                  │
│  4. Guardrails   │  │ 4. Opportunity   │  │                  │
│  5. Scheduler    │  │ 5. Mention Deploy│  │                  │
│  6. Deploy       │  │ 6. Trust Tracker │  │                  │
│  7. Monitor      │  │                  │  │                  │
│  8. Report       │  │ 7. Community Mode│  │                  │
└──────────────────┘  └──────────────────┘  └──────────────────┘
           │                    │                    │
           └────────────────────┼────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────┐
│                      DATA LAYER                               │
│                                                              │
│  ┌──────────────────┐  ┌──────────────────┐                 │
│  │   PostgreSQL     │  │  pgvector        │                 │
│  │   (procedural)   │  │  (episodic +     │                 │
│  │                  │  │   semantic)      │                 │
│  │  • Accounts      │  │                  │                 │
│  │  • Clients       │  │  • Campaigns     │                 │
│  │  • Campaigns     │  │  • Patterns      │                 │
│  │  • State         │  │  • Embeddings    │                 │
│  └──────────────────┘  └──────────────────┘                 │
│                                                              │
│  ┌──────────────────┐  ┌──────────────────┐                 │
│  │  HashiCorp Vault │  │  Object Store    │                 │
│  │  (secrets)       │  │  (training data) │                 │
│  └──────────────────┘  └──────────────────┘                 │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 Component Interaction Patterns

| Interaction | Pattern | Implementation |
|-------------|---------|----------------|
| Signal → Cortex | Async publish/subscribe | Redis pub/sub or RabbitMQ direct exchange |
| Cortex → Ganglion dispatch | LangGraph `Command(go_to=ganglion)` | Sub-graph node transition within compiled graph |
| Ganglion → External platform | API call (preferred) or browser automation (fallback) | PRAW / discord.py / Playwright ToolNode |
| Ganglion → Cortex report | Graph state update + event emit | Return to Cortex via graph edge after completion |
| Cortex → Commander | Discord webhook / bot message | Structured embeds via discord.py bot |
| Commander → Cortex | Discord slash command → API call → graph event | FastAPI endpoint receiving Discord interaction |
| Health check → All components | Periodic worker | Cron-triggered health_check node in Cortex |
| Kill switch → All ganglia | Global state flag + message broadcast | `interrupt()` on all active sub-graphs |

### 2.3 Deployment Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    CLOUD PROVIDER (AWS/GCP)                  │
│                                                              │
│  ┌──────────────────────────┐  ┌──────────────────────────┐│
│  │   COMPUTE (ECS/GKE)      │  │   COMPUTE (ECS/GKE)      ││
│  │   Cortex Service         │  │   Ganglion Workers       ││
│  │   • LangGraph runtime    │  │   • Reddit worker pool   ││
│  │   • FastAPI endpoint     │  │   • Discord worker pool  ││
│  │   • Discord bot          │  │   • Auto-scale           ││
│  │   • Autoscaling: 1-4     │  │   • Autoscaling: 1-20    ││
│  └──────────────────────────┘  └──────────────────────────┘│
│                                                              │
│  ┌──────────────────────────┐  ┌──────────────────────────┐│
│  │   DATABASE (RDS)         │  │   CACHE (ElastiCache)    ││
│  │   PostgreSQL + pgvector  │  │   Redis                  ││
│  │   • Multi-AZ             │  │   • Message queue        ││
│  │   • 50GB initial         │  │   • Rate limit tracking  ││
│  │   • Auto-backup          │  │   • Session state        ││
│  └──────────────────────────┘  └──────────────────────────┘│
│                                                              │
│  ┌──────────────────────────┐  ┌──────────────────────────┐│
│  │   SECRETS (Vault/KMS)    │  │   PROXY GATEWAY          ││
│  │   • Credentials          │  │   • Residential proxy pool││
│  │   • API keys             │  │   • Request routing       ││
│  │   • Rotation automation  │  │   • IP rotation per req  ││
│  └──────────────────────────┘  └──────────────────────────┘│
└─────────────────────────────────────────────────────────────┘
```

---

## 3. DATA ARCHITECTURE

### 3.1 Entity-Relationship Diagram (Logical)

```
┌──────────┐       ┌──────────────┐       ┌──────────┐
│  Client  │1────N│   Campaign   │1────N│ Dispatch │
└──────────┘       └──────────────┘       └──────────┘
     │                                           │
     │1                                          │N
     │                                           │
     ▼                                           ▼
┌──────────┐                              ┌──────────────┐
│  Voice   │                              │  Deployment  │
│  Profile │                              └──────┬───────┘
└──────────┘                                     │
                                                  │1
                                                  │
                    ┌─────────────────┬───────────┼───────────┐
                    │                 │           │           │
                    ▼                 ▼           ▼           ▼
              ┌──────────┐    ┌──────────┐ ┌──────────┐ ┌──────────┐
              │  Signal  │    │  Account │ │ Platform │ │ Training │
              │          │    │  (Ghost) │ │  Event   │ │  Record  │
              └──────────┘    └──────────┘ └──────────┘ └──────────┘

┌──────────────┐       ┌──────────────┐
│  Episodic    │       │  Semantic    │
│  Memory      │       │  Memory      │
│  (pgvector)  │       │  (pgvector)  │
└──────────────┘       └──────────────┘
```

### 3.2 Core Database Schemas

#### Client
```sql
CREATE TABLE clients (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    client_id VARCHAR(64) UNIQUE NOT NULL,
    product_url VARCHAR(2048) NOT NULL,
    status VARCHAR(16) NOT NULL DEFAULT 'onboarding',
    voice_profile JSONB NOT NULL DEFAULT '{}',
    constraints JSONB NOT NULL DEFAULT '{}',
    budget JSONB NOT NULL DEFAULT '{}',
    kpi_weights JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

#### Accounts (Ghost Pool)
```sql
CREATE TABLE accounts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    account_label VARCHAR(64) UNIQUE NOT NULL,
    platform VARCHAR(32) NOT NULL,
    credentials_ref VARCHAR(256) NOT NULL,  -- Vault path
    proxy_pool VARCHAR(64),
    fingerprint JSONB NOT NULL DEFAULT '{}',
    karma INTEGER DEFAULT 0,
    account_age_days INTEGER DEFAULT 0,
    status VARCHAR(16) NOT NULL DEFAULT 'maturing',  -- maturing, active, cooldown, burned
    last_used_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

#### Deployments
```sql
CREATE TABLE deployments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    dispatch_id UUID NOT NULL,
    campaign_id UUID NOT NULL,
    account_id UUID NOT NULL,
    platform VARCHAR(32) NOT NULL,
    content JSONB NOT NULL,
    url VARCHAR(2048),
    status VARCHAR(16) NOT NULL DEFAULT 'pending',
    metrics JSONB DEFAULT '{}',
    deployed_at TIMESTAMP WITH TIME ZONE,
    monitored_until TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

#### Episodic Memory
```sql
CREATE TABLE episodic_memory (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    campaign_id UUID NOT NULL,
    client_id VARCHAR(64) NOT NULL,
    memory_type VARCHAR(32) NOT NULL,  -- deployment, lesson, outcome
    content JSONB NOT NULL,
    embedding VECTOR(1536),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX ON episodic_memory USING ivfflat (embedding vector_cosine_ops);
```

#### Training Records
```sql
CREATE TABLE training_records (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    client_id VARCHAR(64) NOT NULL,
    platform VARCHAR(32) NOT NULL,
    prompt TEXT NOT NULL,
    voice_injection JSONB NOT NULL,
    generated_content TEXT NOT NULL,
    human_edited TEXT,
    deployed BOOLEAN DEFAULT FALSE,
    outcome JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### 3.3 Data Flow: Signal to Deployment

```
1. External signal enters Redis queue
2. Cortex worker pops signal → signal_ingest normalizes
3. signal_classify tags signal → signal_route applies conditional edge
4. cortex_decide (LLM) receives:
     - Classified signal
     - Active client profile (from PostgreSQL)
     - Campaign memory (pgvector similarity search)
     - Account pool status (PostgreSQL)
   → Produces CortexDecision
5. Dispatch formatted + sent to target ganglion sub-graph
6. Ganglion executes: account_select → context_load → content_gen → guardrail → schedule → deploy
7. Deployment written to deployments table
8. Monitor node watches (configurable window)
9. Report node writes to episodic_memory, triggers learn node
10. Learn node extracts lessons → semantic_memory update
```

### 3.4 State Management

| State | Storage | Durability |
|-------|---------|------------|
| Cortex active state | PostgreSQL (via PostgresSaver checkpointer) | Survives restart |
| Ganglion in-flight state | Ganglion sub-graph state (backed by same checkpointer) | Survives restart |
| Message queue backlog | Redis persistence (AOF) | Survives restart |
| Commander session | Discord (stateless) + Cortex state | N/A |
| Rate limit counters | Redis | Best effort |
| Account session cookies | HashiCorp Vault | Survives restart |

---

## 4. INTEGRATION ARCHITECTURE

### 4.1 External Integrations

| Integration | Protocol | Auth | Rate Limits | Fallback |
|-------------|----------|------|-------------|----------|
| Reddit API | HTTPS REST | OAuth2 per ghost account | 60 req/min per user | Playwright browser |
| Discord API | HTTPS REST + WebSocket | Bot token + user tokens | 50 req/sec per token | Playwright browser |
| TikTok API | HTTPS REST (future) | OAuth2 | TBD | Playwright browser |
| LLM (Claude/GPT) | HTTPS REST | API key | Provider-dependent | Secondary provider |
| Residential proxies | HTTPS proxy | IP whitelist + auth header | Per-plan bandwidth | Direct (risk accepted) |
| HashiCorp Vault | HTTPS REST | AppRole / token | N/A | Cloud KMS fallback |
| Discord (Commander) | WebSocket + HTTPS | Bot token | Discord rate limits | N/A |

### 4.2 Internal API (Cortex Service)

```yaml
# Signal ingestion endpoint
POST /api/v1/signals
  Body: { source, type, payload, timestamp }
  Response: { signal_id, status }

# Commander action endpoints (called by Discord bot)
POST /api/v1/commander/onboard
  Body: { client_url }
  Response: { client_id, profile, playbook_url }

POST /api/v1/commander/approve
  Body: { dispatch_id }
  Response: { status }

POST /api/v1/commander/reject
  Body: { dispatch_id, reason }
  Response: { status }

POST /api/v1/commander/kill
  Body: { target, scope }
  Response: { status, affected_resources }

# Status endpoints
GET /api/v1/status
  Response: { cortex, ganglia, accounts, active_campaigns }

GET /api/v1/status/client/{client_id}
  Response: { client_profile, campaigns, metrics }

GET /api/v1/memory/search
  Query: { query, client_id?, limit }
  Response: { results: [...] }
```

---

## 5. SECURITY ARCHITECTURE

### 5.1 Threat Model

| Threat | Severity | Mitigation |
|--------|----------|------------|
| Credential leak (ghost accounts) | Critical | Vault encryption, never in LLM context, rotation |
| Cross-client data leak | High | Per-client scoping, client_id in all queries |
| Platform detection (coordinated inauthentic behavior) | High | Proxy rotation, fingerprint diversity, timing jitter, behavioral variance |
| LLM prompt injection | Medium | Input sanitization, structured outputs (TypedDict), no raw LLM output used directly |
| Commander account compromise | Critical | Discord 2FA required, audit log on all /kill /approve |
| Supply chain (dependency compromise) | Medium | Pinned versions, SBOM, minimal dependency tree |
| Infrastructure access | Critical | IAM least privilege, VPC isolation, no public DB endpoints |

### 5.2 Cryptographic Requirements

| Data | Algorithm | Key Management |
|------|-----------|----------------|
| Credentials at rest | AES-256-GCM | Vault transit engine |
| Credentials in transit | TLS 1.3 | Standard certificate management |
| API keys at rest | AES-256-GCM | Vault KV v2 |
| Database encryption | AES-256 (RDS encryption) | AWS KMS / Cloud KMS |
| Training data at rest | AES-256 (S3 SSE) | AWS KMS / Cloud KMS |

---

## 6. MONITORING & OBSERVABILITY

### 6.1 Key Metrics

| Category | Metric | Alert Threshold |
|----------|--------|-----------------|
| **Business** | Client signups attributed | Below target for 7 days |
| **Business** | Content engagement rate | Below baseline for 3 days |
| **Operations** | Account ban rate | > 3 bans in 24h → auto /kill |
| **Operations** | Content approval queue depth | > 20 items pending > 4h |
| **Operations** | L3 kill window expiry rate | > 10% content killed |
| **Technical** | Cortex decide latency | > 30s p95 |
| **Technical** | LLM API error rate | > 5% of calls |
| **Technical** | Proxy failure rate | > 10% of requests |
| **Technical** | Database connection pool | > 80% utilization |
| **Cost** | LLM cost per deployment | > $0.15 |
| **Cost** | Total daily burn rate | > budget threshold |

### 6.2 Logging Standards

All logs structured as JSON with:
```json
{
  "timestamp": "ISO8601",
  "level": "INFO|WARN|ERROR|CRITICAL",
  "component": "cortex|reddit_ganglion|discord_ganglion|commander",
  "client_id": "string|null",
  "campaign_id": "string|null",
  "dispatch_id": "string|null",
  "action": "signal_classify|cortex_decide|content_generate|deploy|...",
  "message": "human-readable",
  "data": {},
  "trace_id": "uuid"
}
```

---

## 7. PERFORMANCE & SCALING

### 7.1 Capacity Planning

| Metric | Phase 1 | Phase 3 | Phase 4+ |
|--------|---------|---------|----------|
| Active clients | 1 | 3 | 10+ |
| Daily signals processed | 100 | 500 | 2,000+ |
| Daily deployments | 10 | 50 | 200+ |
| Ghost accounts | 5 | 15 | 50+ |
| LLM calls/minute | 5 | 20 | 80+ |
| DB queries/second | 10 | 50 | 200+ |
| Redis throughput | 100 ops/sec | 500 ops/sec | 2,000 ops/sec |

### 7.2 Scaling Strategy

| Component | Strategy | Trigger |
|-----------|----------|---------|
| Cortex Service | Horizontal (ECS task count) | CPU > 70%, queue depth > 50 |
| Ganglion Workers | Horizontal per ganglion type | Pending dispatches > 10 per ganglion |
| PostgreSQL | Vertical (RDS instance size) then read replicas | Connections > 80%, query latency > 50ms |
| Redis | Vertical (ElastiCache node size) then cluster | Memory > 70%, ops/sec approaching limit |
| LLM Calls | Provider-side scaling + multi-model | Latency > 10s, error rate > 1% |
| Proxy Pool | Add more residential IPs | Ban rate > 3%, IP reuse interval < 24h |

---

## 8. DISASTER RECOVERY

| Scenario | RPO | RTO | Recovery Procedure |
|----------|-----|-----|-------------------|
| PostgreSQL failure | 5 min (PITR) | 15 min | Promote read replica or restore from backup |
| Redis failure | 0 (in-flight signals lost) | 5 min | Promote replica, signals re-published by sources |
| Cortex service crash | 0 (state in DB) | 2 min | ECS auto-restart, checkpointer replays state |
| All infra region loss | 1 hour | 1 hour | Multi-region deployment, Route53 failover |
| LLM provider outage | N/A | 5 min | Automatic failover to secondary provider |
| Proxy provider outage | N/A | 5 min | Failover to secondary proxy pool |

---

*This ARD defines the architecture that implements the requirements in BRD.md. SPEC.md defines the detailed functional and non-functional requirements. Any architectural change requires an ADR update and Commander sign-off.*
