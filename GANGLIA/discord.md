# 💬 DISCORD GANGLION — IMPLEMENTATION SPECIFICATION

> **ECHO CHAMBER v1.0**  
> **Document ID:** EC-DISCORD-SPEC-001  
> **Version:** 1.0  
> **Date:** 2026-06-12  
> **Depends on:** BRAIN.md, SPEC.md  
> **Target Phase:** Phase 2

---

## 1. GANGLION OVERVIEW

### 1.1 Purpose
The Discord Ganglion is a dual-mode autonomous LangGraph sub-graph that executes two distinct mission types:
- **Infiltrator Mode:** Ghost accounts join target Discord servers, establish presence, and deploy natural product mentions.
- **Community Mode:** Manage Echo Chamber-owned Discord servers — welcome users, answer questions, monitor sentiment.

### 1.2 Platform Characteristics
| Characteristic | Implication |
|---------------|-------------|
| Real-time chat | Timing matters less; conversational flow matters more |
| Server-isolated | Each server is its own ecosystem — trust doesn't transfer |
| Moderation varies wildly | Some servers are tightly modded, others are free-for-all |
| Relationship-based | Trust takes time; rushing gets you banned |
| Voice channels | Rich interaction but harder to script — not targeted in Phase 1-2 |
| Bot detection improving | Discord actively detects self-botting and automation |

### 1.3 Mode Selection
The Cortex dispatch includes `ganglion_mode` field:
- `ganglion_mode: "infiltrator"` → Infiltrator sub-graph
- `ganglion_mode: "community"` → Community sub-graph
- The mode selects which compiled sub-graph is loaded at dispatch time.

---

## 2. INFILTRATOR MODE

### 2.1 State Schema

```python
class DiscordInfiltratorState(TypedDict):
    # ── Inbound from Cortex ────────────────
    dispatch_id: str
    client_id: str
    ganglion_mode: Literal["infiltrator"]
    mission_type: Literal[
        "discover_servers",
        "join_server",
        "participate",
        "deploy_mention",
        "monitor_opportunity"
    ]
    target_server_id: Optional[str]
    content_params: Optional["DiscordContentParams"]

    # ── Injected at Runtime ───────────────
    voice_profile: "VoiceProfile"
    client_constraints: "ClientConstraints"

    # ── Server Discovery ──────────────────
    discovered_servers: List["DiscoveredServer"]
    selected_server: Optional["DiscoveredServer"]

    # ── Account ────────────────────────────
    account_id: Optional[str]
    join_status: Optional[Literal["pending", "joined", "rejected", "banned"]]

    # ── Lurk Phase ────────────────────────
    lurk_start: Optional[datetime]
    lurk_complete: bool
    server_culture: Optional["ServerCulture"]

    # ── Participation ─────────────────────
    participation_start: Optional[datetime]
    messages_sent: int
    reactions_received: int
    trust_score: float                  # 0.0 - 1.0
    trust_tier: Literal["stranger", "acquaintance", "regular", "trusted"]

    # ── Opportunity Detection ────────────
    opportunities: List["Opportunity"]

    # ── Mention Deploy ───────────────────
    mention_content: Optional[str]
    mention_deployed: bool
    mention_outcome: Optional[Literal["ignored", "engaged", "positive", "negative", "flagged"]]

    # ── Status ────────────────────────────
    status: str
    errors: List[str]
```

### 2.2 Supporting Types

```python
class DiscoveredServer(TypedDict):
    server_id: str
    name: str
    member_count: int
    topic: str
    activity_level: Literal["low", "medium", "high", "very_high"]
    moderation_style: Literal["lax", "moderate", "strict"]
    relevance_score: float             # 0.0 - 1.0 match to client audience
    join_strategy: str                 # "public", "invite_only", "application"
    invite_url: Optional[str]
    risk_assessment: Literal["low", "medium", "high"]  # Ban risk

class ServerCulture(TypedDict):
    dominant_topics: List[str]
    communication_style: str           # "casual", "technical", "meme-heavy", "support-oriented"
    taboo_topics: List[str]
    insider_terms: List[str]           # Community-specific jargon
    power_users: List[str]             # Influential members (not for targeting — for context)
    acceptable_humor: str              # "dark", "wholesome", "sarcastic", "none"
    product_discussion_tolerance: str  # "hostile", "neutral", "receptive"

class Opportunity(TypedDict):
    detected_at: datetime
    channel_id: str
    trigger_message: str               # The message that created the opportunity
    opportunity_type: str              # "buying_signal", "pain_point", "competitor_frustration"
    relevance_score: float
    natural_mention_angle: str         # How to naturally mention the product
    urgency: Literal["now", "soon", "monitor"]
```

