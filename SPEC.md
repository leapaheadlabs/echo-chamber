# 📐 SPEC — SYSTEM SPECIFICATION

> **ECHO CHAMBER v1.0**  
> **Document ID:** EC-SPEC-001  
> **Version:** 1.0  
> **Date:** 2026-06-12  
> **Classification:** INTERNAL — COMMANDER EYES ONLY  
> **Depends on:** BRD.md, ARD.md, BRAIN.md

---

## 1. SCOPE

This document defines the complete functional and non-functional requirements for the ECHO CHAMBER system. It is the implementation authority. Every feature must trace to a requirement in this document.

### 1.1 In Scope
- Cortex signal processing and decision engine
- Reddit Ganglion (content generation, deployment, monitoring)
- Discord Ganglion (infiltrator mode, community mode)
- Commander Discord interface
- Client onboarding pipeline
- Memory architecture (episodic, semantic, procedural)
- Account management (ghost pool)
- Guardrails and kill switch
- Fine-tuning data pipeline (collection only)

### 1.2 Out of Scope (Phase 4+)
- TikTok, X/Twitter, YouTube, Newsletter ganglia
- LoRA fine-tuning execution
- Web-based Commander dashboard
- Client self-service portal
- Payment/billing integration
- Multi-Commander role-based access

---

## 2. FUNCTIONAL REQUIREMENTS

### 2.1 Cortex — Signal Processing

#### FR-CX-001: Signal Ingestion
- **Priority:** P0
- **Description:** The system shall accept signals from multiple sources (Reddit webhook, Discord events, RSS feeds, manual Commander input) via a message queue.
- **Input:** `{ source: string, type: string, payload: object, timestamp: ISO8601 }`
- **Output:** Normalized `Signal` object in Cortex state.
- **Edge Cases:** Invalid payload → dead letter queue. Duplicate signal (same source + timestamp) → deduplication.

#### FR-CX-002: Signal Classification
- **Priority:** P0
- **Description:** The system shall classify each signal as one of: `trend`, `mention`, `opportunity`, `threat`, `noise`.
- **LLM:** Small model (Haiku / GPT-4o-mini), cost-optimized.
- **Input:** Normalized signal + current platform context.
- **Output:** `{ classification: SignalType, confidence: float, reasoning: string }`
- **Edge Cases:** Low confidence (< 0.6) → route to `escalate` for Commander review. `noise` → discard.

#### FR-CX-003: Signal Routing
- **Priority:** P0
- **Description:** The Cortex shall route signals via conditional edges:
  - `trend` → cortex_decide
  - `mention` → cortex_decide
  - `opportunity` → cortex_decide
  - `threat` → escalate (bypasses decide, straight to Commander)
  - `noise` → END
- **No LLM required.** Pure conditional edge logic.

#### FR-CX-004: Cortex Decision Engine
- **Priority:** P0
- **Description:** Given a classified signal and full operational context, the Cortex shall produce a `CortexDecision`.
- **LLM:** Large model (Claude Sonnet / GPT-4).
- **Input context:**
  - Classified signal
  - Client profile (voice, constraints, channels)
  - Campaign memory (pgvector similarity: top-5 relevant past deployments)
  - Account pool status (available accounts per platform)
  - Platform health (recent bans, rate limits)
- **Output:** `CortexDecision` { decision_id, action, rationale, ganglions[], content_params, autonomy_level, priority, suggested_timing }
- **Decision rules:**
  - If signal is `threat` → NEVER auto-decide. Always escalate.
  - If signal confidence < 0.7 → autonomy_level capped at L1.
  - If account pool has no available accounts for target platform → escalate, do not dispatch.
  - If client is in `paused` status → ignore non-threat signals.
- **Evidence:** rationale field must be human-readable and cite specific sources (e.g., "Similar r/Truckers IFTA post (deployment #47) achieved 340 upvotes with pain-point hook").

#### FR-CX-005: Escalation
- **Priority:** P0
- **Description:** When escalation is triggered, the system shall:
  1. Create `Escalation` record in Cortex state.
  2. Post formatted embed to `#🚨 escalation` Discord channel.
  3. Include: severity, signal context, recommended action, decision buttons.
