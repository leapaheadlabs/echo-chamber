# Kanban — ECHO CHAMBER

<!-- Config: Last Task ID: 040 -->

## ⚙️ Configuration

**Columns**: 📝 Backlog | 📋 To Do | 🚀 In Progress | 👀 Review | ✅ Done
**Categories**: Cortex, Reddit Ganglion, Discord Ganglion, Commander, Memory, Account Mgmt, Infra, Guardrails, Onboarding, Documentation
**Users**: @larry (Commander), @command (Command Agent)
**Tags**: #phase-1, #phase-2, #phase-3, #phase-4, #critical-path, #truckerechelon, #pilot, #blocked

---

## 📝 Backlog

### TASK-030 | LoRA fine-tuning pipeline for voice profiles

**Priority**: Low | **Category**: Memory | **Assigned**: @command
**Created**: 2026-06-12
**Tags**: #phase-4

LangChain fine-tuning pipeline: training data curation, LoRA config, evaluation benchmark, model registry.

**Subtasks**:
- [ ] Curate training corpus from episodic memory (>1000 deployments)
- [ ] Define LoRA adapter architecture per client
- [ ] Build training pipeline with LangChain + Hugging Face
- [ ] Create evaluation benchmark (voice consistency, conversion rate)
- [ ] Model registry for versioned voice adapters
- [ ] Hot-swap adapters without Cortex restart

---

### TASK-031 | TikTok Ganglion

**Priority**: Low | **Category**: Reddit Ganglion | **Assigned**: @command
**Created**: 2026-06-12
**Tags**: #phase-4

Short-form video infiltrator: content generation (AI video/audio), trend detection, stitch/duet tactics, comment strategy.

---

### TASK-032 | X/Twitter Ganglion

**Priority**: Low | **Category**: Reddit Ganglion | **Assigned**: @command
**Created**: 2026-06-12
**Tags**: #phase-4

Tweet/reply infiltrator: real-time trend injection, thread posting, reply-to-signal-virality, community building. X API v2 integration.

---

### TASK-033 | YouTube Ganglion

**Priority**: Low | **Category**: Reddit Ganglion | **Assigned**: @command
**Created**: 2026-06-12
**Tags**: #phase-4

Long-form content infiltrator: comment strategy, video response detection, community tab utilization, tutorial/value content generation.

---

### TASK-034 | Newsletter Ganglion

**Priority**: Low | **Category**: Reddit Ganglion | **Assigned**: @command
**Created**: 2026-06-12
**Tags**: #phase-4

Substack/Beehiiv infiltrator: email persona generation, cross-promotion detection, comment engagement, guest post opportunities.

---

### TASK-035 | Automated ghost account creation

**Priority**: Low | **Category**: Account Mgmt | **Assigned**: @command
**Created**: 2026-06-12
**Tags**: #phase-3

Browser automation for Reddit/Discord account signup: randomized persona generation, email verification, initial warming period.

---

### TASK-036 | Multi-Commander role-based access

**Priority**: Low | **Category**: Commander | **Assigned**: @command
**Created**: 2026-06-12
**Tags**: #phase-4

Role hierarchy beyond Commander/Observer: campaign-manager, analyst, operator. Audit log per role.

---

### TASK-037 | Echo Chamber-owned Discord server templates

**Priority**: Low | **Category**: Discord Ganglion | **Assigned**: @command
**Created**: 2026-06-12
**Tags**: #phase-3

Pre-built server templates for client onboarding: channels, roles, welcome flow, FAQ bot, announcement system.

---

### TASK-038 | Client self-service portal

**Priority**: Low | **Category**: Onboarding | **Assigned**: @command
**Created**: 2026-06-12
**Tags**: #phase-4

Web portal for clients to: submit product URL, see campaign status, view reports, adjust budget.

---

### TASK-039 | Payment/billing integration

**Priority**: Low | **Category**: Infra | **Assigned**: @command
**Created**: 2026-06-12
**Tags**: #phase-4

Stripe integration for client billing: usage-based pricing, invoice generation, payment tracking.

---

### TASK-040 | Disaster recovery & cross-region failover

**Priority**: Medium | **Category**: Infra | **Assigned**: @command
**Created**: 2026-06-12
**Tags**: #phase-3

