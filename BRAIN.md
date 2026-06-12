# 🧠 BRAIN.md — ECHO CHAMBER CENTRAL NERVOUS SYSTEM

> *"We don't hire an army. We build one. Then we teach it to think."*

---

## 0. THE MANIFESTO

**ECHO CHAMBER is not a marketing tool. It is an intelligence agency whose mission is distribution.**

Every choice in this architecture serves three masters:

| DNA | What It Means Here |
|-----|--------------------|
| 🥷 **Suge Knight** | We own every room we enter. Gatekeepers are obstacles, not authorities. Distribution is power. |
| 🕵️ **CIA** | Intelligence first, action second. We infiltrate communities. We deploy assets that blend. We know the battlefield before we move. |
| 🏛️ **Civic Duty** | The product must be provably good. No dark patterns. No lies. No scams. The architecture enforces this, not just the policy. |

**Enterprise-grade from day one.** This document is the single source of truth for the system. AI agents read it to understand their role. Human operators read it to understand the machine they command. Future clients read it to understand what they're buying.

---

## I. ARCHITECTURAL PRINCIPLES

### 1. Echo Chamber Owns Strategy. Clients Own Constraints.

```
┌──────────────────────────────┐
│       ECHO CHAMBER            │
│  (built once, services N)     │
│                               │
│  OWNS:                        │
│  • Channel selection          │
│  • Tactic deployment          │
│  • Voice & tone               │
│  • Autonomy decisions         │
│  • Success measurement        │
│  • Account infrastructure     │
└──────────┬───────────────────┘
           │
    ┌──────┴──────┐
    │             │
┌───┴───┐   ┌───┴────┐
│Client │   │Client  │
│ #001  │   │ #002   │
│       │   │        │
│ GIVES:│   │ GIVES: │
│ • URL │   │ • URL  │
│ • $$$ │   │ • $$$  │
│ • No-go│   │ • No-go│
└───────┘   └────────┘
```

### 2. The Brain Is Not the Operator. The Brain Is the Weapon.

Human commanders set rules. The Cortex enforces them. Ganglia execute. Never the other way around.

### 3. Every Action Is Evidence.

The brain logs everything — every signal, every decision, every deployment, every outcome. This is for learning. This is for accountability. This is for when the client asks "why did we do that?" and the Cortex produces the full decision trail.

### 4. Voice Is Injected, Not Baked In.

The system is product-agnostic. Client voice, tone, hooks, and forbidden angles are injected at runtime. No retraining required to onboard a new client. This is why we build once and service forever.

### 5. Data Collection Is Training.

Every deployment — win, loss, or ban — becomes training data. Fine-tuning comes later. The pipeline collects from day one.

---

## II. TOPOLOGY: CORTEX + GANGLIA (HYBRID)

```
                         ┌──────────────────┐
                         │    COMMANDER     │
                         │  (Discord UI)    │
                         │                  │
                         │  Human operators │
                         └────────┬─────────┘
                                  │
                                  ▼
                    ┌─────────────────────────┐
                    │        CORTEX           │
                    │   (LangGraph StateGraph) │
                    │                         │
                    │  • Signal classification │
                    │  • Decision routing      │
                    │  • Autonomy gates        │
                    │  • Escalation logic      │
                    │  • Global state          │
                    │  • Multi-client state    │
                    └──────────┬──────────────┘
                               │
        ┌──────────────────────┼──────────────────────┐
        │                      │                      │
        ▼                      ▼                      ▼
┌───────────────┐    ┌───────────────┐    ┌───────────────┐
│   REDDIT      │    │   DISCORD     │    │  TIKTOK       │
│   GANGLION    │    │   GANGLION    │    │  GANGLION     │
│               │    │               │    │               │
│  Sub-graph    │    │  Sub-graph    │    │  (future)     │
│  • Account sel│    │  • Infiltrator│    │               │
│  • Content gen│    │  • Community  │    │               │
│  • Guardrails │    │  • Auto-resp  │    │               │
│  • Deploy     │    │  • Sentiment  │    │               │
│  • Monitor    │    │               │    │               │
└───────────────┘    └───────────────┘    └───────────────┘
        │                      │
        └──────────────────────┼────────── ...
                               │
                    ┌──────────┴──────────┐
                    │     DATA LAKE       │
                    │                     │
                    │  • pgvector (memory) │
                    │  • PostgreSQL (state)│
                    │  • Training corpus   │
                    │  • Analytics         │
                    └─────────────────────┘
```

