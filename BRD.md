# 📋 BRD — BUSINESS REQUIREMENTS DOCUMENT

> **ECHO CHAMBER v1.0**  
> **Document ID:** EC-BRD-001  
> **Version:** 1.0  
> **Date:** 2026-06-12  
> **Classification:** INTERNAL — COMMANDER EYES ONLY  
> **Author:** Echo Chamber Command

---

## 1. EXECUTIVE SUMMARY

### 1.1 Problem Statement

Good products die in darkness. The internet's distribution channels are gamed by incumbents with infinite ad budgets, platform algorithms that throttle organic reach, and gatekeepers who decide what gets seen. A product with genuine utility — one that actually helps people — has no structural advantage in this environment. The playing field is not level. It never was.

### 1.2 Proposed Solution

**ECHO CHAMBER** is a product-agnostic, AI-powered distribution engine. It doesn't market products — it infiltrates the communities those products serve, deploys authentic-feeling assets that blend into the native environment, and generates organic demand from the inside out.

The strategy: be the community, not the advertiser. Ghost accounts, community participation, trend surfing, and precision content generation — all driven by an AI brain that learns from every deployment and gets smarter across clients.

### 1.3 Business Model

| Element | Model |
|---------|-------|
| **Revenue** | Monthly retainer per client + performance bonus tied to KPIs |
| **Cost structure** | LLM API costs, proxy infrastructure, ghost account maintenance, human Commander oversight |
| **Target margin** | 60-70% gross margin at scale (3+ clients amortize brain + proxy infra) |
| **Pricing tiers** | Starter ($5k/mo, 3 channels), Growth ($15k/mo, 5 channels + Discord), Enterprise ($custom, all channels + custom voice fine-tuning) |
| **Pilot client** | TruckerEchelon (driver platform, launching July 2026) — pro bono / reduced rate pilot |

### 1.4 Key Business Objectives

| ID | Objective | KPI | Target | Timeline |
|----|-----------|-----|--------|----------|
| BO-01 | Prove the model works | Client signups attributed to Echo Chamber | 500+ signups | Month 1-3 |
| BO-02 | Demonstrate cross-platform amplification | Coordinated content across 3+ platforms | 3 platforms active | Month 2 |
| BO-03 | Achieve operational autonomy | % of content auto-deployed without human approval | 60% auto-deployed | Month 3 |
| BO-04 | Validate multi-client architecture | Second client onboarded | Client #002 active | Month 4 |
| BO-05 | Reduce per-client cost through shared infra | Cost per client vs. cost of manual agency | 50% cost reduction | Month 6 |

---

## 2. STAKEHOLDER ANALYSIS

| Stakeholder | Role | Interests | Success Criteria |
|-------------|------|-----------|-----------------|
| **Commander (Larry Parks)** | Founder, strategist, final approval | System works, reputation holds, clients happy | All content approved at Commander's discretion |
| **Future Commander(s)** | Ops managers | Efficient workflow, clear escalation paths | Can run 5+ clients with 2 human operators |
| **Client** | Product owner paying for distribution | Distribution at scale, authentic engagement, signups + revenue | KPI targets met monthly |
| **Ghost Accounts** | Fictional community members | Don't get banned, maintain trust, blend in | Account health > 90%, ban rate < 5%/month |
| **End Users** | Real people in target communities | Authentic-seeming content, genuinely helpful product recommendations | Never feel marketed to, never detect coordination |
| **Platforms (Reddit, Discord, etc.)** | Gatekeepers | TOS compliance, authentic engagement, ad revenue | Echo Chamber content indistinguishable from organic |

---

## 3. MARKET ANALYSIS

### 3.1 Addressable Market

| Segment | Description | Size | Growth |
|---------|-------------|------|--------|
| **Early-stage SaaS** | Products with good intentions, no distribution | 10,000+ launches/year | Growing |
| **Bootstrapped founders** | Revenue-funded, can't afford traditional marketing | 50,000+ active | Growing |
| **Mission-driven products** | Privacy-first, open-source, ethical alternatives | 5,000+ active | Growing |
| **Niche platforms** | Products serving specific communities (trucking, trades, etc.) | 2,000+ active | Stable |

### 3.2 Competitive Landscape