Multi-region PostgreSQL read replicas, Cortex failover, LLM provider auto-switch, proxy pool redundancy. RTO < 1 hour, RPO < 5 minutes.

---

## 📋 To Do

### TASK-005 | Project skeleton — LangGraph scaffold, FastAPI, PostgreSQL, Docker

**Priority**: Critical | **Category**: Infra | **Assigned**: @command
**Created**: 2026-06-12
**Tags**: #phase-1 #critical-path

Initialize the full project skeleton. Everything else builds on this.

**Subtasks**:
- [ ] Initialize Python project with Poetry (LangGraph + LangChain + FastAPI + PRAW + discord.py)
- [ ] Docker Compose: Cortex service, PostgreSQL 16, pgvector, Redis
- [ ] FastAPI skeleton with health endpoint, OpenAPI docs
- [ ] PostgreSQL schema: signals, deployments, accounts, clients, episodic_memory, semantic_memory
- [ ] pgvector extension setup + embedding table
- [ ] LangGraph StateGraph scaffold (empty graph, test invoke)
- [ ] Environment/config management (pydantic-settings)
- [ ] CI/CD: GitHub Actions for lint + test on PR
- [ ] Pre-commit hooks: black, ruff, mypy

---

### TASK-006 | Cortex core — StateGraph with all 8 nodes

**Priority**: Critical | **Category**: Cortex | **Assigned**: @command
**Created**: 2026-06-12
**Tags**: #phase-1 #critical-path

Implement the Cortex StateGraph: signal_ingest → classify → route → decide → escalate → dispatch → learn → health_check.

**Subtasks**:
- [ ] CortexState TypedDict with all fields from SPEC.md
- [ ] signal_ingest node: normalize input to Signal object
- [ ] classify node: LLM classification (trend/mention/opportunity/threat/noise)
- [ ] route node: conditional edges based on classification
- [ ] decide node: LLM decision engine with full context injection
- [ ] escalate node: create Escalation record, Discord notification
- [ ] dispatch node: forward CortexDecision to target ganglion(s)
- [ ] learn node: extract lessons from completed deployments
- [ ] health_check node: periodic account pool + API health scan

---

### TASK-007 | Signal ingestion + classification pipeline

**Priority**: Critical | **Category**: Cortex | **Assigned**: @command
**Created**: 2026-06-12
**Tags**: #phase-1 #critical-path

Ingest signals from Reddit PRAW (hot/rising posts), RSS feeds, and manual Commander input. Classify with small LLM.

**Subtasks**:
- [ ] Reddit signal scanner: poll target subreddits via PRAW, detect new trending posts
- [ ] RSS feed ingester: configurable feed list, poll every 5 min
- [ ] Manual signal endpoint: Commander submits signal via Discord → REST → Cortex
- [ ] Signal deduplication (same source + timestamp = skip)
- [ ] Small LLM classifier (Haiku/GPT-4o-mini): classify as trend/mention/opportunity/threat/noise
- [ ] Confidence scoring: low confidence (<0.6) routes to escalate
- [ ] Dead letter queue for malformed signals

---

### TASK-008 | Cortex decision engine

**Priority**: Critical | **Category**: Cortex | **Assigned**: @command
**Created**: 2026-06-12
**Tags**: #phase-1 #critical-path

Large-model LLM decision: given signal + full context, produce CortexDecision with action, ganglions, content params, autonomy level.

**Subtasks**:
- [ ] Context assembler: client profile + voice + constraints + campaign memory + account pool
- [ ] Decision prompt template (from SPEC.md FR-CX-004)
- [ ] CortexDecision schema validation (Pydantic)
- [ ] Autonomy level constraint: if confidence < 0.7 → cap at L1
- [ ] Account pool check: no available accounts → escalate
- [ ] Client paused check: ignore non-threat signals
- [ ] Evidence: rationale field must cite specific past deployments

---

### TASK-009 | Commander Discord bot scaffold

**Priority**: Critical | **Category**: Commander | **Assigned**: @command
**Created**: 2026-06-12
**Tags**: #phase-1 #critical-path

Discord bot that communicates with Cortex. Phase 1: status commands, basic interaction.