---

## III. CORTEX — THE CENTRAL NERVOUS SYSTEM

### 3.1 StateGraph Definition

The Cortex is a LangGraph `StateGraph`. It is the single source of truth for all active operations.

```python
from typing import TypedDict, List, Dict, Optional, Literal
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.postgres import PostgresSaver

class CortexState(TypedDict):
    # ── Multi-Client ──────────────────────
    active_clients: Dict[str, "ClientProfile"]
    current_focus: Optional[str]

    # ── Signal Pipeline ───────────────────
    signals: List["Signal"]
    signal_backlog: List["Signal"]

    # ── Active Operations ─────────────────
    campaigns: Dict[str, "Campaign"]
    dispatches: List["Dispatch"]
    escalations: List["Escalation"]

    # ── Global Resources ──────────────────
    account_pool: "AccountPool"
    platform_health: Dict[str, "PlatformStatus"]

    # ── Memory ────────────────────────────
    episodic_memory: "CampaignMemory"
    semantic_memory: "KnowledgeBase"
    threat_log: List["ThreatEvent"]

    # ── Guardrails ────────────────────────
    global_guardrails: "GuardrailConfig"
    autonomy_mode: Literal["full_auto", "auto_with_override", "queue", "manual"]
```

### 3.2 Core Nodes

| Node | Function | LLM Required |
|------|----------|-------------|
| `signal_ingest` | Receive signal from webhook/stream, normalize schema | No |
| `signal_classify` | Tag signal: trend, mention, opportunity, threat, noise | Yes (small) |
| `signal_route` | Conditional edge: route signal to appropriate handler | No (rules) |
| `cortex_decide` | Given classified signal + client context, decide action | Yes (large) |
| `dispatch` | Format and send task to target ganglion | No |
| `escalate` | Queue for human review in Discord | No |
| `learn` | After campaign completes, extract lessons → memory | Yes (medium) |
| `health_check` | Periodic: scan account pool, platform status, rate limits | No |

### 3.3 Graph Edges

```
[SIGNAL_INGEST]
      │
      ▼
[SIGNAL_CLASSIFY] ──→ (classification = noise) ──→ END
      │
      ▼
[SIGNAL_ROUTE] ── conditional edge ──┐
      │                              │
      ├── trend     → [CORTEX_DECIDE]
      ├── mention   → [CORTEX_DECIDE]
      ├── threat    → [ESCALATE] → END
      └── noise     → END
             │
             ▼
      [CORTEX_DECIDE]
             │
      ┌──────┴──────┐
      │             │
      ▼             ▼
 [DISPATCH]    [ESCALATE]
      │             │
      ▼             ▼
 [Ganglion]    [Commander]
      │             │
      ▼             ▼
 [MONITOR]      [Human decision]
      │             │
      ▼             │
 [LEARN] ←─────────┘
      │
      ▼
     END
```

### 3.4 Cortex Decide — The Core Reasoning Loop

This is the heaviest LLM call in the system. It receives:

**Input:**
- Classified signal
- Active client profile (voice, channels, constraints, budget)
- Campaign memory (what worked before for this audience)
- Account pool status (which accounts are available)
- Platform health (any bans? rate limits?)