- **Timeout:** If Commander does not respond within configurable window (default: 4 hours), escalation is re-posted with urgency bump.

#### FR-CX-006: Learning Loop
- **Priority:** P1
- **Description:** After any deployment completes monitoring, the Cortex shall:
  1. Extract deployment outcomes (metrics, sentiment).
  2. Generate lessons via LLM: "What worked? What didn't? Why?"
  3. Store episodic memory with embedding.
  4. Aggregate patterns into semantic memory.
  5. Update procedural state (account health, platform metrics).

#### FR-CX-007: Health Check
- **Priority:** P1
- **Description:** Periodic (every 15 minutes) health check that:
  1. Scans all ghost accounts for bans, restrictions, karma anomalies.
  2. Checks platform API health.
  3. Validates proxy pool availability.
  4. Posts anomalies to `#⚙️ system-health` Discord channel.

---

### 2.2 Client Onboarding

#### FR-ON-001: Ingest Client URL
- **Priority:** P0
- **Description:** Commander submits client URL via `/onboard <url>`. System scrapes and analyzes the landing page.
- **Input:** `{ url: string }`
- **Output:** `ProductAnalysis` { features, pricing, positioning, claims, target_market_indicators }

#### FR-ON-002: Audience Mapping
- **Priority:** P0
- **Description:** Based on product analysis, the system shall identify target audiences: demographics, psychographics, online communities, pain points, buying triggers.
- **LLM:** Large model with web search tool access.
- **Output:** `List[Audience]` with confidence scores.

#### FR-ON-003: Channel Selection
- **Priority:** P0
- **Description:** The system shall select target platforms and communities based on audience analysis, platform fit, and Echo Chamber's current capabilities.
- **Rules-based + LLM-assisted.**
- **Output:** `Dict[Platform, List[Community]]` with priority ordering and rationale.

#### FR-ON-004: Voice Profile Generation
- **Priority:** P0
- **Description:** Generate `VoiceProfile` — persona, tone, vocabulary, hook archetypes, forbidden angles, brand safety rules.
- **LLM:** Large model.
- **Input:** Product analysis + audience map + community contexts.
- **Output:** `VoiceProfile` object.

#### FR-ON-005: Playbook Generation
- **Priority:** P0
- **Description:** Generate first 30-day campaign playbook: content calendar, account assignments, KPI targets, budget allocation.
- **Output:** Structured playbook document + Commander preview embed.

#### FR-ON-006: Human Review Gate
- **Priority:** P0
- **Description:** All onboarding artifacts (profile, voice, channels, playbook) must be approved by Commander before client is set to `active`.
- **Commander can:** approve, reject with feedback, or modify any field.
- **Post-approval:** Client profile persisted to PostgreSQL. Status set to `active`. Client channel created in Commander Discord.

---

### 2.3 Reddit Ganglion

#### FR-RD-001: Account Selection
- **Priority:** P0
- **Description:** For each dispatch, select the optimal ghost account based on:
  - Target subreddit membership and karma
  - Account status (`active`)
  - Cooldown window (minimum time between posts)
  - Fingerprint match (does this account "fit" the target subreddit?)
  - Recent activity (avoid posting-pattern detection)
- **Tiebreaker:** Account with lowest recent post count.

#### FR-RD-002: Context Loading
- **Priority:** P0
- **Description:** Load current state of target subreddit:
  - Top 25 posts (hot)
  - Top 10 posts (rising)
  - Recent mod actions (sticky posts, rule changes)
  - Current sentiment (via comment sentiment analysis)
  - Recent Echo Chamber deployments in this subreddit
- **Sources:** PRAW API (primary), web scraping (fallback).

#### FR-RD-003: Content Generation
- **Priority:** P0
- **Description:** Generate platform-native Reddit content:
  - Post title (character limit: 300)
  - Post body (optional, markdown)
  - Comment strategy (3-5 planned replies for own post)
  - Flair selection (if subreddit requires)