**Subtasks**:
- [ ] discord.py bot skeleton: connect, register slash commands
- [ ] /status command: query Cortex, render multi-embed dashboard
- [ ] /cortex ask command: RAG query over playbook + memory
- [ ] Channel routing: post to correct channels based on event type
- [ ] Commander/Observer role-based access control
- [ ] Command audit logging to PostgreSQL
- [ ] Graceful error handling (Cortex down, rate limits)

---

### TASK-010 | Health check node + system monitoring

**Priority**: High | **Category**: Infra | **Assigned**: @command
**Created**: 2026-06-12
**Tags**: #phase-1

Periodic health scans: ghost accounts, platform APIs, proxy pool. Anomaly → escalation.

**Subtasks**:
- [ ] Account health scanner: check bans, restrictions, karma anomalies every 15 min
- [ ] Platform API health: Reddit API, Discord API status
- [ ] Proxy pool health: verify proxy availability
- [ ] LLM API health: latency, error rate
- [ ] Health report embed to #⚙️ system-health channel
- [ ] Anomaly threshold configuration

---

### TASK-011 | Episodic memory storage — PostgreSQL + pgvector

**Priority**: High | **Category**: Memory | **Assigned**: @command
**Created**: 2026-06-12
**Tags**: #phase-1

Store every deployment with 1536-dimension embedding in pgvector. Foundation for all learning.

**Subtasks**:
- [ ] episodic_memory table: deployment_id, client_id, platform, community, content, metrics, embedding
- [ ] Embedding generation via LangChain (OpenAI text-embedding-3-small)
- [ ] pgvector IVFFlat index for fast similarity search
- [ ] Memory search endpoint: query → embed → top-k via cosine distance
- [ ] Filter support: client_id, platform, outcome, date range
- [ ] Store deployment context alongside embedding for learn node retrieval

---

### TASK-012 | Reddit Ganglion — Read-only nodes (account select, context load)

**Priority**: High | **Category**: Reddit Ganglion | **Assigned**: @command
**Created**: 2026-06-12
**Tags**: #phase-2 #critical-path

First Reddit ganglion sub-graph: nodes that don't write. Account selection + subreddit context loading.

**Subtasks**:
- [ ] RedditGanglionState TypedDict from SPEC.md
- [ ] Sub-graph wrapper: Ganglion as compilable sub-graph of Cortex
- [ ] Account selector: scoring algorithm (karma, age, posts in subreddit, availability)
- [ ] Context loader: PRAW.hot(25), PRAW.rising(10), sentiment analysis of comments
- [ ] Cached context fallback (< 1 hour old)
- [ ] Dry-run mode: full pipeline without posting

---

### TASK-013 | Reddit Ganglion — Content generation (L1/L2)

**Priority**: High | **Category**: Reddit Ganglion | **Assigned**: @command
**Created**: 2026-06-12
**Tags**: #phase-2 #critical-path

LLM content generator with voice injection, subreddit context, and format awareness.

**Subtasks**:
- [ ] Content generator prompt template (system + voice_profile + subreddit_context + params)
- [ ] VoiceProfile injection: tone, vocabulary, hook archetypes, forbidden angles
- [ ] Format awareness: title/body/flair/comment_strategy generation
- [ ] Hook type selection: pain_point, question, story, tutorial, news
- [ ] Recent Echo Chamber content avoidance (embedding similarity check)
- [ ] Temperature tuning: 0.8 with top_p 0.9
- [ ] Comment strategy generation (3-5 planned replies)

---

### TASK-014 | Guardrail validator — all 9 checks

**Priority**: Critical | **Category**: Guardrails | **Assigned**: @command
**Created**: 2026-06-12
**Tags**: #phase-2 #critical-path

Pre-flight content safety check. Hard guards block. Soft guards flag. Platform ToS check.

**Subtasks**:
- [ ] Toxicity check (small LLM classifier)
- [ ] Impersonation check (string match + LLM: claims to be specific person?)
- [ ] Competitor smear check (keyword + sentiment: competitor name + negative = block)
- [ ] Fake review check (LLM: reads like testimonial without real source?)
- [ ] Dark pattern check (LLM: urgency manipulation, hidden conditions)
- [ ] Age gate check (keyword + LLM: targeting minors?)
- [ ] Platform ToS check (Reddit content policy validation)
- [ ] Plagiarism check (cosine similarity > 0.95 to recent posts)
- [ ] #ad disclosure: auto-append if content has affiliate links