**Output:**
```python
class CortexDecision(TypedDict):
    decision_id: str
    action: Literal["deploy", "queue", "escalate", "ignore", "monitor"]
    rationale: str                    # Explainable — this is evidence
    ganglions: List[str]              # Which ganglia to dispatch
    content_params: "ContentParams"   # Voice, hooks, format
    autonomy_level: int               # 0-4
    priority: int                     # 1-5
    suggested_timing: Optional[str]   # "now" or ISO timestamp
```

### 3.5 Autonomy Levels

The brain operates on a 5-level autonomy spectrum. The Commander sets the default. The Cortex can upgrade/downgrade per signal.

| Level | Name | Who Acts | Example |
|-------|------|----------|---------|
| **L0** | Full Manual | Commander does everything | Crisis response, launch announcements |
| **L1** | Suggest | Brain drafts → Commander edits and posts | Official subreddit posts |
| **L2** | Queue | Brain generates + schedules → Commander approves batch | Ghost posts, community content |
| **L3** | Auto + Override | Brain deploys → Commander can kill within window | Ghost comments, meme replies |
| **L4** | Full Auto | Brain detects, creates, deploys, measures | Low-risk engagement, reposts |

**Default mapping:**
- Tier 1 content (official brand voice, high-visibility posts) → L1-L2
- Tier 2 content (ghost accounts, community engagement) → L3
- Tier 3 content (reposts, meme replies, routine engagement) → L4
- Threat/Crisis → Always L0

---

## IV. CLIENT ONBOARDING — THE INGESTION NODE

Before Echo Chamber can deploy for any client, the Cortex must analyze the product and generate the operational profile. This is a one-time LangGraph sub-graph, triggered on new client ingestion.

### 4.1 Onboarding Pipeline

```
[Client URL submitted]
         │
         ▼
┌─────────────────────┐
│ PRODUCT ANALYSIS     │  ← LLM scrapes + analyzes landing page
│                     │    Features, pricing, positioning, claims
└─────────┬───────────┘
          ▼
┌─────────────────────┐
│ AUDIENCE MAPPER      │  ← LLM + web search identifies:
│                     │    Who buys this? Where do they hang out?
│                     │    What do they complain about? What do they love?
└─────────┬───────────┘
          ▼
┌─────────────────────┐
│ CHANNEL SELECTION    │  ← Echo Chamber logic selects:
│                     │    Which platforms? Which communities?
│                     │    Priority ordering. Required account specs.
└─────────┬───────────┘
          ▼
┌─────────────────────┐
│ VOICE PROFILE        │  ← LLM generates:
│                     │    Tone, vocabulary, hook archetypes
│                     │    Forbidden angles, brand safety rules
└─────────┬───────────┘
          ▼
┌─────────────────────┐
│ PLAYBOOK DRAFT       │  ← First 30-day campaign:
│                     │    Content calendar, account assignments,
│                     │    KPI targets, budget allocation
└─────────┬───────────┘
          ▼
┌─────────────────────┐
│ HUMAN REVIEW         │  ← Commander reviews + adjusts
│                     │    Playbook + profile sent to client
│                     │    Client approves → stored in Cortex
└─────────┬───────────┘
          ▼
     [PROFILE STORED]
          │
          ▼
     [READY FOR OPS]
```

### 4.2 Client Profile Schema

```python
class ClientProfile(BaseModel):
    client_id: str
    product_url: str
    onboarded_at: datetime

    # ── Echo Chamber Generated ──────────────
    target_audiences: List[Audience]
    channel_map: Dict[Platform, List[Community]]
    voice_profile: VoiceProfile
    content_strategy: ContentStrategy
    account_requirements: Dict[Platform, int]   # "reddit": 7, "discord": 3

    # ── Client Supplied ─────────────────────
    pricing: List[PriceTier]
    forbidden_topics: List[str]
    budget: Budget
    kpi_weights: Dict[str, float]   # e.g. {"signups": 0.6, "mentions": 0.2, "sentiment": 0.2}

    # ── Operational ────────────────────────
    status: Literal["onboarding", "active", "paused", "offboarded"]
    campaign_history: List[str]     # campaign IDs
    current_campaign: Optional[str]
```

