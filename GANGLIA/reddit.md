# 🤖 REDDIT GANGLION — IMPLEMENTATION SPECIFICATION

> **ECHO CHAMBER v1.0**  
> **Document ID:** EC-REDDIT-SPEC-001  
> **Version:** 1.0  
> **Date:** 2026-06-12  
> **Depends on:** BRAIN.md, SPEC.md  
> **Target Phase:** Phase 1 (L1/L2) → Phase 2 (L3) → Phase 3 (L3 ghost posts)

---

## 1. GANGLION OVERVIEW

### 1.1 Purpose
The Reddit Ganglion is an autonomous LangGraph sub-graph that receives dispatch orders from the Cortex and executes content operations on Reddit — from intelligence gathering through content deployment and outcome monitoring.

### 1.2 Platform Characteristics
| Characteristic | Implication |
|---------------|-------------|
| Community-moderated | Content must match subreddit culture or face removal |
| Karma-gated | Low-karma accounts are rate-limited and distrusted |
| Anti-astroturfing detection | Reddit actively detects coordinated posting patterns |
| Text-first platform | Content quality matters more than production value |
| Upvote velocity matters | First 30 minutes determine post trajectory |
| Niche depth | Subreddits are hyper-specific communities, not general audiences |

### 1.3 Account Requirements
| Account Type | Min Age | Min Karma | Max Posts/Day | Use Case |
|-------------|---------|-----------|---------------|----------|
| Ghost (New) | 90 days | 500 | 1 | Low-risk subreddits, comments only |
| Ghost (Established) | 180 days | 2,000 | 2 | Primary posting, higher-visibility subs |
| Ghost (Veteran) | 365+ days | 10,000+ | 3 | r/all-potential posts, controversial topics |
| Official (if applicable) | N/A | N/A | 1-2 | Brand announcements, AMAs |

---

## 2. GANGLION STATE SCHEMA

```python
from typing import TypedDict, List, Optional, Literal
from datetime import datetime
from langgraph.graph import StateGraph

class RedditGanglionState(TypedDict):
    # ── Inbound from Cortex ────────────────
    dispatch_id: str
    client_id: str
    signal_id: Optional[str]           # If triggered by a signal
    target_subreddit: str
    content_type: Literal["post", "comment", "crosspost"]
    content_params: "RedditContentParams"
    autonomy_level: int                # 0-4
    priority: int                      # 1-5

    # ── Injected at Runtime ───────────────
    voice_profile: "VoiceProfile"
    client_constraints: "ClientConstraints"

    # ── Ganglion Internal State ────────────
    # Account Selection
    selected_account_id: Optional[str]
    account_available: bool

    # Context
    subreddit_context: Optional["SubredditContext"]
    recent_echo_content: List[dict]

    # Content
    generated_title: Optional[str]
    generated_body: Optional[str]
    generated_comment_strategy: Optional[List["CommentPlan"]]
    selected_flair: Optional[str]

    # Guardrails
    guardrail_passed: bool
    guardrail_violations: List[str]

    # Human Gate
    approval_status: Optional[Literal["pending", "approved", "rejected", "edited"]]
    human_edited_content: Optional[dict]

    # Scheduling
    scheduled_time: Optional[datetime]
    jitter_applied: int                # minutes

    # Deployment
    deployment_method: Optional[Literal["api", "browser"]]
    post_url: Optional[str]
    post_id: Optional[str]
    deployment_error: Optional[str]

    # Monitoring
    monitor_start: Optional[datetime]
    monitor_end: Optional[datetime]
    metrics: Optional["RedditMetrics"]
    anomalies: List[str]

    # Final
    status: Literal["pending", "in_progress", "awaiting_approval",
                    "scheduled", "deployed", "monitoring", "complete", "failed"]
```

### 2.1 Supporting Types