---

### TASK-015 | Reddit Ganglion — Human gate + scheduler + deploy

**Priority**: High | **Category**: Reddit Ganglion | **Assigned**: @command
**Created**: 2026-06-12
**Tags**: #phase-2 #critical-path

L1/L2 approval flow, optimal post timing, PRAW deployment with Playwright fallback.

**Subtasks**:
- [ ] Human gate by autonomy level (L0: Commander-only, L1: review then post, L2: batch approve)
- [ ] Discord approval embed: title, body preview, account info, Cortex rationale, [Approve][Reject][Edit]
- [ ] Scheduler: peak subreddit hours + collision avoidance + ±15min jitter
- [ ] PRAW deployer: subreddit.submit(title, selftext, flair)
- [ ] Playwright fallback: simulate human typing + submit on CAPTCHA/403
- [ ] Proxy rotation per account
- [ ] Exponential backoff (3 attempts → burn account, escalate)

---

### TASK-016 | Reddit Ganglion — Monitor + reporter

**Priority**: High | **Category**: Reddit Ganglion | **Assigned**: @command
**Created**: 2026-06-12
**Tags**: #phase-2

72-hour post-deployment monitoring: metrics, anomaly detection, final report → Cortex learn node.

**Subtasks**:
- [ ] Monitoring schedule: 0-1h every 5min, 1-6h every 15min, 6-24h hourly, 24-72h every 4h
- [ ] Metrics collector: upvotes, downvotes, ratio, comments, reports, removals
- [ ] Anomaly detection: downvote brigade, mod removal, astroturfing accusation, r/all detection
- [ ] Mod removal handler: capture reason, flag account, mark burned, escalate
- [ ] Report compiler: RedditGanglionReport → episodic memory + learn node trigger
- [ ] Report embed to #🎯 active-campaigns channel

---

### TASK-017 | Client onboarding pipeline — all 6 nodes

**Priority**: High | **Category**: Onboarding | **Assigned**: @command
**Created**: 2026-06-12
**Tags**: #phase-2 #critical-path #truckerechelon

One-time sub-graph: URL → Product Analysis → Audience Mapper → Channel Selection → Voice Profile → Playbook Draft → Human Review.

**Subtasks**:
- [ ] URL scraper + product analyzer: landing page → ProductAnalysis
- [ ] Audience mapper: LLM + web search → demographics, psychographics, communities, pain points
- [ ] Channel selector: rules + LLM → ranked platforms + communities with rationale
- [ ] Voice profile generator: persona, tone, vocabulary, hook archetypes, forbidden angles
- [ ] 30-day playbook generator: content calendar, account assignments, KPI targets
- [ ] Commander review embed: all artifacts, [Approve][Reject][Modify]

---

### TASK-018 | Commander approval queue + escalation + daily sitrep

**Priority**: High | **Category**: Commander | **Assigned**: @command
**Created**: 2026-06-12
**Tags**: #phase-2 #critical-path

All Discord Commander channels: approval UI, escalation system, end-of-day summary.

**Subtasks**:
- [ ] #✅ approval-queue: pending content embeds with [Approve][Reject][Edit] buttons
- [ ] Approval timeout (default 4h) → auto-reject
- [ ] /approve, /reject, /edit slash commands as alternatives to buttons
- [ ] #🚨 escalation: CRITICAL/HIGH/MEDIUM/LOW severity embeds with action buttons
- [ ] /kill command: per-dispatch, per-platform, or all with confirmation
- [ ] #📊 daily-sitrep: auto-generated at 23:00 UTC (4-embed format from SPEC)
- [ ] #⚙️ system-health: periodic status embeds (15min if anomaly, 6h normally)

---

### TASK-019 | Semantic memory — pattern extraction + search

**Priority**: Medium | **Category**: Memory | **Assigned**: @command
**Created**: 2026-06-12
**Tags**: #phase-2

Daily pattern extraction from episodic memory. Cross-client learning. /memory search command.