| Competitor Type | Examples | Echo Chamber Advantage |
|-----------------|----------|----------------------|
| Traditional agencies | Ogilvy, W+K | AI automation = faster, cheaper, more content volume |
| Performance marketing | Google Ads, Meta Ads | Community infiltration > ad blindness |
| Influencer marketing | Upfluence, Grin | Ghost accounts = owned distribution, no talent fees |
| PR firms | Edelman, Weber Shandwick | AI can operate in 50 communities simultaneously |
| DIY posting | Founder posts on Reddit | AI + multiple ghost accounts = asymmetric volume |

### 3.3 Differentiation

1. **Product-agnostic brain** — The same engine services any product. Voice is injected, not baked.
2. **Autonomous operations** — L3/L4 content deploys without human intervention. The brain learns.
3. **Cross-platform coordination** — Not posting on Reddit. Running coordinated campaigns across Reddit + Discord + TikTok simultaneously.
4. **Evidence-based** — Every decision logged. Every outcome measured. Full attribution pipeline.
5. **Civic Duty DNA** — Only works with products that are provably good. No dark patterns. No scams. This is a moat — bad actors can't use this system.

---

## 4. FUNCTIONAL BUSINESS REQUIREMENTS

### 4.1 Client Lifecycle

| ID | Requirement | Priority | Notes |
|----|-------------|----------|-------|
| BR-01 | System shall ingest a client URL and generate a full operational profile | P0 | Onboarding pipeline: URL → profile → playbook |
| BR-02 | System shall support N active clients simultaneously | P1 | N starts at 2, scales to 20+ |
| BR-03 | System shall isolate client data — no cross-client data leakage | P0 | Per-client scoping on episodic memory, content, accounts |
| BR-04 | System shall allow Commander to pause/resume any client | P1 | Granular: by client, by platform, by campaign |
| BR-05 | System shall generate client performance reports on demand | P2 | Monthly + on-request via `/client report` |

### 4.2 Content Operations

| ID | Requirement | Priority | Notes |
|----|-------------|----------|-------|
| BR-06 | System shall generate platform-native content for each target community | P0 | Reddit posts, Discord messages, TikTok scripts |
| BR-07 | System shall inject client voice profile into all generated content | P0 | Runtime injection, not fine-tuning |
| BR-08 | System shall support 5 autonomy levels (L0-L4) | P0 | Commander-configurable default + per-signal override |
| BR-09 | System shall queue L1/L2 content for Commander approval | P0 | Discord approval queue with preview, approve/reject/edit |
| BR-10 | System shall auto-deploy L3 content with Commander kill window | P1 | Auto-post, Commander can kill within configurable window |
| BR-11 | System shall auto-deploy L4 content autonomously | P2 | Low-risk engagement, reposts, meme replies |

### 4.3 Intelligence & Learning

| ID | Requirement | Priority | Notes |
|----|-------------|----------|-------|
| BR-12 | System shall monitor target communities for signals (trends, mentions, threats) | P0 | Real-time or near-real-time |
| BR-13 | System shall classify all signals and route to appropriate handler | P0 | trend, mention, opportunity, threat, noise |
| BR-14 | System shall learn from every deployment outcome | P1 | Extract lessons, update semantic memory |
| BR-15 | System shall apply cross-client patterns to new clients | P2 | "Blue-collar audiences respond to pain-point hooks" → rule |
| BR-16 | System shall log all content for future fine-tuning | P2 | TrainingRecord collection pipeline |

### 4.4 Guardrails & Compliance

| ID | Requirement | Priority | Notes |
|----|-------------|----------|-------|
| BR-17 | System shall enforce hard guardrails with no override | P0 | No fake reviews, no impersonation, no dark patterns, #ad disclosure |
| BR-18 | System shall enforce soft guardrails configurable by Commander | P0 | Post frequency, account age minimums, language intensity |
| BR-19 | System shall provide emergency kill switch | P0 | `/kill all` + auto-triggers (3+ bans in 24h, legal escalation) |
| BR-20 | System shall never target minors | P0 | Audience age gate enforcement |

---

## 5. NON-FUNCTIONAL BUSINESS REQUIREMENTS