```python
class RedditContentParams(TypedDict):
    hook_type: str                     # "pain_point", "question", "story", "tutorial", "news"
    angle: str                         # Specific angle for this post
    keywords: List[str]                # Must-include terms
    avoid_keywords: List[str]          # Must-avoid terms
    target_sentiment: str              # "positive", "neutral", "rage-bait" (careful)
    include_link: bool
    link_destination: Optional[str]

class SubredditContext(TypedDict):
    top_posts: List[dict]              # Title, upvotes, comments, flair for top 25
    rising_posts: List[dict]           # Top 10 rising
    mod_activity: List[dict]           # Recent sticky posts, rule changes
    sentiment: float                   # -1.0 to 1.0
    active_hours: List[int]            # Peak activity hours (0-23 UTC)
    banned_words: List[str]            # Auto-mod filtered terms
    content_preferences: dict          # "text_posts_perform_better": true, etc.

class CommentPlan(TypedDict):
    position: Literal["early_reply", "defense", "question_response", "humor"]
    trigger_condition: str             # "if someone asks about pricing", "if post gets negative comment"
    voice: str                         # Sub-voice for this reply type
    template_angle: str

class RedditMetrics(TypedDict):
    upvotes: int
    downvotes: int
    upvote_ratio: float
    comment_count: int
    awards: int
    reports: int
    removed: bool
    removal_reason: Optional[str]
    peak_hour: int
    engagement_rate: float             # (upvotes+comments) / subreddit_members * 100
    sentiment_score: float             # Comment sentiment aggregate
    comment_reply_count: int           # How many comments we replied to
    link_clicks: Optional[int]
```

---

## 3. NODE SPECIFICATIONS

### 3.1 ACCOUNT SELECTOR

**Priority:** P0  
**LLM Required:** No (rules-based with scoring)

#### Algorithm
```
1. Query PostgreSQL: accounts WHERE platform='reddit' AND status='active'
2. Filter: account is member of target_subreddit
3. Filter: account has not posted in target_subreddit in last 24 hours
4. Filter: account cooldown window has elapsed
5. Score remaining accounts:
   score = (karma / 1000) * 0.4
         + (account_age_days / 365) * 0.2
         + (posts_in_this_subreddit * 0.1)
         + (avg_upvote_ratio_in_this_subreddit * 0.3)
6. Add randomness factor: ±10% to avoid always picking same account
7. Return highest-scoring account
```

#### Edge Cases
- No accounts available → set `account_available = False`, status = `failed`, report to Cortex
- Only 1 account available → use it, but flag low redundancy
- Account was recently reported in target subreddit → deprioritize

---

### 3.2 CONTEXT LOADER

**Priority:** P0  
**LLM Required:** No (API data fetching)

#### Data Sources (Priority Order)
1. **PRAW API** — `subreddit.hot(limit=25)`, `subreddit.rising(limit=10)`, `subreddit.sticky()`, `subreddit.rules`
2. **Pushshift/Arctic Shift** (if available) — Historical data for pattern analysis
3. **Web scraping** — Fallback if API returns incomplete

#### Processing
- Extract common topics from top posts (keyword extraction)
- Detect sentiment: positive/negative/neutral ratio in top comments
- Identify content formats that are performing well (text posts vs links vs images)
- Log recent Echo Chamber posts in this subreddit with outcomes

#### Timeout
- 10 seconds for data fetch. If timeout, proceed with cached context from last fetch (if < 1 hour old).

---

### 3.3 CONTENT GENERATOR

**Priority:** P0  
**LLM Required:** Yes (medium-large: Claude Sonnet / GPT-4)

#### Prompt Structure
```xml
<system>
You are the Reddit content generator for ECHO CHAMBER.
You write posts that blend perfectly into their target subreddit.

CRITICAL RULES:
- Never sound like marketing. Sound like a real person in this community.
- Match the subreddit's tone, vocabulary, and posting style exactly.
- Never fabricate personal experiences. Use hypothetical framing: "I've noticed..."
- Never mention the product name until it's natural and earned.
- Include #ad disclosure when required.
</system>

<voice_profile>
{{voice_profile}}
</voice_profile>

<subreddit_context>
Subreddit: {{target_subreddit}}
Current top post themes: {{top_themes}}
Dominant sentiment: {{sentiment}}
Content formats performing well: {{winning_formats}}
Active hours: {{active_hours}}
Taboo topics: {{banned_words}}
</subreddit_context>

<content_parameters>
Hook type: {{hook_type}}
Angle: {{angle}}
Keywords to include: {{keywords}}
Keywords to avoid: {{avoid_keywords}}
Target sentiment: {{target_sentiment}}
</content_parameters>

<recent_echo_content>
These are recent posts from our network in this subreddit. 
Do NOT repeat or closely resemble these:
{{recent_echo_content}}
</recent_echo_content>

<output_format>
Generate:
1. Title (max 300 chars, scroll-stopping, native to this subreddit)
2. Body (markdown, authentic length for this sub's style)
3. Flair (if applicable)
4. Comment strategy (3-5 planned replies with trigger conditions)
</output_format>
```