- **LLM:** Medium/large model.
- **Injected context:**
  - Client VoiceProfile
  - Subreddit context (trending topics, top-performing formats)
  - Content parameters from Cortex dispatch
  - Recent Echo Chamber content (avoid repetition)
- **Format awareness:** The LLM must understand what works on Reddit — AMA style, story format, question hooks, pain-point rants, tutorial/value posts.

#### FR-RD-004: Guardrail Validation
- **Priority:** P0
- **Description:** Pre-deployment validation:
  1. **Hard guards:** Fake review detection, impersonation check, competitor false claims, dark patterns, minor targeting, #ad disclosure check.
  2. **Soft guards:** Post frequency for account, account age minimum, language intensity, competitor name mention.
  3. **Platform ToS:** Reddit-specific content policy check (no vote manipulation language, no personal information, no harassment).
  4. **Plagiarism check:** Cosine similarity against recent posts in target subreddit (avoid rephrased copies).
- **Failure:** Block deployment. Log violation. If hard guard → escalate to Commander.

#### FR-RD-005: Human Gate (L1/L2)
- **Priority:** P0
- **Description:** For autonomy levels L1 and L2:
  - Post content preview to `#✅ approval-queue` Discord channel.
  - Include: title, body, subreddit, selected account, autonomy level, context (why this post?).
  - Commander actions: Approve, Reject, Edit.
  - Timeout: If no Commander action within configurable window (default: 4 hours), content auto-rejected (not auto-approved).
- **Rejection:** Feedback sent to Cortex for learning.

#### FR-RD-006: Scheduling
- **Priority:** P0
- **Description:** Determine optimal posting time:
  - Subreddit-specific peak activity hours (from Reddit metrics API).
  - Stagger from other Echo Chamber content in same subreddit.
  - Respect account cooldown windows.
  - Add jitter (±15 minutes) to avoid pattern detection.
- **Output:** ISO 8601 scheduled deployment time.

#### FR-RD-007: Deployment
- **Priority:** P0
- **Description:** Execute the post:
  - **Primary:** Reddit API (PRAW) — `subreddit.submit(title, selftext=body)`
  - **Fallback:** Playwright browser automation (simulate human typing + submit) — used when API returns CAPTCHA or account requires browser fingerprint.
  - Proxy rotation per account.
  - **Result:** Reddit post URL captured.
  - **Error handling:** API failure → retry with exponential backoff. 3 failures → mark account for investigation, escalate.

#### FR-RD-008: Post-Deployment Monitoring
- **Priority:** P0
- **Description:** Monitor deployed content for configurable window (default: 72 hours):
  - Track: upvotes, downvotes, comment count, reports, removals.
  - L3/L4: Auto-reply to top-level comments using voice profile injection.
  - L1/L2: Queue replies for Commander approval.
  - Anomaly detection: vote manipulation accusation, sudden downvote brigade, mod removal.
  - If post removed: log reason (if available from Reddit), flag account, do not use account for cooldown period.

#### FR-RD-009: Report Generation
- **Priority:** P0
- **Description:** At end of monitoring window, generate structured report:
  - Final metrics (upvotes, comments, engagement rate).
  - Sentiment score from comments.
  - Conversion indicators (link clicks if trackable, "where can I find this?" comments).
  - Account health update.
  - Trigger Cortex learn node.

---

### 2.4 Discord Ganglion

#### FR-DC-001: Server Discovery (Infiltrator Mode)
- **Priority:** P1
- **Description:** Identify Discord servers matching client's target audience:
  - Search via Discord server discovery, Disboard, third-party server lists.
  - LLM evaluates server fit: member count, activity level, topic relevance, moderation style.
  - Output: Ranked list of target servers with join strategy.

#### FR-DC-002: Join + Lurk (Infiltrator Mode)
- **Priority:** P1
- **Description:** Ghost Discord account joins target server:
  - Accept server rules (parse rules channel, acknowledge).
  - Initial lurking period (configurable, default: 7 days) — read only, no posting.
  - During lurk: log server culture, active members, conversation patterns, taboo topics.