---

### 2.3 Node Specifications

#### 2.3.1 Server Discovery
**Priority:** P1 | **LLM:** Yes (medium)

**Input:** Client profile (audience, demographic, interests)  
**Output:** Ranked list of DiscoveredServer objects

**Discovery Sources:**
1. Discord Server Discovery (in-app)
2. Disboard.org (public server listing)
3. Top.gg (server listing)
4. Reddit cross-reference (servers mentioned in client's target subreddits)
5. Web search: "{client_audience} Discord server"

**Scoring Algorithm:**
```
relevance_score = (
    topic_match * 0.4 +
    audience_demographic_match * 0.3 +
    activity_level_score * 0.2 +
    size_appropriateness * 0.1
)

Where:
- topic_match: LLM semantic similarity between server description and client product domain
- audience_demographic_match: LLM assessment of server audience vs client target
- activity_level_score: "very_high"=1.0, "high"=0.8, "medium"=0.5, "low"=0.2
- size_appropriateness: 1.0 if 500-50000 members (sweet spot), declining outside range
```

**Risk Filtering:**
- Reject servers with < 100 members (too small, no ROI)
- Reject servers with > 500,000 members (too visible, high ban risk for small ghost presence)
- Reject servers flagged as "strict moderation" unless trust_tier can be built first
- Reject servers where product category is explicitly banned in rules
- Flag servers requiring phone verification → require veteran accounts only

#### 2.3.2 Join + Lurk
**Priority:** P1 | **LLM:** No (API + rules)

**Join Phase:**
1. Ghost account joins server via invite URL (or applies if application-only)
2. Parse #rules channel → confirm acceptance
3. If server has verification gate (reaction, captcha, intro) → complete it
4. Set `join_status` to `joined`
5. Begin lurk period

**Lurk Phase (Default: 7 days):**
1. Read all public channels (no posting)
2. Log:
   - Message frequency by channel
   - Active hours
   - Dominant conversation topics
   - Power users and their communication styles
   - Insider jargon and memes
   - Taboo topics that get negative reactions
   - How product mentions are received by the community
3. After lurk period: generate `ServerCulture` profile via LLM

**Safety Rules:**
- Never read DMs of other users
- Never join voice channels (Phase 1-2)
- Never react to messages during lurk (lurk means invisible)
- If server has "introduce yourself" requirement: generate generic persona intro

#### 2.3.3 Participation Engine
**Priority:** P1 | **LLM:** Yes (medium-large)

**Transition from Lurk:**
After lurk period complete and ServerCulture generated, transition to participation.

**Message Generation:**
```xml
<system>
You are a member of this Discord server. You are NOT marketing anything.
You are a real person who shares genuine interests with this community.

Generate a Discord message that:
- Matches the server's communication style exactly
- Uses community insider terms naturally
- Adds value (help, insight, humor — never just "agree")
- Is 1-3 sentences (Discord is chat, not essays)
- NEVER mentions products, brands, or services
- Feels like it was typed by a human, not generated
</system>

<server_culture>
{{server_culture}}
</server_culture>

<recent_conversation>
Last 20 messages in target channel:
{{recent_messages}}
</recent_conversation>

<persona>
You are a {{persona_description}} who has been in this community for {{days_in_server}} days.
Your communication style: {{communication_style}}
</persona>
```

**Posting Schedule:**
- Week 2-3: 1-2 messages/day, spread across active hours
- Week 4+: 3-5 messages/day, more active participation
- 30% replies to existing conversations, 70% new contributions
- Add jitter: ±30 minute randomization on posting times
- Never post when server is dead (< 5 messages/hour)

**Trust Score Tracking:**
```python
trust_score = min(1.0, (
    base_trust +                    # 0.0 at participation start
    (messages_sent * 0.01) +        # Max +0.5 from volume (capped at 50 messages)
    (reactions_received * 0.02) +   # Max +0.4 from engagement
    (days_active * 0.005) +         # Max +0.2 from tenure
    (replies_received * 0.03)       # Max +0.3 from being part of conversations
))

# Adjusted for negatives
trust_score -= (warnings * 0.2)
trust_score -= (message_deletions * 0.1)
trust_score = max(0.0, trust_score)

trust_tier = (
    "stranger" if trust_score < 0.2 else
    "acquaintance" if trust_score < 0.4 else
    "regular" if trust_score < 0.7 else
    "trusted"
)
```

**Escalation Trigger:**
If trust_score < 0.0 or account receives mod warning → pause participation, escalate to Commander.

#### 2.3.4 Opportunity Detection
**Priority:** P1 | **LLM:** Yes (small, continuous scanning)

**Scanning Method:**
- Poll all readable channels every 5 minutes (or use Discord gateway events for real-time)
- For each new message batch, run small LLM classifier:
  - "Does this message contain a buying signal for {product_category}?"
  - "Does this message express frustration with {pain_point}?"
  - "Does this message mention dissatisfaction with {competitor_category}?"

**Opportunity Types:**
| Type | Example Message | Action |
|------|----------------|--------|
| `buying_signal` | "Anyone know a good app for tracking mileage?" | High priority — natural mention |
| `pain_point` | "IFTA paperwork is going to be the death of me" | Medium priority — empathize first, product later |
| `competitor_frustration` | "I've been using {competitor} and it keeps crashing" | Low priority — don't bash, just relate |
| `general_question` | "How do you guys handle logbook compliance?" | Monitor — potential education opportunity |

**Output:** `Opportunity` object sent to Cortex for routing (Cortex decides whether to deploy mention).

#### 2.3.5 Natural Mention Deploy
**Priority:** P1 | **LLM:** Yes (medium-large) | **Autonomy:** Always L1

**Critical Rule: Product mentions in infiltrated servers require Commander approval. No exceptions.**

```xml
<system>
You are deploying a NATURAL product mention in a Discord server where you've built trust.

THIS IS NOT AN AD. You are a community member sharing something you've found useful.

Generate a Discord message that:
- Responds directly to the opportunity (buying signal / pain point / question)
- Mentions the product naturally, as a recommendation from personal experience
- Uses the server's communication style
- Is 1-3 sentences
- Includes ONE specific, honest detail about the product
- Does NOT include links unless the conversation explicitly asks for them
- Does NOT sound like a pitch — "oh yeah I've been using X for a while now, the Y feature is actually pretty solid"
</system>

<opportunity>
{{opportunity}}
</opportunity>

<product_info>
Product: {{product_name}}
Key feature for this use case: {{relevant_feature}}
Honest limitation (mention if relevant): {{limitation}}
</product_info>

<voice_profile>
{{voice_profile}}
</voice_profile>

<server_culture>
{{server_culture}}
</server_culture>
```

**Restrictions:**
- Max 1 product mention per server per 7 days
- Max 1 product mention per account per 3 days (across all servers)
- Never mention product in first 14 days of participation
- Never mention product if trust_tier < "regular"
- Never mention product in servers flagged as "strict moderation"

**Post-Mention Monitoring:**
- Monitor for 24 hours after mention
- If mention receives negative reactions → Do NOT defend. Let it fade.
- If mention receives positive engagement → Do NOT over-engage. 1-2 follow-ups max.
- If mention flagged by mod → Accept. Do not argue. Pause all activity. Escalate.

---

## 3. COMMUNITY MODE

### 3.1 State Schema

```python
class DiscordCommunityState(TypedDict):
    dispatch_id: str
    client_id: str
    ganglion_mode: Literal["community"]
    mission_type: Literal[
        "welcome_user",
        "answer_question",
        "announce",
        "sentiment_scan",
        "engagement_event"
    ]
    target_server_id: str             # Echo Chamber-owned server
    channel_id: Optional[str]
    user_id: Optional[str]

    voice_profile: "VoiceProfile"
    client_constraints: "ClientConstraints"

    # Welcome
    welcome_message: Optional[str]
    onboarding_flow: Optional[List[str]]  # Steps sent to new user

    # Q&A
    question: Optional[str]
    answer: Optional[str]
    confidence: float                 # 0.0-1.0, how confident is the answer

    # Announcement
    announcement_content: Optional[str]
    cross_post_targets: List[str]     # Other platforms to cross-post

    # Sentiment
    sentiment_score: float
    sentiment_trend: str
    flagged_users: List[str]

    # Status
    status: str
```

### 3.2 Node Specifications

#### 3.2.1 Welcome Engine
**Priority:** P2 | **LLM:** Yes (small, templated)

**Trigger:** New member joins Echo Chamber-owned Discord server.

**Flow:**
1. Auto-DM new member: "Welcome to {server_name}! {personalized_greeting}"
2. Offer onboarding: "Want a quick tour? React with 👋"
3. If user reacts: send 3-5 message onboarding flow explaining channels, product basics, community norms.
4. Assign base role.
5. Log member join to database.

**Personalization:** LLM generates welcome message based on:
- User's Discord username (avoid overly familiar)
- How they found the server (if known via invite tracking)
- Current server events or discussions

#### 3.2.2 Support Router
**Priority:** P2 | **LLM:** Yes (small, RAG-based)

**Trigger:** User asks question in support channel or @mentions bot.

**Flow:**
1. Embed user question → search FAQ database (pgvector similarity)
2. If match found (confidence > 0.85): answer with FAQ entry
3. If medium match (0.6-0.85): answer with "Here's what I found... does this help?" + offer human escalation
4. If low match (< 0.6): "Great question — let me flag this for the team. Someone will get back to you soon." → escalate to Commander
5. NEVER fabricate answers. If unsure, escalate.

**FAQ Database:** Continuously updated from:
- Real user questions + Commander-provided answers
- Product documentation
- Common onboarding friction points

#### 3.2.3 Sentiment Monitor
**Priority:** P2 | **LLM:** Yes (small, periodic)

**Scan Schedule:** Every 6 hours, scan last 500 messages.

**Analysis:**
- Per-user sentiment: positive/neutral/negative
- Aggregate server sentiment trend: improving/stable/declining
- Flag: users with consistently negative sentiment (potential churn)
- Flag: users mentioning competitor products
- Flag: users expressing confusion about product

**Output:** Sentiment report posted to `#📋 client-{name}` Commander channel.

#### 3.2.4 Announcement Sync
**Priority:** P2 | **LLM:** Yes (for reformatting)

**Trigger:** Commander or Cortex schedules an announcement.

**Flow:**
1. Receive announcement content + target platforms
2. Reformat for Discord (appropriate length, embed or plain text, @everyone if warranted)
3. Post to announce channel
4. If cross-post targets exist: dispatch to other ganglia with reformatted content
5. Pin announcement if important
6. Monitor engagement (reactions, replies)

#### 3.2.5 Engagement Events
**Priority:** P3 | **LLM:** Yes (medium)

**Trigger:** Scheduled or Cortex-suggested.

**Event Types:**
- AMA (Ask Me Anything) with product team → schedule, announce, moderate
- Feedback thread → post prompt, collect responses, summarize
- Community challenge → announce, track participation, celebrate winners
- Product update watch party → schedule, live-chat coordination

---

## 4. GRAPH CONSTRUCTION

### 4.1 Infiltrator Sub-Graph

```python
def build_discord_infiltrator_graph(checkpointer) -> StateGraph:
    graph = StateGraph(DiscordInfiltratorState)

    graph.add_node("discover_servers", server_discovery)
    graph.add_node("join_lurk", join_and_lurk)
    graph.add_node("participate", participation_engine)
    graph.add_node("detect_opportunity", opportunity_detector)
    graph.add_node("deploy_mention", mention_deployer)
    graph.add_node("monitor_mention", mention_monitor)

    # Entry: depends on mission_type
    graph.add_conditional_edges("__start__", route_infiltrator_mission, {
        "discover": "discover_servers",
        "join": "join_lurk",
        "participate": "participate",
        "detect": "detect_opportunity",
        "deploy": "deploy_mention"
    })

    graph.add_edge("discover_servers", END)  # Results go to Cortex for routing
    graph.add_edge("join_lurk", "participate")  # Auto-transition after lurk
    graph.add_edge("participate", "detect_opportunity")
    graph.add_edge("detect_opportunity", END)  # Opportunities sent to Cortex
    graph.add_edge("deploy_mention", "monitor_mention")
    graph.add_edge("monitor_mention", END)

    return graph.compile(checkpointer=checkpointer)
```

### 4.2 Community Sub-Graph

```python
def build_discord_community_graph(checkpointer) -> StateGraph:
    graph = StateGraph(DiscordCommunityState)

    graph.add_node("welcome", welcome_engine)
    graph.add_node("answer_question", support_router)
    graph.add_node("sentiment_scan", sentiment_monitor)
    graph.add_node("announce", announcement_sync)
    graph.add_node("engagement_event", engagement_events)

    graph.add_conditional_edges("__start__", route_community_mission, {
        "welcome": "welcome",
        "answer": "answer_question",
        "sentiment": "sentiment_scan",
        "announce": "announce",
        "event": "engagement_event"
    })

    for node in ["welcome", "answer_question", "sentiment_scan", "announce", "engagement_event"]:
        graph.add_edge(node, END)

    return graph.compile(checkpointer=checkpointer)
```

---

## 5. DISCORD API USAGE

### 5.1 Authentication
- Bot token: Used for Community Mode operations (own servers)
- User tokens: Used for Infiltrator Mode (ghost accounts acting as real users)
- **Critical:** User tokens are against Discord ToS for automation. This is an accepted risk. Phase 1-2 mitigates with human-like behavior patterns. Phase 4+ evaluates official alternatives.

### 5.2 Rate Limiting
- Discord global: 50 requests per second per token
- Per-route limits vary
- Ganglion implements exponential backoff + jitter
- Queue system for cross-account coordination (avoid burst from multiple ghosts)

### 5.3 Gateway (WebSocket) Usage
- Community Mode: Connect to gateway for real-time events (member join, messages)
- Infiltrator Mode: REST API only in Phase 1-2 (gateway connection = higher detection risk)
- Phase 3+: Evaluate gateway for infiltrator accounts (better opportunity detection)

---

## 6. SAFETY & DETECTION AVOIDANCE

### 6.1 Behavioral Fingerprint Diversity
Each ghost account has a unique behavioral profile:
- Typing speed variation (message send delay: 30s-5min after reading)
- Active hours (different timezone patterns)
- Response patterns (some accounts reply fast, some slow)
- Vocabulary quirks (slight variations — some use "lol", some use "haha")
- Emoji usage patterns

### 6.2 Detection Red Flags (AVOID)
- Joining multiple servers in rapid succession
- Identical messages across servers
- Posting at machine-like intervals
- Never being "offline" (always responds instantly)
- Never making typos or casual mistakes
- Perfect grammar in casual servers
- Joining voice channels but never speaking

### 6.3 If Detected
1. Cease all activity on flagged account immediately
2. Mark account `flagged` in database
3. Do not login with that account for 72 hours
4. After cooldown: evaluate if account can be rehabilitated
5. If banned: burn account, do not create new account with same IP/email

---

## 7. ERROR SCENARIOS

| Scenario | Detection | Recovery |
|----------|-----------|----------|
| Account banned from server | API returns 403 or role stripped | Mark account `burned` for that server. Do not rejoin with different account (linked ban risk). |
| Server requires phone verification | Join attempt fails | Skip server. Flag in discovery: "needs verified account". |
| Message flagged by automod | Message deleted by server bot | Pause posting for 24h. Analyze what triggered filter. Adjust content rules. |
| Other users suspect bot | Accusatory message detected | Reduce posting frequency. Add more "human" variation. If persists, withdraw account. |
| Discord API outage | 5xx errors from Discord API | Queue operations. Retry with backoff when API recovers. |
| Rate limit burst | 429 responses | Exponential backoff per account. Spread queued operations. |

---

*This specification defines the complete behavior of the Discord Ganglion. Implement Infiltrator Mode first (Phase 2), Community Mode second. All product mentions require Commander approval. No exceptions.*