#### Guardrails Within Generation
- The LLM prompt itself enforces voice profile boundaries
- Post-generation validation by guardrail node (separate pass)
- Temperature: 0.8 (creativity) with top_p: 0.9

---

### 3.4 GUARDRAIL VALIDATOR

**Priority:** P0  
**LLM Required:** Yes (small model for classification tasks)

#### Validation Pipeline (Sequential, Fail-Fast)
```
1. TOXICITY CHECK (small LLM classifier)
   → Block if: hate speech, harassment, personal attacks

2. IMPERSONATION CHECK (string match + LLM)
   → Block if: content claims to be a specific real person

3. COMPETITOR SMEAR CHECK (keyword + sentiment)
   → Block if: competitor name + negative sentiment
   → Allow if: competitor name + neutral/positive sentiment (configurable)

4. FAKE REVIEW CHECK (LLM classifier)
   → Block if: reads like a testimonial without real user source

5. DARK PATTERN CHECK (LLM classifier)
   → Block if: urgency manipulation, hidden conditions, misleading claims

6. AGE GATE CHECK (keyword + LLM)
   → Block if: content targets or appeals to minors

7. PLATFORM TOS CHECK (rules engine + LLM)
   → Block if: violates Reddit content policy

8. PLAGIARISM CHECK (embedding similarity)
   → Flag if: cosine similarity > 0.85 to recent post in subreddit
   → Block if: > 0.95

9. #AD DISCLOSURE CHECK
   → If content contains affiliate link → append disclosure
   → Disclosure text: "(full disclosure: I may receive compensation if you use this link, but I genuinely use and recommend this product)"
```

#### Output
```python
class GuardrailResult(TypedDict):
    passed: bool
    checks_run: List[str]
    violations: List[dict]  # [{check: "fake_review", severity: "hard", detail: "..."}]
    modified_content: Optional[str]  # If #ad disclosure appended
    requires_human_review: bool  # True if soft guard violated
```

---

### 3.5 HUMAN GATE

**Priority:** P0  
**LLM Required:** No

#### Behavior by Autonomy Level
| Level | Gate Behavior |
|-------|--------------|
| L0 | Content not generated — Commander creates content directly |
| L1 | Content generated → Commander reviews → Commander posts |
| L2 | Content generated → Commander reviews in batch → System posts on approval |
| L3 | Content generated + auto-posted → Commander can `/kill` within kill_window (default: 30 min) |
| L4 | Content generated + auto-posted → No Commander gate (monitoring only) |

#### Discord Embed Format (L1/L2)
```
Title: Pending Approval — r/{subreddit}
Color: YELLOW
Fields:
  - Client: {client_id}
  - Account: Ghost #{id} ({karma} karma, {age} old)
  - Autonomy: L{level}
  - Hook Type: {hook_type}
  - Angle: {angle}
  - Content Preview: [title] \n\n [body preview 300 chars]
  - Cortex Rationale: {rationale}
Buttons: [✅ Approve] [❌ Reject] [✏️ Edit]
```

#### Commander Actions
- **Approve** → Update `approval_status = "approved"`, forward to scheduler.
- **Reject** → Update `approval_status = "rejected"`, log feedback to episodic memory, END.
- **Edit** → Commander provides edited text → stored in `human_edited_content` → proceed to scheduler with edited content.

---

### 3.6 SCHEDULER

**Priority:** P0  
**LLM Required:** No

#### Algorithm
```
1. Get subreddit peak activity hours from context
2. Find next available window:
   - Within peak hours if within next 6 hours
   - Otherwise, use next day's peak hour
3. Check for Echo Chamber posts in subreddit within ±2 hours
   - If collision: shift by 30 minutes
4. Apply jitter: random(-15, +15) minutes
5. Set scheduled_time
6. If autonomy L3/L4: deploy immediately (jitter still applies)
```