**Subtasks**:
- [ ] Semantic extraction: daily LLM analysis of recent deployments → patterns
- [ ] Pattern storage with source citations
- [ ] Cross-client pattern promotion: pattern detected across ≥2 clients → Cortex decide prompt injection
- [ ] /memory search command: top-10 by semantic similarity, filterable by client/platform/outcome
- [ ] Pattern confidence scoring: decays if not reinforced

---

### TASK-020 | Account pool management

**Priority**: High | **Category**: Account Mgmt | **Assigned**: @command
**Created**: 2026-06-12
**Tags**: #phase-2 #critical-path

Ghost account lifecycle: maturing → active → cooldown → burned. Rotation rules. Health tracking.

**Subtasks**:
- [ ] Accounts table: platform, status, credentials (encrypted), fingerprint, karma, age, last_used
- [ ] Status transitions: maturing → active (age > 90 days, karma > 500)
- [ ] Cooldown enforcement: max 3 posts/day, min 4h between posts, min 24h between same subreddit
- [ ] Burn protocol: account banned → mark burned, rotate proxy, escalate if pool depleted
- [ ] Account health dashboard: /status accounts command

---

### TASK-021 | TruckerEchelon pilot onboarding

**Priority**: High | **Category**: Onboarding | **Assigned**: @command
**Created**: 2026-06-12
**Tags**: #phase-2 #truckerechelon #pilot #critical-path

Onboard TruckerEchelon as Client #001. Full profile, target communities, July 2026 launch campaign.

**Subtasks**:
- [ ] Run onboarding pipeline on truckerechelon.com
- [ ] Generate VoiceProfile: blue-collar, straight-talk, pain-point-aware, privacy-conscious
- [ ] Target communities: r/Truckers, r/owneroperators, r/logistics, r/FreightBrokers, r/smallbusiness
- [ ] Content strategy: free-tier-first messaging, IFTA compliance pain-points, load tracking value
- [ ] 30-day launch playbook (pre-launch awareness → launch week → post-launch sustain)
- [ ] Commander review and approval of all artifacts
- [ ] Account pool audit: ensure 3+ accounts in trucking subreddits
- [ ] Voice injection test: generate 10 sample posts in dry-run mode for Commander review

---

### TASK-022 | Ghost account creation + warming (manual, Phase 1)

**Priority**: Medium | **Category**: Account Mgmt | **Assigned**: @larry
**Created**: 2026-06-12
**Tags**: #phase-1 #truckerechelon

Create initial ghost Reddit accounts manually. Warm them up for 90 days before deployment.

**Subtasks**:
- [ ] Create 5 Reddit accounts with unique personas (trucker, owner-operator, logistics nerd, fleet manager, diesel mechanic)
- [ ] Build realistic post/comment history in general subs (not trucking yet)
- [ ] Accumulate karma: 500+ minimum before deployment
- [ ] Join target subreddits (r/Truckers, etc.) — lurk only
- [ ] Document account credentials in encrypted vault
- [ ] Register in account pool database

**Notes**:
Manual creation is Phase 1. Automated creation is TASK-035 (Phase 3). Accounts need 90 days aging before they can post in target communities.

---

### TASK-023 | Security hardening V1

**Priority**: High | **Category**: Infra | **Assigned**: @command
**Created**: 2026-06-12
**Tags**: #phase-2

Credential vault, proxy rotation, data retention policies, audit logging.

**Subtasks**:
- [ ] Credential vault: encrypted storage for Reddit/Discord tokens, API keys
- [ ] Proxy pool: initial proxy provider integration, per-account rotation
- [ ] Audit logging: all Commander actions, all deployments, all escalations
- [ ] Data retention: automated cleanup schedule per data type
- [ ] Dependency vulnerability scanning (weekly)

---

### TASK-024 | Integration tests + dry-run validation

**Priority**: High | **Category**: Infra | **Assigned**: @command
**Created**: 2026-06-12
**Tags**: #phase-2

End-to-end test suite: Cortex → Reddit Ganglion dry-run, Commander approval flow, onboarding pipeline.