### 4.3 Voice Profile Schema

```python
class VoiceProfile(BaseModel):
    persona: str                    # "Blue-collar trucker who got tired of broker BS"
    tone: List[str]                 # ["direct", "respectful", "no-corporate-BS"]
    vocabulary: List[str]           # Words that land for this audience
    avoid: List[str]                # Words/phrases that smell corporate
    hook_archetypes: List[str]      # Top-3 hook types that convert
    forbidden_angles: List[str]     # "Never badmouth specific brokers by name"
    brand_safety_rules: List[str]   # "Never claim FDA/regulatory endorsement"
    proof_points: List[str]         # "Free tier is free forever, no card required"
```

---

## V. GANGLIA — AUTONOMOUS SUB-GRAPHS

Each ganglion is a compiled LangGraph sub-graph. The Cortex dispatches a mission with `Command(go_to=ganglion_name)`. The ganglion executes autonomously within guardrails and reports back.

### 5.1 Reddit Ganglion

```
[Dispatch received from Cortex]
         │
         ▼
┌─────────────────────┐
│ ACCOUNT SELECTOR     │  ← Query account pool:
│                     │    karma, subreddit history, cooldown, fingerprint match
│                     │    Returns: best account_id for this deployment
└─────────┬───────────┘
          ▼
┌─────────────────────┐
│ CONTEXT LOADER       │  ← Fetch current state of target subreddit:
│                     │    Top posts, trending topics, mod activity,
│                     │    recent bans, current sentiment
└─────────┬───────────┘
          ▼
┌─────────────────────┐
│ CONTENT GENERATOR    │  ← LLM call with:
│                     │    Voice profile injected
│                     │    Subreddit context injected
│                     │    Campaign parameters injected
│                     │  Returns: post title + body + comment strategy
└─────────┬───────────┘
          ▼
┌─────────────────────┐
│ GUARDRAIL CHECK      │  ← Validate:
│                     │    Platform ToS compliance
│                     │    Client forbidden topics
│                     │    Rate limits on selected account
│                     │    Plagiarism check
└─────────┬───────────┘
          ▼
    ┌─────┴─────┐
    │ Autonomy? │
    │ L1/L2?    │──── Yes ───→ [HUMAN GATE] → Discord approval queue
    │ L3/L4?    │
    └─────┬─────┘
          │ No
          ▼
┌─────────────────────┐
│ SCHEDULER            │  ← Optimal posting time:
│                     │    Platform-specific timing model
│                     │    Avoid posting near other Echo Chamber content
│                     │    Respect account cooldown windows
└─────────┬───────────┘
          ▼
┌─────────────────────┐
│ DEPLOY               │  ← Execute:
│                     │    Reddit API (preferred) or Playwright fallback
│                     │    Rotate proxy per account
│                     │    Log deployment to campaign DB
└─────────┬───────────┘
          ▼
┌─────────────────────┐
│ MONITOR              │  ← Watch 24-72 hours:
│                     │    Upvotes, comments, reports, removals
│                     │    Reply to comments (L3/L4 auto, L1/L2 queue)
│                     │    Flag anomalies (vote manipulation detection)
└─────────┬───────────┘
          ▼
┌─────────────────────┐
│ REPORT               │  ← Send structured result to Cortex:
│                     │    Metrics, anomalies, account health update
│                     │    Trigger LEARN node for memory update
└─────────────────────┘
```