#### Constraints
- Minimum 2 hours between any Echo Chamber posts in same subreddit
- Maximum 3 posts per day per subreddit (across all accounts)
- Account-level: respect per-account daily limit

---

### 3.7 DEPLOYER

**Priority:** P0  
**LLM Required:** No

#### Primary: PRAW API
```python
import praw
reddit = praw.Reddit(
    client_id=account.credentials.client_id,
    client_secret=account.credentials.client_secret,
    user_agent=account.fingerprint.user_agent,
    username=account.credentials.username,
    password=account.credentials.password
)
subreddit = reddit.subreddit(target_subreddit)
submission = subreddit.submit(
    title=title,
    selftext=body,
    flair_id=flair_id
)
```

#### Fallback: Playwright Browser
- Trigger: PRAW returns CAPTCHA, 403, or rate limit
- Browser automation: open Reddit, login, navigate to submit page, type title + body (with human-like typing delay), select flair, submit
- Proxy: Rotated per account via ProxyRouter

#### Error Handling
```
1. Attempt 1: PRAW API (with account-specific User-Agent)
2. Attempt 2: PRAW API (with different proxy)
3. Attempt 3: Playwright browser (simulated human)
4. All failed → Mark account for investigation, escalate to Commander, try different account
```

#### Post-Deployment
- Capture `post_url` and `post_id`
- Update `deployments` table in PostgreSQL
- Update account `last_used_at` and status to `cooldown`
- Begin monitoring window

---

### 3.8 MONITOR

**Priority:** P0  
**LLM Required:** No (metrics) + Yes/small (comment selection for replies)

#### Monitoring Schedule
| Time Since Post | Check Frequency | Actions |
|----------------|-----------------|---------|
| 0-1 hours | Every 5 minutes | Check removal, vote velocity |
| 1-6 hours | Every 15 minutes | Check removal, top comments, reply opportunities |
| 6-24 hours | Every 1 hour | Check removal, comment replies, engagement |
| 24-72 hours | Every 4 hours | Final metrics collection |

#### Auto-Reply Engine (L3/L4 Only)
For L3/L4 deployments, the ganglion can auto-reply to comments:

1. **Comment Selection:** Score comments by:
   - Relevance (semantic similarity to post topic)
   - Engagement potential (comment length, question marks)
   - Risk (avoid hostile/troll comments)

2. **Reply Generation:** LLM with voice profile injection:
   - Match OP's established voice
   - Natural, not defensive
   - Add value, not just agreement
   - Never spam product links

3. **Reply Rate Limit:** Max 3 auto-replies per post in first 24 hours.

#### Anomaly Detection
- Sudden downvote surge (< -10 votes in 5 minutes) → flag
- Mod removal → capture reason, mark account
- "Astroturfing" accusation in comments → flag, reduce replies
- Post hits r/all → increase monitoring frequency

---

### 3.9 REPORTER

**Priority:** P0  
**LLM Required:** No

#### Report Content (Sent to Cortex LEARN node)
```python
class RedditGanglionReport(TypedDict):
    dispatch_id: str
    deployment_id: str
    status: str                       # "success", "mod_removed", "low_engagement", "viral"
    metrics: RedditMetrics
    anomalies: List[str]
    account_health_update: dict       # {account_id: {karma_delta, status_change}}
    lessons_generated: List[str]      # Human-readable insights
    training_record: TrainingRecord   # For fine-tuning pipeline
```

#### Triggering LEARN
After report is compiled:
1. Store full deployment record in episodic_memory
2. Extract lessons via LLM: "Given post achieved {outcome}, what patterns explain this?"
3. Update semantic_memory with extracted patterns
4. Update account health in procedural memory
5. Cortex signal: "Reddit deployment complete. Status: {status}. Outcome: {metrics}"

---

## 4. GRAPH CONSTRUCTION