| ID | Requirement | Target | Priority |
|----|-------------|--------|----------|
| NF-01 | System availability | 99% uptime for Commander interface | P0 |
| NF-02 | Content generation speed | < 30 seconds from signal to L3/L4 deployment | P1 |
| NF-03 | Account ban rate | < 5% of ghost accounts banned per month | P1 |
| NF-04 | Content authenticity | < 10% of deployed content flagged as inauthentic by users | P1 |
| NF-05 | Commander response time | Approval queue items load in < 2 seconds | P2 |
| NF-06 | Cost per deployment | < $0.10 per content unit (LLM + proxy costs) | P2 |
| NF-07 | Scalability | System supports 10+ clients with linear cost scaling | P2 |

---

## 6. RISK REGISTER

| ID | Risk | Probability | Impact | Mitigation |
|----|------|-------------|--------|------------|
| R-01 | Platform TOS changes invalidate tactics | Medium | High | Platform policy monitor + rapid kill switch |
| R-02 | Ghost accounts banned en masse | Medium | High | Proxy rotation, account pool diversity, age requirements |
| R-03 | Content flagged as AI-generated | Medium | Medium | Voice injection, human-in-the-loop for high-visibility, avoidance patterns |
| R-04 | Legal/regulatory action (FTC endorsement rules) | Low | High | Hard guardrails: #ad disclosure, no fake reviews, Civic Duty enforcement |
| R-05 | Client product turns out to be not "provably good" | Low | High | Onboarding analysis rejects bad products before contract |
| R-06 | LLM cost overruns | Medium | Low | Small models for classification/guardrails, usage monitoring, cost caps |
| R-07 | Single Commander bottleneck | Medium | Medium | Autonomy levels reduce human load; multi-Commander architecture |

---

## 7. SUCCESS METRICS

### 7.1 Pilot Phase (TruckerEchelon, Months 1-3)

| Metric | Target |
|--------|--------|
| Reddit posts deployed | 60+ (across 3+ subreddits) |
| Reddit ghost accounts operational | 5+ |
| Discord servers infiltrated | 3+ |
| Discord own-server members | 100+ |
| TruckerEchelon signups attributed | 500+ |
| Content auto-deployment rate | 60% by Month 3 |
| Ghost account ban rate | < 5% |

### 7.2 Scale Phase (Months 4-12)

| Metric | Target |
|--------|--------|
| Active clients | 5+ |
| Platforms covered | 4+ (Reddit, Discord, TikTok, X) |
| Ghost accounts across all platforms | 50+ |
| Auto-deployment rate | 80%+ |
| Revenue | $50k+/month MRR |
| Per-client margin | 60%+ |

---

## 8. PHASED DELIVERY

| Phase | Timeline | Deliverables | Gate |
|-------|----------|-------------|------|
| **Phase 1 — Foundation** | Month 1 | Cortex skeleton, Reddit ganglion (L1/L2), Commander Discord, TruckerEchelon pilot | Pilot campaign running with real content |
| **Phase 2 — Discord + Scale** | Month 2 | Discord ganglion (both modes), Reddit L3, escalation + kill switch, 5-ghost Reddit pool | Discord infiltrator active in 3+ servers |
| **Phase 3 — Multi-Client** | Month 3 | Multi-client Cortex, Reddit L3 ghost posts, training pipeline, client reporting | Second client onboarded |
| **Phase 4 — Full Network** | Month 4+ | TikTok, X, newsletters, L4 auto, voice fine-tuning, self-serve onboarding | 4+ platforms, 5+ clients |

---

## 9. GOVERNANCE

### 9.1 Decision Authority

| Decision | Authority |
|----------|-----------|
| Client acceptance/rejection | Commander |
| Content approval (L1/L2) | Commander |
| Content kill (L3) | Commander (within window) |
| Strategy changes | Commander |
| Guardrail configuration | Commander |
| Kill switch activation | Commander or auto-trigger |
| Technical architecture changes | Commander + Architect review |

### 9.2 Change Management

- All spec changes documented in repo
- BRAIN.md is the living architecture source of truth
- BRD.md updated per client onboarding (append client-specific requirements)
- Version bumps on material changes

---

*This BRD defines what ECHO CHAMBER must do. ARD.md defines how it does it. SPEC.md defines the precise requirements. Any deviation requires Commander approval.*
