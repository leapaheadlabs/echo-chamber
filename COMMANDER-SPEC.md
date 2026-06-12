# 🎛️ COMMANDER — DISCORD INTERFACE SPECIFICATION

> **ECHO CHAMBER v1.0**  
> **Document ID:** EC-COMMANDER-SPEC-001  
> **Version:** 1.0  
> **Date:** 2026-06-12  
> **Depends on:** BRAIN.md, SPEC.md  
> **Target Phase:** Phase 1

---

## 1. OVERVIEW

### 1.1 Purpose
The Commander is the human-in-the-loop interface for ECHO CHAMBER. It is a Discord bot + channel architecture that provides full operational control, situational awareness, and decision-making capability.

### 1.2 Design Philosophy
- **Discord-first:** No web UI. The Discord server IS the command center.
- **No-BS feedback:** Every embed tells you what happened, why, and what you can do about it — in that order.
- **One-touch decisions:** Approve, Reject, Kill — all one button click.
- **Full evidence trail:** Every decision is logged. Every action is reversible (kill window). Every outcome is reported.
- **Silent until necessary:** The Commander surfaces what matters. It does not spam.

### 1.3 Access Control
| Role | Permissions |
|------|------------|
| **Commander** | All commands, all channels, all approval authority, `/kill` |
| **Observer** | Read-only: `/status`, `/memory search`. Cannot approve/kill. |
| **Bot** | System messages, embeds, monitoring output |

---

## 2. CHANNEL ARCHITECTURE

### 2.1 Channel Map

```
ECHO CHAMBER COMMAND
├── #📡 signals-feed           Real-time intel stream
├── #🎯 active-campaigns       What's running right now
├── #✅ approval-queue         Content waiting for Commander
├── #🚨 escalation             Threats, bans, crises
├── #📊 daily-sitrep           Auto-generated EOD summary
├── #🗣️ commander-chat         Direct Cortex interaction
├── #📋 client-vault           Category: one channel per active client
│   ├── #client-truckerechelon
│   └── #client-future-client
└── #⚙️ system-health           Cortex, ganglia, account pool status
```

### 2.2 Channel Details

#### #📡 signals-feed
**Purpose:** Unfiltered signal stream — the brain's raw intel.

**Message Format:**
```yaml
Embed:
  Color: Based on classification (trend=BLUE, mention=GREEN, opportunity=GOLD, threat=RED, noise=GRAY)
  Title: "{classification_emoji} {source}: {summary}"
  Fields:
    - Type: trend | mention | opportunity | threat | noise
    - Source: Reddit, Discord, RSS, manual
    - Confidence: 0.XX
    - Cortex Action: deploy | queue | escalate | ignore | monitor
    - Target Client: {client_id} (if matched)
  Footer: Signal ID {signal_id}
```

**Commander Actions:** None required. Informational only. Escalations routed separately.

#### #🎯 active-campaigns
**Purpose:** Dashboard of everything running right now.

**Pinned Messages:**
1. **Campaign Overview** (updated hourly): Table of active campaigns with client, platform, deploy count, status.
2. **Account Pool Status** (updated hourly): Available/active/cooldown/burned counts per platform.

**Message Format (per deployment):**
```yaml
Embed:
  Color: GREEN (success), YELLOW (pending), RED (failed/removed)
  Title: "[{client}] {content_type} → r/{subreddit} | {discord_server}"
  Fields:
    - Status: deployed | monitoring | complete | removed | failed
    - Account: Ghost #{id} ({karma} karma)
    - Posted: {timestamp} | Monitoring until: {timestamp}
    - Engagement: {upvotes}↑ {comments}💬 {ratio}% (if available)
    - Link: {post_url}
  Footer: Dispatch {dispatch_id} | Auto-updates every 15 min during monitoring
```

#### #✅ approval-queue
**Purpose:** Content requiring Commander decision before deployment.