#### FR-DC-003: Participation Engine (Infiltrator Mode)
- **Priority:** P1
- **Description:** After lurk period, begin natural participation:
  - Generate contextually relevant messages in server's voice.
  - Avoid product mention entirely during initial participation phase (configurable: 14 days).
  - Build "trust score" — track reactions received, replies, @mentions.
  - Post frequency: 3-5 messages/day, spread across active hours.

#### FR-DC-004: Opportunity Detection (Infiltrator Mode)
- **Priority:** P1
- **Description:** Scan server conversations for natural product insertion opportunities:
  - Buying signals: "anyone know a good app for...", "I wish there was a tool that...", "What do you guys use for..."
  - Pain points: Users complaining about problems the client product solves.
  - Competitor mentions: Users discussing frustrations with competitor products.
- **Output:** Opportunity alert to Cortex for decide routing.

#### FR-DC-005: Natural Mention Deploy (Infiltrator Mode)
- **Priority:** P1
- **Description:** Deploy natural product mention:
  - NOT a pitch. A genuine-seeming recommendation from a community member.
  - Voice: "oh yeah I've been using [product] for [timeframe], the [feature] is actually pretty solid for [pain_point]"
  - Always at L1/L2 autonomy (Commander approval required for direct product mentions in infiltrated servers).
  - Maximum 1 product mention per account per 7 days in infiltrated servers.

#### FR-DC-006: Trust Score Tracking (Infiltrator Mode)
- **Priority:** P1
- **Description:** Track account trust in each server:
  - Factors: days since join, message count, reactions received, reply rate, moderation actions (warnings, mutes).
  - Low trust score → reduce frequency, more generic content.
  - High trust score → unlocked for product mentions.
  - Account flagged/banned → burn account, do not reuse in that server ecosystem.

#### FR-DC-007: Welcome Engine (Community Mode)
- **Priority:** P2
- **Description:** For Echo Chamber-owned Discord servers:
  - Auto-DM new members with server guide and product context.
  - Role assignment based on user input (onboarding flow).
  - Track member journey: joined → introduced → engaged → power user.

#### FR-DC-008: Support Router (Community Mode)
- **Priority:** P2
- **Description:** Auto-answer product questions:
  - FAQ matching via embedding similarity.
  - Escalate complex/angry questions to Commander.
  - Never fabricate answers — if unknown, say so and escalate.

#### FR-DC-009: Sentiment Monitoring (Community Mode)
- **Priority:** P2
- **Description:** Monitor own-server sentiment:
  - Detect unhappy users, complaints, churn signals.
  - Flag for Commander intervention.
  - Track sentiment trend over time.

---

### 2.5 Commander Interface

#### FR-CM-001: Discord Bot
- **Priority:** P0
- **Description:** A Discord bot (`ECHO CHAMBER COMMAND`) that:
  - Provides slash commands for all Commander operations.
  - Posts structured embeds to appropriate channels.
  - Supports button interactions (Approve/Reject/Edit/Kill).
  - Requires Commander role for destructive commands.

#### FR-CM-002: Status Command
- **Priority:** P0
- **Description:** `/status` returns full system dashboard embed:
  - Active clients with status
  - Ganglion health per platform
  - Account pool summary (active/cooldown/burned counts)
  - Recent deployments (last 24h)
  - Pending approval queue count
  - Platform health indicators

#### FR-CM-003: Approval Queue
- **Priority:** P0
- **Description:** `#✅ approval-queue` channel displays:
  - Each pending item as a Discord embed with:
    - Content preview (truncated at 300 chars + expand button)
    - Target platform + community
    - Selected account info
    - Autonomy level
    - Cortex rationale
    - [Approve] [Reject] [Edit] buttons
  - Items ordered by priority then age.
  - Expired items (no action within timeout) auto-rejected with notification.

#### FR-CM-004: Daily Sitrep
- **Priority:** P1
- **Description:** Auto-generated at configurable time (default: 23:00 UTC):
  - Deployments executed in last 24h.
  - Performance highlights (top 3 by engagement).
  - Account health changes.
  - Platform incidents.
  - Upcoming scheduled content.
  - Posted to `#📊 daily-sitrep`.