**Reddit Ganglion State:**
```python
class RedditGanglionState(TypedDict):
    dispatch: Dispatch
    client_profile: ClientProfile
    voice_profile: VoiceProfile
    target_subreddit: str
    content_params: ContentParams
    autonomy_level: int
    
    # Internal
    selected_account: Optional[Account]
    subreddit_context: Optional[SubredditContext]
    generated_content: Optional[GeneratedContent]
    guardrail_result: Optional[GuardrailResult]
    deployment_result: Optional[DeploymentResult]
    monitor_result: Optional[MonitorResult]
```

### 5.2 Discord Ganglion

The Discord ganglion operates in two modes, selectable by dispatch type:

```
                     ┌─────────────────────┐
                     │  DISCORD GANGLION   │
                     └──────────┬──────────┘
                                │
              ┌─────────────────┴─────────────────┐
              │                                   │
              ▼                                   ▼
┌──────────────────────────┐      ┌──────────────────────────┐
│   INFILTRATOR MODE        │      │   COMMUNITY MODE          │
│                           │      │                           │
│  • Join target servers    │      │  • Own server management  │
│  • Lurk → participate     │      │  • Auto-welcome new users │
│  • Build trust            │      │  • Product Q&A support    │
│  • Natural product mention│      │  • Sentiment monitoring   │
│  • Detect buying signals  │      │  • Escalate issues        │
│                           │      │  • Cross-post content     │
└──────────────────────────┘      └──────────────────────────┘
```

**Infiltrator Mode Nodes:**
1. **Server Discovery** — Find Discord servers matching client's target audience
2. **Join + Lurk** — Join server, establish presence, learn culture
3. **Participation Engine** — LLM generates natural conversation in server's voice
4. **Opportunity Detector** — Monitor for buying signals ("anyone know a good app for...")
5. **Mention Deploy** — Natural product mention, not a pitch
6. **Trust Score Tracker** — How established is this account in this server?

**Community Mode Nodes:**
1. **Welcome Engine** — Auto-DM new members with onboarding flow
2. **Support Router** — Answer product questions, escalate complex issues
3. **Announcement Sync** — Cross-post Reddit/GitHub/product updates
4. **Sentiment Monitor** — Detect unhappy users, flag for human intervention
5. **Engagement Events** — Schedule AMAs, feedback threads, community events

---

## VI. COMMANDER — THE DISCORD INTERFACE

The Commander is Discord. No web app. No separate dashboard. The Discord server IS the command center.

### 6.1 Channel Architecture

```
ECHO CHAMBER COMMAND SERVER
├── #📡 signals-feed        Real-time intel stream
├── #🎯 active-campaigns    What's running + status
├── #✅ approval-queue      Content waiting for Commander
├── #🚨 escalation          Threats, bans, crises
├── #📊 daily-sitrep        Auto-generated EOD summary
├── #🗣️ commander-chat      Direct Cortex interaction
├── #📋 client-vault        Per-client channel (one per active client)
│   ├── #client-truckerechelon
│   └── #client-future-client
└── #⚙️ system-health        Cortex, ganglia, account pool status
```

### 6.2 Commander Commands

All commands are Discord slash commands or prefix-based (`!command`).

**Status & Intel:**
```
/status                     → Full system dashboard
/status reddit              → Reddit ganglion status: accounts, campaigns, health
/status discord             → Discord ganglion status
/status client [name]       → Client profile + active campaigns
/status accounts            → Account pool: count, health, cooldowns
/memory search [query]      → Search episodic memory: "what worked on r/Truckers?"
```

**Approval & Control:**
```
/approve [dispatch_id]      → Approve queued content
/reject [dispatch_id] [why] → Reject with feedback for Cortex
/edit [dispatch_id] [text]  → Modify before approve
/pause all                  → Freeze all ganglia immediately
/pause reddit               → Freeze Reddit ganglion only
/resume all                 → Resume
/boost [campaign_id]        → Escalate to L3 auto, increase frequency
/kill [dispatch_id]         → Delete deployed content + burn account if needed
```