**Embed Format:**
```yaml
Embed:
  Color: YELLOW (awaiting)
  Title: "✋ Approval Required: {platform} post for {client}"
  Fields:
    - Platform: reddit | discord
    - Target: r/{subreddit} | {server_name}
    - Account: Ghost #{id} | {karma} karma | {age} old
    - Autonomy: L{level}
    - Hook Type: {hook_type}
    - Angle: {angle}
    - Priority: {"🔴" if priority >= 4 else "🟡" if priority >= 2 else "🟢"}
    - Cortex Rationale: "{rationale}"
    - Content Preview:
      ```
      {title}
      ---
      {body_preview_300_chars}...
      ```
  Buttons: [✅ Approve] [❌ Reject] [✏️ Edit]
  Footer: Dispatch {dispatch_id} | Expires in {timeout_minutes}min
```

**Timeout Behavior:**
- Default: 4 hours
- On timeout: Auto-reject. Notification: "⏰ Dispatch {id} auto-rejected — Commander did not respond within window."
- Commander can configure timeout per client, per campaign.

**Button Actions:**
| Button | Action | Follow-up |
|--------|--------|-----------|
| [✅ Approve] | Sets dispatch to approved. Content proceeds to scheduler. | Embed color → GREEN. "✅ Approved by {commander_name} at {time}" |
| [❌ Reject] | Sets dispatch to rejected. Feedback prompt. | Modal opens: "Reason for rejection?" (optional). Embed → RED. |
| [✏️ Edit] | Opens modal for Commander to edit content. | Modified content stored. Resubmitted for approval with edited flag. |

#### #🚨 escalation
**Purpose:** Everything that needs Commander attention NOW.

**Severity Levels:**
| Level | Emoji | Color | Example | Auto-Action |
|-------|-------|-------|---------|-------------|
| CRITICAL | 🔴 | RED | 3+ bans in 24h, legal threat, kill switch auto-trigger | Auto-pause all ganglia |
| HIGH | 🟠 | ORANGE | Account banned, platform policy change, major guardrail violation | Auto-pause affected ganglion |
| MEDIUM | 🟡 | YELLOW | Unusual engagement pattern, rate limit warnings, trust score drop | Flag only |
| LOW | 🟢 | GREEN | Minor anomalies, account health degradation | Informational |

**Embed Format:**
```yaml
Embed:
  Color: Based on severity
  Title: "{severity_emoji} {severity}: {title}"
  Description: "{detailed_explanation}"
  Fields:
    - Impact: {what's_affected}
    - Detected: {timestamp}
    - Recommended: {cortex_recommendation}
    - Affected Resources: {list}
  Buttons: [Action buttons based on scenario]
  Footer: Escalation {escalation_id}
```

**Common Escalation Templates:**

*Account Ban:*
```yaml
🔴 CRITICAL: Ghost #3 banned from r/Truckers
Description: Account Ghost-RDT-03 was permanently banned from r/Truckers at {time}.
Impact: 1 of 5 Reddit accounts offline. Reddit ganglion capacity reduced to 80%.
Recommended: Burn account. Rotate proxy. Deploy replacement from maturing pool.
Affected: ghost-rdt-03, r/Truckers campaign, TruckerEchelon Reddit coverage
Buttons: [🔥 Confirm Burn] [🔍 Investigate] [⏸️ Pause Reddit]
```

*Guardrail Violation:*
```yaml
🟠 HIGH: Hard guardrail triggered — fake review detected
Description: Content generated for r/owneroperators was blocked by FAKE_REVIEW check.
Content: "I've been using TruckerEchelon for 6 months and it changed my life..."
Impact: Dispatch blocked. Content not deployed.
Recommended: Review content. Adjust voice profile if generating review-like content.
Buttons: [👀 Review Content] [✏️ Edit Voice Profile]
```

#### #📊 daily-sitrep
**Purpose:** End-of-day summary — the Commander reads this once a day and knows everything.

**Generated:** 23:00 UTC daily (configurable).