#### FR-CM-005: Escalation Channel
- **Priority:** P0
- **Description:** `#🚨 escalation` channel for:
  - Threats detected
  - Account bans
  - Guardrail violations
  - Platform policy changes
  - System errors
  - Each item with severity indicator (🟢🟡🟠🔴) and action buttons.

#### FR-CM-006: Kill Switch
- **Priority:** P0
- **Description:** `/kill` command behavior:
  - `/kill all` → All ganglia freeze, all scheduled posts cancelled, all ghost accounts dormant.
  - `/kill reddit` → Reddit ganglion freeze only.
  - `/kill discord` → Discord ganglion freeze only.
  - `/kill <dispatch_id>` → Remove specific deployment + burn account if needed.
  - Confirmation required for `/kill all`.
  - Auto-trigger on: 3+ bans in 24h, legal escalation, platform TOS change.

---

### 2.6 Memory & Learning

#### FR-MM-001: Episodic Storage
- **Priority:** P0
- **Description:** After every deployment, store full record with 1536-dimension embedding in pgvector.
- **Searchable by:** Client, platform, community, content type, outcome metrics, date range, semantic similarity.

#### FR-MM-002: Semantic Extraction
- **Priority:** P1
- **Description:** Periodically (daily) extract patterns from episodic memory:
  - "Pain-point hooks outperformed feature-list hooks 3:1 in trucking communities"
  - "Posts over 500 words in r/owneroperators had 2x engagement"
  - "Tutorial/value posts had lowest ban rate across all communities"
- **Stored as:** Semantic memory entries with source citations.

#### FR-MM-003: Cross-Client Learning
- **Priority:** P2
- **Description:** When semantic memory detects a pattern that generalizes across clients, it becomes a first-class rule injected into the Cortex decide prompt.

#### FR-MM-004: Memory Search
- **Priority:** P1
- **Description:** `/memory search <query>` returns top-10 episodic memories by semantic similarity.
  - Optional filter: `client:<id>`, `platform:<name>`, `outcome:<success|failure>`
  - Results include: summary, metrics, date, link to full record.

---

### 2.7 Account Management

#### FR-AC-001: Account Pool
- **Priority:** P0
- **Description:** System maintains a pool of ghost accounts per platform with status tracking:
  - `maturing` — Account exists, aging up, not yet deployable.
  - `active` — Available for deployment.
  - `cooldown` — Recently used, waiting for cooldown window.
  - `burned` — Permanently retired.
  - `flagged` — Under investigation (unusual activity detected).

#### FR-AC-002: Account Rotation
- **Priority:** P0
- **Description:** No account shall be used for:
  - More than 3 posts per day.
  - More than 1 post per 4 hours.
  - The same subreddit/server twice within 24 hours (for ghost accounts).
  - Deployment until minimum age (default: 90 days).

#### FR-AC-003: Account Creation (Future Phase)
- **Priority:** P2
- **Description:** Automated account creation:
  - Randomized persona generation (name, bio, interests).
  - Browser automation for signup flow.
  - Email verification handling.
  - Initial warming period: automated organic browsing + upvoting for configurable days.
  - **Note:** Phase 1 uses manually created accounts. Automated creation is Phase 3.

---

### 2.8 Guardrails

#### FR-GR-001: Content Validator (Pre-Flight)
- **Priority:** P0
- **Description:** Before any content is deployed, validate against all guardrails:
  - Fake review/recommendation detection: LLM classifier + keyword patterns.
  - Impersonation check: Generated persona cross-referenced against known real individuals.
  - Competitor false claims: Competitor name mention + negative sentiment = block.
  - Dark pattern detection: Urgency manipulation, hidden conditions, misleading claims.
  - Age targeting: Content analysis for minor-targeting language.

#### FR-GR-002: #ad Disclosure
- **Priority:** P0
- **Description:** Any content containing affiliate links or paid promotion must include clear disclosure:
  - Reddit: "*(disclosure: I use this product and may receive compensation)*"
  - Discord: Similar natural-language disclosure.
  - Cannot be stripped, hidden, or minimized.
  - Auto-appended by system, not LLM-generated.