```python
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.postgres import PostgresSaver

def build_reddit_ganglion(checkpointer: PostgresSaver) -> StateGraph:
    graph = StateGraph(RedditGanglionState)

    # Add nodes
    graph.add_node("account_select", account_selector)
    graph.add_node("context_load", context_loader)
    graph.add_node("content_generate", content_generator)
    graph.add_node("guardrail_validate", guardrail_validator)
    graph.add_node("human_gate", human_gate)
    graph.add_node("schedule", scheduler)
    graph.add_node("deploy", deployer)
    graph.add_node("monitor", monitor)
    graph.add_node("report", reporter)

    # Entry point
    graph.set_entry_point("account_select")

    # Edges
    graph.add_edge("account_select", "context_load")
    graph.add_edge("context_load", "content_generate")
    graph.add_edge("content_generate", "guardrail_validate")

    # Guardrail conditional edge
    graph.add_conditional_edges("guardrail_validate", after_guardrail, {
        "passed": "human_gate",
        "soft_violation": "human_gate",  # Pass through but flagged
        "hard_violation": END            # Blocked, report failure
    })

    # Human gate conditional edge
    graph.add_conditional_edges("human_gate", after_gate, {
        "approved": "schedule",
        "auto_approved": "deploy",        # L3/L4: skip schedule, deploy now
        "rejected": END,
        "timeout": END                    # Auto-reject on timeout
    })

    graph.add_edge("schedule", "deploy")
    graph.add_edge("deploy", "monitor")
    graph.add_edge("monitor", "report")
    graph.add_edge("report", END)

    return graph.compile(checkpointer=checkpointer)
```

### Conditional Edge Functions

```python
def after_guardrail(state: RedditGanglionState) -> str:
    if not state["guardrail_passed"]:
        return "hard_violation"
    if state.get("requires_human_review"):
        return "soft_violation"
    return "passed"

def after_gate(state: RedditGanglionState) -> str:
    if state["approval_status"] == "approved":
        return "approved"
    if state["approval_status"] == "rejected":
        return "rejected"
    if state["autonomy_level"] >= 3:
        return "auto_approved"
    # L1/L2 awaiting Commander
    # On timeout, auto-reject
    return "timeout"
```

---

## 5. ERROR SCENARIOS & RECOVERY

| Scenario | Detection | Recovery |
|----------|-----------|----------|
| Account banned during deployment | API returns 403/forbidden | Mark account `burned`. Select new account. Retry. Escalate if pool depleted. |
| Subreddit goes private | PRAW `subreddit.quarantined` or access error | Flag subreddit status. Report to Cortex. Skip this subreddit for 7 days. |
| Content removed by mods | Monitor detects removal | Log reason if available. Update account health. Do not re-post same content. |
| Post downvoted to zero | Monitor detects vote ratio < 0.3 | Accept loss. Log to memory as negative example. Do not delete (looks suspicious). |
| CAPTCHA on deploy | API returns CAPTCHA | Switch to browser fallback. If browser also CAPTCHA, mark account suspect. |
| Rate limit hit | API returns 429 | Exponential backoff. If persistent, reduce deployment frequency for this account. |
| LLM generation timeout | > 30 seconds | Retry once with lower temperature. If still timeout, use cached template + voice fill. |

---

## 6. TESTING STRATEGY

### 6.1 Unit Tests (Per Node)
- Account selector: correct scoring, tiebreaking, no-account-available
- Guardrail: each check type (toxic, impersonation, fake review, etc.)
- Scheduler: timing logic, collision avoidance, jitter range

### 6.2 Integration Tests (Node Chains)
- `select → load → generate` pipeline with mock subreddit data
- `guardrail → gate → schedule → deploy` pipeline with mock Reddit API

### 6.3 E2E Tests (Real Platform - Staging)
- Dedicated test subreddit (private, controlled)
- Test ghost accounts posting to test subreddit
- Verify: content appears correctly, monitoring works, report generates

### 6.4 Dry-Run Mode
- All ganglia support `DRY_RUN=true` env flag
- In dry-run: full pipeline executes but deploy node logs instead of posting
- Used for Commander "what-if" testing: "Show me what you'd post to r/Truckers right now"

---

*This specification defines the complete behavior of the Reddit Ganglion. Implementation must satisfy all requirements. Deviations require Commander approval.*