**Format:**
```yaml
Embed 1 — Executive Summary:
  Title: "📊 Daily Sitrep — {date}"
  Fields:
    - Active Clients: {count} ({names})
    - Deployments Today: {count} ({success} success, {failed} failed, {removed} removed)
    - Content Auto-Deployed: {count} ({percentage}% autonomous)
    - Commander Approvals: {count} approved, {count} rejected, {count} edited
    - Account Health: {active} active, {cooldown} cooldown, {burned} burned, {maturing} maturing
    - Escalations: {count} ({critical} critical, {high} high)
    - Top Performer: "{post_title}" — {upvotes}↑ {comments}💬 on r/{subreddit}

Embed 2 — Performance by Client:
  Table: Client | Deployments | Avg Engagement | Signups Attributed | Status

Embed 3 — Upcoming (Next 24h):
  List of scheduled deployments with platform, target, time

Embed 4 — System Health:
  - Cortex: ✅ | ⚠️ | 🔴
  - Reddit Ganglion: ✅ | ⚠️ | 🔴
  - Discord Ganglion: ✅ | ⚠️ | 🔴
  - LLM API: ✅ | ⚠️ | 🔴
  - PostgreSQL: ✅ | ⚠️ | 🔴
  - Proxy Pool: ✅ | ⚠️ | 🔴
  - Cost Today: ${amount}
  - Cost MTD: ${amount}
```

#### #🗣️ commander-chat
**Purpose:** Direct Cortex interaction. The Commander talks to the brain.

**Interaction Model:**
- Slash commands for structured operations
- Free-form text for open-ended queries
- Cortex responds in-thread for context preservation

**Example Interactions:**
```
Commander: /cortex ask what's our best performing content this week?
Cortex: Analyzing... 
  Top 3 by engagement:
  1. "IFTA calculator saved me 4 hours this quarter" — r/Truckers — 340↑ 87💬
  2. "Owner ops: what's your biggest time-waster?" — r/owneroperators — 280↑ 112💬
  3. "Free tool for load tracking (not a broker)" — r/logistics — 195↑ 43💬
  Pattern: Pain-point hooks outperform feature-list hooks 3:1 this week.

Commander: What would you post to r/Truckers right now?
Cortex: (without deploying — dry-run mode)
  Title: "Month-end IFTA: I built a spreadsheet that auto-calculates everything. Sharing it."
  Angle: Value-first, spreadsheet giveaway to build trust
  Rationale: IFTA complaints trending (velocity: 87/100). Spreadsheet angle worked in deployment #47.
  Autonomy: Would recommend L2 — Commander review before posting giveaway content.
```

#### #⚙️ system-health
**Purpose:** Machine-level status. Infra, costs, errors.

**Auto-Posted (every 15 minutes if anomaly, every 6 hours normally):**
```yaml
Embed:
  Color: GREEN (all clear), YELLOW (warning), RED (degraded)
  Fields:
    - Cortex: status, last signal processed, queue depth
    - Reddit Ganglion: status, active deployments, API health
    - Discord Ganglion: status, active infiltrations, bot health
    - Accounts: per-platform counts, bans in last 24h
    - LLM: provider, latency p95, error rate
    - DB: connections, query latency p95
    - Proxy: available IPs, failure rate
    - Cost: today, MTD, projected monthly
```

---

## 3. COMMAND REFERENCE

### 3.1 Status & Intel Commands

| Command | Description | Output |
|---------|-------------|--------|
| `/status` | Full system dashboard | Multi-embed: clients, ganglia, accounts, recent deployments |
| `/status reddit` | Reddit ganglion status | Accounts, active deployments, health, recent bans |
| `/status discord` | Discord ganglion status | Infiltrations, community servers, trust scores |
| `/status client [name]` | Client-specific status | Profile, campaigns, metrics, account allocation |
| `/status accounts` | Account pool overview | Per-platform: active/cooldown/burned/maturing counts |
| `/memory search [query]` | Search campaign memory | Top 10 results with metrics, dates, links |
| `/memory search client:[id] [query]` | Client-scoped memory search | Top 10 results filtered to client |
| `/memory search platform:[name] [query]` | Platform-scoped memory search | Top 10 results filtered to platform |

### 3.2 Approval & Control Commands