#### FR-GR-003: Platform Policy Monitor
- **Priority:** P1
- **Description:** Monitor for changes to platform Terms of Service:
  - Check weekly (or on-demand via `/check policies`).
  - LLM compares current TOS to cached version.
  - If changes detected that could impact Echo Chamber tactics → escalate to Commander.
  - Auto-suspend affected ganglion if change is clearly prohibitive.

---

## 3. NON-FUNCTIONAL REQUIREMENTS

### 3.1 Performance

| ID | Requirement | Target | Measurement |
|----|-------------|--------|-------------|
| NF-PERF-01 | Signal-to-classification latency | < 5 seconds p95 | Prometheus histogram |
| NF-PERF-02 | Cortex decide latency | < 30 seconds p95 | Prometheus histogram |
| NF-PERF-03 | Content generation latency | < 15 seconds p95 | Prometheus histogram |
| NF-PERF-04 | Commander dashboard load | < 2 seconds for /status | Discord interaction response time |
| NF-PERF-05 | Approval queue item load | < 1 second for embed render | Measured at Discord API |
| NF-PERF-06 | Memory search latency | < 3 seconds for /memory search | Measured at API endpoint |

### 3.2 Reliability

| ID | Requirement | Target |
|----|-------------|--------|
| NF-REL-01 | Cortex service uptime | 99.5% (monthly) |
| NF-REL-02 | Deployment success rate | > 95% (API success on first attempt) |
| NF-REL-03 | LLM API availability | > 99.9% (with provider failover) |
| NF-REL-04 | Data durability | 99.999999999% (11 9's via RDS) |
| NF-REL-05 | Graceful degradation | Ganglia degrade independently; Cortex + Commander remain operational |

### 3.3 Security

| ID | Requirement | Target |
|----|-------------|--------|
| NF-SEC-01 | Credentials in LLM context | Never |
| NF-SEC-02 | Database encryption | AES-256 at rest, TLS 1.3 in transit |
| NF-SEC-03 | API authentication | OAuth2 / API key with rotation |
| NF-SEC-04 | Commander authentication | Discord OAuth2 + 2FA |
| NF-SEC-05 | Audit trail completeness | All commander actions, all deployments, all escalations |
| NF-SEC-06 | Dependency vulnerability scanning | Weekly automated scan |

### 3.4 Maintainability

| ID | Requirement | Target |
|----|-------------|--------|
| NF-MAIN-01 | New ganglion implementation time | < 1 week for experienced developer |
| NF-MAIN-02 | Code coverage (critical paths) | > 80% (Cortex, guardrails, deployment) |
| NF-MAIN-03 | Documentation completeness | All public interfaces documented |
| NF-MAIN-04 | Configuration as code | All infra defined in Terraform/OpenTofu |

### 3.5 Cost

| ID | Requirement | Target |
|----|-------------|--------|
| NF-COST-01 | Cost per deployment (LLM) | < $0.10 average |
| NF-COST-02 | Cost per deployment (total) | < $0.25 including proxy + infra |
| NF-COST-03 | Monthly infrastructure baseline | < $500/month (excluding LLM + proxy) |
| NF-COST-04 | Per-client marginal cost | < $200/month (excluding LLM usage per client) |

---

## 4. USE CASE CATALOG

### UC-01: Commander Onboards New Client
1. Commander types `/onboard https://example.com`
2. Cortex scrapes landing page, analyzes product.
3. Cortex maps audiences, selects channels, generates voice profile.
4. Cortex generates first 30-day playbook.
5. All artifacts posted to `#client-{name}` channel for Commander review.
6. Commander reviews, edits voice profile, approves.
7. Client set to `active`. Campaign begins.

### UC-02: Trend Triggers Automatic Content
1. Reddit monitoring detects rising IFTA complaint trend in r/Truckers.
2. Signal ingested, classified as `trend`, routed to cortex_decide.
3. Cortex retrieves TruckerEchelon profile, campaign memory, account pool.
4. Cortex decides: deploy pain-point post to r/Truckers, L3 autonomy.
5. Reddit ganglion: selects account, loads context, generates content, validates, deploys.
6. Commander receives notification: "Auto-deployed. /kill within 30 min to cancel."
7. Post achieves 200+ upvotes. Ganglion monitors, auto-replies to comments.
8. After 72h, final metrics stored. Learn node extracts: "IFTA complaint timing correlates with month-end."

### UC-03: Commander Approves Queued Content
1. `#✅ approval-queue` shows new embed: Ghost post for r/owneroperators.
2. Commander reads rationale: "Similar post #52 had 180 upvotes. Trucker pain-point angle."
3. Commander clicks [Edit], modifies title for better hook.
4. Commander clicks [Approve].
5. Content scheduled and deployed.

### UC-04: Account Ban Triggers Escalation
1. Ghost account #3 banned from r/Truckers.
2. Health check detects ban. Account status → `burned`.
3. Escalation posted to `#🚨 escalation`: "Ghost #3 banned. 1 of 5 Reddit accounts offline."
4. Commander clicks [Confirm Burn]. Account permanently retired.
5. Cortex checks account pool: 4 accounts remain for Reddit. Autonomy levels adjusted.
6. If < 3 accounts remain → auto-pause Reddit ganglion, escalate to Commander.

### UC-05: Emergency Kill Switch
1. Commander detects platform backlash or legal concern.
2. Commander types `/kill all`.
3. Bot requests confirmation: "This will freeze all operations. Confirm?"
4. Commander confirms.
5. All ganglia: `interrupt()` called. All scheduled posts cancelled. All ghost accounts set to dormant.
6. Confirmation posted to all Commander channels.
7. Commander must `/resume` to restart.

### UC-06: Cross-Platform Coordinated Campaign
1. Cortex identifies product launch window for TruckerEchelon (July 2026).
2. Generates campaign: "Launch Week" — Reddit (3 subreddits) + Discord (own server) + Discord (3 infiltrated servers).
3. Content synchronized: Discord server announcement → Reddit posts same day with server link.
4. Ganglia coordinate timing, avoid overlap, cross-reference content.
5. Commander monitors across channels via `/status`.

---

## 5. REQUIREMENTS TRACEABILITY MATRIX

| BRD ID | SPEC ID(s) | Description |
|--------|-----------|-------------|
| BR-01 | FR-ON-001 through FR-ON-006 | Client onboarding pipeline |
| BR-02 | FR-CX-001 (multi-client state) | Multi-client support |
| BR-03 | FR-CX-001 (client_id scoping) | Client data isolation |
| BR-04 | FR-CM-001 (/pause, /resume) | Client pause/resume |
| BR-05 | FR-CM-004, FR-MM-004 | Client reporting |
| BR-06 | FR-RD-003, FR-DC-003, FR-DC-005 | Platform-native content |
| BR-07 | FR-RD-003 (voice injection) | Voice profile injection |
| BR-08 | FR-CX-004 (autonomy_level) | L0-L4 autonomy |
| BR-09 | FR-RD-005, FR-CM-003 | L1/L2 approval queue |
| BR-10 | FR-RD-007 (L3 auto-deploy) | L3 auto with kill window |
| BR-11 | FR-RD-007 (L4 auto-deploy) | L4 full auto |
| BR-12 | FR-CX-001, FR-CX-002 | Signal monitoring |
| BR-13 | FR-CX-002, FR-CX-003 | Signal classify + route |
| BR-14 | FR-CX-006, FR-MM-001, FR-MM-002 | Deployment learning |
| BR-15 | FR-MM-003 | Cross-client learning |
| BR-16 | FR-CX-006 (training record) | Fine-tuning data collection |
| BR-17 | FR-GR-001 (hard guards) | Hard guardrail enforcement |
| BR-18 | FR-GR-001 (soft guards) | Soft guardrail configuration |
| BR-19 | FR-CM-006 | Emergency kill switch |
| BR-20 | FR-GR-001 (age targeting) | Minor targeting prevention |

---

*This document specifies every requirement that must be satisfied for ECHO CHAMBER v1.0. No feature exists without a traceable requirement. Changes require Commander approval and version bump.*