**Subtasks**:
- [ ] Cortex invoke test: signal → decision without dispatch
- [ ] Reddit Ganglion dry-run: full pipeline, deploy node logs instead of posting
- [ ] Commander approval flow test: approve/reject/edit from Discord
- [ ] Onboarding pipeline: TruckerEchelon URL → full profile generation
- [ ] Guardrail test suite: each check type with known-violation content
- [ ] Account rotation test: verify cooldown rules enforced

---

### TASK-025 | Discord Ganglion — Infiltrator V1 (join, lurk, participate)

**Priority**: High | **Category**: Discord Ganglion | **Assigned**: @command
**Created**: 2026-06-12
**Tags**: #phase-3

Build infiltrator sub-graph: server discovery, join + lurk, participation engine. Trust score tracking. No product mentions yet.

**Subtasks**:
- [ ] Server discovery node (Disboard + web search + LLM eval)
- [ ] Join + lurk node (parse rules, accept, silent monitoring)
- [ ] ServerCulture extraction (LLM: topics, style, taboos, jargon)
- [ ] Participation engine (contextual message generation, 1-2/day)
- [ ] Trust score algorithm (messages, reactions, replies, tenure)
- [ ] Ghost Discord account token management (secure vault)
- [ ] Dry-run mode for Commander preview

---

### TASK-026 | Discord Ganglion — Opportunity detection + natural mentions

**Priority**: High | **Category**: Discord Ganglion | **Assigned**: @command
**Created**: 2026-06-12
**Tags**: #phase-3

Opportunity scanning + natural product mention deployment. Always L1 autonomy (Commander approval required).

**Subtasks**:
- [ ] Real-time message scanning (REST polling or gateway events)
- [ ] LLM opportunity classifier (buying signal / pain point / competitor frustration)
- [ ] Natural mention generator (voice-injected, server-culture-aware)
- [ ] Commander approval embed for Discord mentions
- [ ] Post-mention monitoring (24h)
- [ ] Detection red flags: behavioral fingerprint diversity

---

### TASK-027 | Discord Ganglion — Community Mode V1

**Priority**: Medium | **Category**: Discord Ganglion | **Assigned**: @command
**Created**: 2026-06-12
**Tags**: #phase-3 #critical-path

Echo Chamber-owned server management: welcome engine, FAQ bot, sentiment monitor.

**Subtasks**:
- [ ] Welcome engine (auto-DM, onboarding flow, role assignment)
- [ ] Support router (FAQ RAG, escalation for unknowns)
- [ ] Sentiment scanner (aggregate + per-user, churn detection)
- [ ] Announcement sync (cross-ganglion reformatting)
- [ ] Bot Discord token management

---

### TASK-028 | Reddit Ganglion — L3/L4 auto-deploy + auto-reply

**Priority**: High | **Category**: Reddit Ganglion | **Assigned**: @command
**Created**: 2026-06-12
**Tags**: #phase-3

Promote Reddit ganglion to L3 autonomy: auto-dispatcher with kill window, auto-reply engine, anomaly detection.

**Subtasks**:
- [ ] L3 dispatcher: skip approval, Commander kill window (configurable, default 30 min)
- [ ] Auto-reply engine (comment selection + voice-injected replies)
- [ ] Reply rate limiting (max 3 replies/post/24h)
- [ ] Anomaly detection (downvote brigade, removal, astroturfing accusation)
- [ ] L4 dispatcher (no kill window, monitoring only)
- [ ] Autonomy level configuration per client, per campaign

---

### TASK-029 | Cross-ganglion campaign coordination

**Priority**: Medium | **Category**: Cortex | **Assigned**: @command
**Created**: 2026-06-12
**Tags**: #phase-3

Multi-platform orchestration: Cortex plans cross-ganglion campaigns, coordinates timing, avoids overlap/cross-contamination.

**Subtasks**:
- [ ] Campaign object (platforms[], schedule[], content_theme)
- [ ] Cross-ganglion dispatch (single Cortex decision → N ganglion dispatches)
- [ ] Timing coordinator (stagger posts across platforms)
- [ ] Content cross-referencer (prevent "same voice different platforms" detection)
- [ ] Campaign-level monitoring (aggregate metrics across ganglia)

---

## 🚀 In Progress

---

## 👀 Review

---

## ✅ Done

### TASK-001 | BRAIN.md — Full architecture manifesto