**Client Operations:**
```
/onboard [url]              → Start client onboarding pipeline
/client [name] status       → Client operational status
/client [name] report       → Generate performance report
/client [name] pause        → Pause all operations for client
/client [name] offboard     → Graceful offboarding
```

**Direct Cortex Query:**
```
/cortex ask [question]      → RAG query over playbook + memory + state
```

### 6.3 Alert Format

All automated messages use a consistent embed format:

```yaml
Signal Alert:
  Title: "Rising trend: r/Truckers IFTA complaints"
  Type: trend
  Velocity: 87/100
  Recommended: deploy "IFTA pain" meme to Reddit L3
  Decision: AUTO-DEPLOYED in 2 min unless /kill

Approval Request:
  Title: "Ghost post for r/owneroperators"
  Content: [preview]
  Account: Ghost #7 (1.2k karma, 4mo age)
  Autonomy: L2 — needs approval
  Buttons: [Approve] [Reject] [Edit]

Escalation:
  Title: "🚨 Ghost #3 banned from r/Truckers"
  Severity: HIGH
  Impact: 1 of 5 Reddit accounts offline
  Action: Burn account, rotate proxy, deploy replacement
  Buttons: [Confirm Burn] [Investigate]
```

---

## VII. MEMORY ARCHITECTURE

The brain doesn't just execute — it learns. Three memory systems, two operational modes.

### 7.1 Memory Stores

| Store | Backend | Contents | Query Pattern |
|-------|---------|----------|---------------|
| **Episodic** | pgvector | Every campaign, every deployment, every outcome | "Show me Reddit posts with >100 upvotes in trucking communities" |
| **Semantic** | pgvector | Extracted patterns: "Truckers respond to pain-point hooks more than feature list hooks" | "What hooks work for blue-collar audiences?" |
| **Procedural** | PostgreSQL | Current state: account health, active campaigns, client profiles | "Which Reddit accounts are available right now?" |

### 7.2 Learning Loop

After every campaign/deployment:
```
[DEPLOYMENT COMPLETE]
         │
         ▼
[EXTRACT OUTCOMES]  →  metrics, sentiment, conversions
         │
         ▼
[GENERATE LESSONS]  →  LLM: "What worked? What didn't? Why?"
         │
         ▼
[STORE EPISODIC]    →  pgvector: full campaign record with embedding
         │
         ▼
[UPDATE SEMANTIC]   →  aggregate patterns: update knowledge graph
         │
         ▼
[UPDATE PROCEDURAL] →  account health, platform status, cooldowns
```

### 7.3 Cross-Client Learning

Lessons from TruckerEchelon benefit future clients. If "blue-collar audiences respond to pain-point hooks" holds across clients, it becomes a first-class rule in the Cortex decision node. The semantic memory is shared. Episodic memory is client-scoped. Procedural memory is global.

### 7.4 Fine-Tuning Data Pipeline (Future)

Every piece of generated content is logged with:

```python
class TrainingRecord(BaseModel):
    timestamp: datetime
    client_id: str
    platform: str
    prompt: str                      # Full LLM prompt
    voice_injection: VoiceProfile    # Active voice profile
    generated_content: str           # What the LLM produced
    human_edited: Optional[str]      # If Commander edited it
    deployed: bool
    outcome: DeploymentResult        # Metrics
    lesson: Optional[str]            # Post-hoc analysis
```

This becomes the LoRA fine-tuning dataset for product-specific voice optimization. **Not now. Collection starts now.**

---

## VIII. GUARDRAILS — THE CIVIC DUTY LAYER

This is not optional. This is not configurable by clients. This is the constitution.

### 8.1 Hard Guards (System Enforced — No Override)

| Rule | Enforcement |
|------|-------------|
| No fake reviews or testimonials | Content validator blocks any review-like text unless sourced from real user |
| No impersonation of real individuals | Account persona must be fictional, verified against known individuals DB |
| No false claims about competitors | Competitor name detection → block |
| No dark patterns or deception | Funnel validator: must disclose affiliate relationship |
| No content targeting minors | Audience age gate in targeting logic |
| #ad disclosure on all affiliate content | Auto-appended, cannot be stripped |