| Command | Description | Confirmation |
|---------|-------------|-------------|
| `/approve [dispatch_id]` | Approve queued content | Immediate |
| `/reject [dispatch_id] [reason?]` | Reject with optional feedback | Immediate |
| `/edit [dispatch_id] [new_content]` | Edit content before approve | Immediate; re-queues for self-review |
| `/kill [dispatch_id]` | Kill deployed content + optional account burn | "This will delete the post. Burn account? [Yes] [No]" |
| `/kill all` | Emergency stop — freeze everything | ⚠️ "CONFIRM: Freeze all Echo Chamber operations?" [I'M SURE] [Cancel] |
| `/kill reddit` | Freeze Reddit ganglion only | "Confirm freeze Reddit ganglion?" [Yes] [No] |
| `/kill discord` | Freeze Discord ganglion only | "Confirm freeze Discord ganglion?" [Yes] [No] |
| `/pause all` | Pause all new deployments (monitoring continues) | Immediate |
| `/pause reddit` | Pause Reddit ganglion only | Immediate |
| `/resume all` | Resume all ganglia | Immediate |
| `/boost [campaign_id]` | Escalate campaign to L3, increase frequency | "Confirm boost {campaign}?" [Yes] [No] |

### 3.3 Client Operations Commands

| Command | Description | Output |
|---------|-------------|--------|
| `/onboard [url]` | Start client onboarding | Onboarding status updates in `#client-{name}` |
| `/client [name] status` | Client operational status | Full profile + metrics |
| `/client [name] report` | Generate performance report | Posted to client channel |
| `/client [name] pause` | Pause all ops for client | Confirmation + status update |
| `/client [name] resume` | Resume ops for client | Confirmation + status update |
| `/client [name] offboard` | Graceful offboarding | Checklist + confirmation |

### 3.4 Direct Cortex Commands

| Command | Description | Notes |
|---------|-------------|-------|
| `/cortex ask [question]` | RAG query over playbook + memory | Cortex responds with cited sources |
| `/cortex why [dispatch_id]` | Ask Cortex to explain a decision | Full decision trail |
| `/cortex dry-run [platform] [subreddit/server]` | Generate what-if content without deploying | Preview only, not stored |
| `/cortex predict [content_idea]` | Ask Cortex to predict performance | Based on memory patterns |

---

## 4. BOT IMPLEMENTATION

### 4.1 Technology
- **Framework:** discord.py (Python)
- **Commands:** Hybrid (`discord.app_commands` for slash commands, `discord.ext.commands` for prefix fallback)
- **State:** Stateless — all state in Cortex/DB. Bot translates Discord interactions ↔ Cortex API calls.

### 4.2 Architecture
```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  Discord API    │────▶│  Commander Bot   │────▶│  Cortex Service │
│  (WebSocket)    │◀────│  (discord.py)    │◀────│  (FastAPI)      │
└─────────────────┘     └──────────────────┘     └─────────────────┘
                                  │
                                  ▼
                         ┌──────────────────┐
                         │  PostgreSQL      │
                         │  (command log)   │
                         └──────────────────┘
```

### 4.3 Key Implementation Notes

**Button Handlers:**
```python
class ApprovalView(discord.ui.View):
    def __init__(self, dispatch_id: str, timeout_minutes: int = 240):
        super().__init__(timeout=timeout_minutes * 60)
        self.dispatch_id = dispatch_id

    @discord.ui.button(label="✅ Approve", style=discord.ButtonStyle.green)
    async def approve(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Disable all buttons
        for child in self.children:
            child.disabled = True
        # Call Cortex API
        result = await cortex_api.approve_dispatch(self.dispatch_id, interaction.user.name)
        # Update embed
        embed = interaction.message.embeds[0]
        embed.color = discord.Color.green()
        embed.set_footer(text=f"Approved by {interaction.user.name}")
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="❌ Reject", style=discord.ButtonStyle.red)
    async def reject(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Show reason modal
        modal = RejectionModal(self.dispatch_id)
        await interaction.response.send_modal(modal)

    @discord.ui.button(label="✏️ Edit", style=discord.ButtonStyle.blurple)
    async def edit(self, interaction: discord.Interaction, button: discord.ui.Button):
        modal = EditModal(self.dispatch_id)
        await interaction.response.send_modal(modal)
```

**Command Audit Logging:**
Every Commander command is logged:
```sql
CREATE TABLE commander_audit_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    commander_id VARCHAR(64) NOT NULL,
    commander_name VARCHAR(128) NOT NULL,
    command VARCHAR(64) NOT NULL,
    args JSONB,
    result JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### 4.4 Error Handling

| Scenario | Bot Behavior |
|----------|-------------|
| Cortex API unreachable | "⚠️ Cortex is not responding. Retrying..." (3 retries with backoff). Then: "🔴 Cortex is down. Check #⚙️ system-health." |
| Command rate limited | Queue command. "⏳ Processing... (Discord rate limit, your command will execute shortly)" |
| Invalid dispatch_id | "❌ Dispatch {id} not found. It may have already been processed or expired." |
| Unauthorized user | Silent ignore + log attempt. No response to non-Commander users. |
| Button timeout | Auto-disable buttons. Edit embed: "⏰ This approval request has expired." |

---

## 5. NOTIFICATION RULES

### 5.1 Push vs. Pull

| Information | Channel | Push/Pull | Frequency |
|-------------|---------|-----------|-----------|
| New signals | #📡 signals-feed | Push | Real-time |
| Content approvals needed | #✅ approval-queue | Push | On generation |
| Escalations | #🚨 escalation | Push | Immediate |
| Campaign status | #🎯 active-campaigns | Push | Hourly updates |
| Daily summary | #📊 daily-sitrep | Push | Once daily |
| System health | #⚙️ system-health | Push | Every 6h (15min if anomaly) |
| Commander queries | #🗣️ commander-chat | Pull | On demand |

### 5.2 Notification Priority
| Priority | @mention | Sound | Mobile Push |
|----------|----------|-------|-------------|
| Escalation CRITICAL | @Commander | Yes | Yes |
| Escalation HIGH | @Commander | Yes | Yes |
| Content approval (priority 4-5) | None | No | Yes |
| Content approval (priority 1-3) | None | No | No |
| Daily sitrep | None | No | No |

---

## 6. CONFIGURATION

### 6.1 Commander-Configurable Settings

```yaml
commander_config:
  approval:
    default_timeout_minutes: 240
    per_client_overrides: {}     # {client_id: timeout_minutes}
    
  autonomy:
    default_reddit_level: 2      # L2 = queue for approval
    default_discord_level: 1     # L1 = suggest (more conservative)
    per_client_overrides: {}
    
  kill_window:
    l3_kill_window_minutes: 30   # Commander can /kill L3 posts within this window
    
  sitrep:
    daily_sitrep_time_utc: 23    # Hour of day (0-23)
    
  notifications:
    push_escalations: true
    push_approvals_high_priority: true
    push_approvals_normal: false
    
  cortex:
    dry_run_enabled: true
    memory_search_limit: 10
```

### 6.2 Environment Variables
```bash
# Discord Bot
DISCORD_BOT_TOKEN=xxx
DISCORD_COMMAND_GUILD_ID=xxx
DISCORD_COMMANDER_ROLE_ID=xxx
DISCORD_OBSERVER_ROLE_ID=xxx

# Channel IDs
CHANNEL_SIGNALS_FEED=xxx
CHANNEL_ACTIVE_CAMPAIGNS=xxx
CHANNEL_APPROVAL_QUEUE=xxx
CHANNEL_ESCALATION=xxx
CHANNEL_DAILY_SITREP=xxx
CHANNEL_COMMANDER_CHAT=xxx
CHANNEL_SYSTEM_HEALTH=xxx

# Cortex API
CORTEX_API_URL=http://cortex-service:8000
CORTEX_API_KEY=xxx
```

---

*This specification defines the complete Commander interface. The Discord bot is the face of the brain. Every interaction must feel fast, clear, and in control.*