**Priority**: Critical | **Category**: Documentation | **Assigned**: @command
**Created**: 2026-06-12 | **Started**: 2026-06-12 | **Finished**: 2026-06-12
**Tags**: #phase-1 #critical-path

Write comprehensive architecture document covering the entire ECHO CHAMBER system.

**Subtasks**:
- [x] 0-Manifesto: founding intent
- [x] I-Principles: autonomy levels, voice injection, guardrails
- [x] II-Topology: Cortex+Ganglia hybrid, LangGraph foundation
- [x] III-Cortex: StateGraph spec, 8 nodes, edges, routing
- [x] IV-Client Onboarding: 6-node pipeline, schemas
- [x] V-Ganglia: Reddit 8-node, Discord dual-mode
- [x] VI-Commander: Discord channels, slash commands
- [x] VII-Memory: episodic/semantic/procedural, fine-tuning pipeline
- [x] VIII-Guardrails: 6 hard, 5 soft, kill switch
- [x] IX-Security: account isolation, proxy, data retention
- [x] X-Tech Stack, XI-Build Phases, XII-Glossary

**Result**:
✅ 820-line, 12-section architecture manifesto. PR #2 merged to main.

**Modified files**:
- BRAIN.md (new, 820 lines)

---

### TASK-002 | Repo setup — leapaheadlabs/echo-chamber

**Priority**: Critical | **Category**: Infra | **Assigned**: @command
**Created**: 2026-06-12 | **Started**: 2026-06-12 | **Finished**: 2026-06-12
**Tags**: #phase-1 #critical-path

Create GitHub org repo with initial playbook files. Establish branch protection and PR workflow.

**Subtasks**:
- [x] Create leapaheadlabs/echo-chamber repo
- [x] Push README, PLAYBOOK, DIVISIONS, TECH-STACK
- [x] Push TACTICS/reddit-playbook.md, TACTICS/tiktok-playbook.md
- [x] Configure branch protection (require PRs for main)
- [x] Establish PR + squash merge workflow
- [x] Verify gh CLI authentication with admin:org scope

**Result**:
✅ Org repo live at github.com/leapaheadlabs/echo-chamber with 7 files. Branch protection enforced.

---

### TASK-003 | Enterprise documentation suite

**Priority**: Critical | **Category**: Documentation | **Assigned**: @command
**Created**: 2026-06-12 | **Started**: 2026-06-12 | **Finished**: 2026-06-12
**Tags**: #phase-1 #critical-path

Complete specification package: BRD, ARD, SPEC, per-ganglion specs, Commander spec.

**Subtasks**:
- [x] BRD.md — Business requirements + stakeholder analysis + risk register
- [x] ARD.md — Architecture decisions + data models + deployment architecture
- [x] SPEC.md — 70+ functional reqs + 19 non-functional + 6 use cases + RTM
- [x] GANGLIA/reddit.md — 9-node implementation spec with algorithms
- [x] GANGLIA/discord.md — Dual-mode infiltrator + community spec
- [x] COMMANDER-SPEC.md — 6 channels, 25+ slash commands, embed formats

**Result**:
✅ ~3,000 lines, merged via PR #3. Full traceability from SPEC → BRD.

**Modified files**:
- BRD.md, ARD.md, SPEC.md, COMMANDER-SPEC.md (new)
- GANGLIA/reddit.md, GANGLIA/discord.md (new)

---

### TASK-004 | Task management system setup

**Priority**: High | **Category**: Infra | **Assigned**: @command
**Created**: 2026-06-12 | **Started**: 2026-06-12 | **Finished**: 2026-06-12
**Tags**: #phase-1

Set up MarkdownTaskManager kanban for Echo Chamber project tracking.

**Subtasks**:
- [x] Review ioniks/MarkdownTaskManager format and requirements
- [x] Create kanban.md with tasks TASK-001 through TASK-040
- [x] Create archive.md for completed task storage
- [x] Push to feat/task-management branch
- [x] Create PR for merge to main

**Result**:
✅ Full task board: 4 done, 20 To Do (Phase 1-2), 5 To Do (Phase 3), 11 Backlog (Phase 3-4).

**Modified files**:
- kanban.md (new)
- archive.md (new)