### 8.2 Soft Guards (Commander Configurable)

| Rule | Default | Overridable |
|------|---------|-------------|
| Maximum posting frequency per account | 3/day | Yes |
| Minimum account age before deployment | 90 days | Yes (risk accepted) |
| Content queue L2 for first 30 days of client | On | Yes |
| Swearing/casual language intensity | Medium | Per client voice |
| Mention of specific competitor names | Blocked | Yes (with rationale) |

### 8.3 Emergency Kill Switch

```
/kill all
  → All ganglia freeze
  → All scheduled posts cancelled
  → All ghost accounts set to dormant
  → Commander notified across all channels
  → Requires Commander to /resume

Trigger conditions:
  • Manual: Commander issues /kill
  • Automatic: 3+ account bans in 24h
  • Automatic: Legal escalation detected
  • Automatic: Platform rule change that invalidates current tactics
```

---

## IX. SECURITY & OPSEC

### 9.1 Account Isolation

No two ghost accounts may share:
- IP address (rotated per session)
- Browser fingerprint
- Device profile
- Payment method
- Recovery email
- Recovery phone
- Creation timestamp (staggered creation dates)

### 9.2 Credential Management

- Ghost account credentials: encrypted at rest (AWS KMS / HashiCorp Vault)
- Access logged, auditable
- Account credentials never exposed to LLM prompts
- Rotation: credentials rotated every 90 days or on burn event

### 9.3 Proxy Architecture

```
                    ┌──────────────┐
                    │ Proxy Router │
                    └──────┬───────┘
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
        ▼                  ▼                  ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│ Residential  │  │ Residential  │  │ Residential  │
│ Pool A       │  │ Pool B       │  │ Pool C       │
│ (US East)    │  │ (US Central) │  │ (US West)    │
│              │  │              │  │              │
│ Reddit       │  │ Discord      │  │ Reddit       │
│ Ghosts 1-5   │  │ Ghosts 1-3   │  │ Ghosts 6-10  │
└──────────────┘  └──────────────┘  └──────────────┘
```

### 9.4 Data Retention

| Data | Retention | Rationale |
|------|-----------|-----------|
| Content generated | Indefinite | Training corpus |
| Deployment metrics | Indefinite | Cross-client learning |
| Account credentials | Until rotation | Ops necessity |
| Client data | Duration of contract + 90 days | Client obligations |
| Conversation logs | 90 days | Debug + compliance |

---

## X. TECHNOLOGY STACK

### 10.1 Core Infrastructure

| Component | Technology | Why |
|-----------|------------|-----|
| **Agent Framework** | LangGraph + LangChain | StateGraph for Cortex, sub-graphs for ganglia, memory store integration |
| **LLM Provider** | Claude (Anthropic) / GPT-4 (OpenAI) | Cortex reasoning needs top-tier reasoning |
| **Small LLM** | Claude Haiku / GPT-4o-mini | Classifier, guardrail, simple generation |
| **Vector DB** | pgvector (PostgreSQL) | Same DB for structured + vector — less infra |
| **Relational DB** | PostgreSQL | Accounts, clients, campaigns, state |
| **Message Queue** | Redis / RabbitMQ | Signal ingestion, inter-ganglion communication |
| **Workflow Engine** | LangGraph built-in + Temporal (future) | LangGraph handles graph execution; Temporal for long-running campaign orchestration |
| **Browser Automation** | Playwright | Reddit/Discord posting where APIs are insufficient |
| **Platform APIs** | PRAW (Reddit), discord.py | Preferred over browser where available |
| **Proxy Network** | BrightData / Oxylabs / IPRoyal | Residential rotating proxies |
| **Monitoring** | Grafana + Prometheus | System health, cost tracking, anomaly detection |
| **Secrets** | HashiCorp Vault / cloud KMS | Credentials, API keys |

### 10.2 LangGraph Features in Use

| Feature | How We Use It |
|---------|---------------|
| `StateGraph` | Cortex central state machine |
| `CompiledGraph` / `SubGraph` | Each ganglion is a compiled sub-graph |
| `conditional_edges` | Signal routing: trend vs threat vs mention |
| `Command(go_to=...)` | Cortex redirects to specific ganglia |
| `interrupt()` | Human-in-the-loop: L1/L2 approval gates |
| `Checkpointer` (PostgresSaver) | Persist Cortex + ganglion state between runs |
| `MemoryStore` | Long-term episodic + semantic memory |
| `Streaming` (`astream_events`) | Real-time Commander dashboard updates |
| `ToolNode` | Platform API calls, scraping, content validation |

---

## XI. BUILD PHASES

### Phase 1 — Foundation (Month 1)
- [ ] Cortex skeleton: StateGraph with signal_ingest, classify, route
- [ ] Cortex decide: basic LLM decision node
- [ ] Client onboarding pipeline: URL → profile
- [ ] Reddit ganglion: single account, single subreddit, L1/L2 only
- [ ] Discord Commander: approval queue, daily sitrep, `/status`
- [ ] PostgreSQL + pgvector: schema, episodic memory store
- [ ] **Pilot:** Onboard TruckerEchelon, generate playbook, first manual campaign

### Phase 2 — Discord Ganglion + Scaling (Month 2)
- [ ] Discord ganglion: Infiltrator mode (join servers, participation engine)
- [ ] Discord ganglion: Community mode (own server, auto-welcome, support router)
- [ ] Reddit ganglion: 5-ghost pool, L3 auto for comments
- [ ] Escalation channel + kill switch implementation
- [ ] Semantic memory extraction (LLM generates lessons from campaigns)
- [ ] Cross-platform coordination (Reddit + Discord same-message timing)

### Phase 3 — Multi-Client + Autonomy (Month 3)
- [ ] Cortex handles 2+ active clients simultaneously
- [ ] Reddit L3 auto-deploy for ghost posts
- [ ] Fine-tuning data pipeline: TrainingRecord collection active
- [ ] Client performance reporting: automated reports
- [ ] Account health predictive monitoring (pre-emptive ban detection)

### Phase 4+ — Full Network (Month 4+)
- [ ] TikTok ganglion
- [ ] X (Twitter) ganglion
- [ ] Newsletter ganglion
- [ ] YouTube ganglion
- [ ] Full L4 autonomy with confidence thresholds
- [ ] LoRA fine-tuning per client voice
- [ ] Client self-service onboarding

---

## XII. GLOSSARY

| Term | Definition |
|------|------------|
| **Cortex** | The central LangGraph StateGraph — decides, routes, escalates |
| **Ganglion** | Autonomous sub-graph for a single platform (Reddit, Discord, etc.) |
| **Commander** | Human operator interface (Discord) |
| **Signal** | Any inbound intel — trend, mention, threat, opportunity |
| **Dispatch** | A task sent from Cortex to a Ganglion |
| **Ghost Account** | Fictional persona account used for distribution |
| **Voice Profile** | Client-specific tone, vocabulary, hooks — injected at runtime |
| **Client Profile** | Full operational spec for a client — generated by onboarding |
| **Autonomy Level** | L0-L4: how much the brain does without human approval |
| **Guardrail** | Hard (system-enforced) or soft (configurable) content/behavior rules |
| **Burn** | Permanently retire a ghost account and rotate credentials |
| **Blackboard** | The shared CortexState that all ganglia read/write |

---

*This document is the constitution of the ECHO CHAMBER brain. Every agent — silicon or carbon — operates under its rules. Amendments require Commander approval. The DNA is non-negotiable.*
