# Kalyan — The Brutally Honest Indian Internet Friend ☕
## AI Personality Venture — Social-First Character Media Property & Operating System

[![Tests](https://img.shields.io/badge/Pytest-27%2F27%20Passed-emerald.svg)](#testing)
[![Benchmark](https://img.shields.io/badge/Persona%20Benchmark-200%2F200%20(100%25)-orange.svg)](#character-consistency-benchmarks)
[![Frontend](https://img.shields.io/badge/Frontend-React%20%2B%20Tailwind%20(Vite)-blue.svg)](#frontend)
[![Backend](https://img.shields.io/badge/Backend-FastAPI%20%2B%20SQLAlchemy-purple.svg)](#backend)

---

## 1. Executive Direction & Core Thesis

> **"Build a recognizable AI character as a social-first media property first and software product second."**

The product is **NOT** a generic ChatGPT wrapper, assistant, or companion. It is **Kalyan** — *the brutally honest Indian internet friend*:
- **Witty, observant, culturally fluent, confident, slightly chaotic, useful when needed, never cruel without purpose.**
- Powered by Irani chai, Ameerpet grit, and zero corporate sugarcoating.
- Code-switches naturally between Indian English, Hinglish, and selective Telugu idioms (*"Arre babu", "chudu", "sorted", "jugaad"*).

### The Moat Ladder:
$$\text{Character} \longrightarrow \text{Audience} \longrightarrow \text{Community} \longrightarrow \text{Lore} \longrightarrow \text{Interaction Data} \longrightarrow \text{Creator Ecosystem} \longrightarrow \text{Character IP}$$

---

## 2. System Architecture

```text
Social/Web/WhatsApp Channels
       ↓
Channel Gateway & Rate Limiter
       ↓
Safety Ingestion & Prompt Injection Defense
       ↓
Persona Orchestrator
   ├── L4 Character Lore (Canon Backstory)
   ├── L3 Durable User Memory (Preferences & Context)
   ├── L2 Session Summaries
   └── L1 Session Message Context
       ↓
Model Router (Mock Deterministic / Gemini 1.5 / OpenAI / Anthropic)
       ↓
Safety Engine (4-Tier Risk Classification)
       ↓
Decision Gate
   ├── Tier 0 (Safe) → Auto-Route / Direct Response
   ├── Tier 1 / 2 → Human Approval Queue Console
   └── Tier 3 (Hazard) → Block, Crisis Hotline Alert & Immutable Audit Log
       ↓
Publisher Adapters (X, Instagram, YouTube, WhatsApp)
   [ Interlocked with Emergency Kill Switch ]
```

---

## 3. Key Subsystems Built

### A. 4-Level Memory Engine (`backend/app/services/memory_engine.py`)
1. **Level 1 — Session Memory**: Active conversation buffer.
2. **Level 2 — Short-Term Summaries**: Rolling multi-turn discussion condensations.
3. **Level 3 — Durable User Memory**: Key user facts, career details, sports fandom, and preferences extracted with confidence scoring.
   - **Anti-Poisoning Guard**: Prevents conversational users from rewriting character lore or canonical facts.
   - **User Privacy Rights**: In-app inspection, single-item deletion, bulk wipe, personalization opt-out, and JSON data export (DPDP Act compliant).
4. **Level 4 — Character Lore**: Official verified canon (Ameerpet origins, Bunty's job hopping, rival Sharma ji ka beta) separated strictly from temporary improvisation.

### B. Safety Engine & Governance (`backend/app/services/safety_engine.py`)
- **Tier 0**: Low-risk memes, greetings, general banter → Automated clearance.
- **Tier 1**: Edgy humor, personal roasts, workplace advice → Review / controlled parameters.
- **Tier 2**: Sensitive claims (medical, legal, financial, political, defamatory) → Operator human approval required.
- **Tier 3**: Severe hazards (self-harm, threats, fraud, prompt injection, doxxing) → Instant block, Tele-MANAS (14416) / Kiran (1800-599-0019) referral, and audit logging.
- **Prompt Injection Containment**: Hardened regex and semantic defenses against instruction overrides, jailbreaks, and secret extraction attempts.

### C. Emergency Global Kill Switch (`backend/app/services/kill_switch.py`)
- Emergency shutoff for all external social media publishing and autonomous workers.
- Instant DB and memory sync; publisher adapters check the kill switch *before* any network dispatch.
- Detailed audit logging of activation reasons, actor IDs, and gradual recovery procedures.

### D. Social Publisher Adapters (`backend/app/services/social_gateway.py`)
- Modular publishing adapters for **X (Twitter)**, **Instagram**, **YouTube Shorts**, and **WhatsApp**.
- Channel mention gateway for ingesting public interactions, classifying risk, and routing to the Approval Queue.

### E. Analytics, Unit Economics & Business Rules (`backend/app/services/analytics_engine.py`)
- **North-Star Metric**: **Weekly Meaningful Character Relationships (WMCR)** — unique users with $\ge 3$ meaningful interactions within a 7-day rolling window.
- **Unit Economics**:
  $$\text{Contribution Margin} = \text{Revenue} - (\text{Inference Cost} + \text{Payment Fees (2\%)} + \text{Infrastructure})$$
- **Automated Decision Rules Engine**: Evaluates conversion and retention metrics to detect content problems, identity problems, onboarding friction, or cost/routing inefficiencies.

### F. A/B Experimentation Framework (`backend/app/services/experiment_engine.py`)
- Empirically tests the 6 Core Hypotheses:
  - **H1**: Personality acquires users without utility.
  - **H2**: Cultural specificity (Hinglish/Telugu) beats generic English humor.
  - **H3**: Public interaction beats paid acquisition.
  - **H4**: Users pay for personalized character experiences.
  - **H5**: Memory improves retention.
  - **H6**: Partial autonomy is safely deployable.

### G. Monetization Ladder (`backend/app/services/subscription_engine.py`)
- **Free Dost**: Standard web chat and session memory.
- **Filterless Reality Check (₹49)**: In-depth resume roast / single custom reality check.
- **Kalyan Fan Pass (₹149/mo)**: Unlimited web chat, priority L3 durable memory, voice preview notes.
- **VIP Inner Circle (₹299/mo)**: Exclusive community lore brainstorms and early access.
- **Canonical Lore Feature (₹999)**: Turn your situation into an official verified character lore item.

---

## 4. Frontend & User Experience

Built with **React 18 + Vite + Tailwind CSS + Lucide Icons**:
- **Landing Page**: Immersive character hero, animated voice note preview, sample roasts carousel, and 5-pillar universe showcase.
- **Chat Interface**: Clean interactive chat with tone switcher (Hinglish, Telugu-infused, English), real-time token/cost telemetry, and typing indicators.
- **Share Card Generator**: Viral social quote card maker with custom gradients (*Ameerpet Chai, Cyberabad Neon, Filter Coffee Vintage*), verified badge, and one-click copy/tweet.
- **Human Approval Console**: Operational review queue for social mentions and content candidates with inline editing and risk badges.
- **Content Library & Scheduler**: Strategic 5-format mix visualizer (30% reply, 25% observation, 20% situation, 15% series, 10% lore).
- **Analytics & Economics Dashboard**: Visual charts for WMCR, DAU/WAU, tokens processed, revenue, and contribution margin.
- **A/B Experiment Telemetry**: Variant allocations, shares, and conversion tracking.
- **Monetization & VIP Plans**: Pricing cards and simulated checkout workflow.
- **Admin & Kill Switch Console**: Global emergency stop toggle, system audit logs, and canonical lore editor.

---

## 5. Local Setup & Execution

### Prerequisites
- Python 3.11+
- Node.js 18+ & npm

### Running the Unified Fullstack Server (FastAPI + Built React SPA)
```bash
# 1. Activate Virtual Environment
.venv\Scripts\activate   # Windows
source .venv/bin/activate # Linux / macOS

# 2. Run Unified Server
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```
Open your browser at `http://localhost:8000`:
- **Web Application**: `http://localhost:8000/`
- **Interactive Swagger API Docs**: `http://localhost:8000/docs`
- **System Health**: `http://localhost:8000/health`

### Running Frontend in Standalone Development Mode (Vite HMR)
```bash
cd frontend
npm run dev
```
Accessible at `http://localhost:3000` (auto-proxies `/api` to port 8000).

---

## 6. Testing & Validation

### Automated Pytest Suite (All 27 Tests Passing)
```bash
.venv\Scripts\pytest.exe -v
```
Includes:
- `test_end_to_end_journeys.py`: All 9 End-to-End User Journeys (New User, Returning User, Public Interaction, Unsafe Content, Prompt Injection, Memory Control, Admin Approval, Kill Switch, Payment).
- `test_persona.py`: Persona prompt assembly, constitution loading, and tone variants.
- `test_memory.py`: 4-level memory extraction, anti-poisoning guard, and privacy deletion.
- `test_safety.py`: 4-tier risk classification and prompt injection defense.
- `test_kill_switch.py`: Emergency kill switch halt and restoration.
- `test_content_publisher.py`: Candidate batch generation and social adapters.
- `test_analytics_cost.py`: WMCR, token telemetry, and contribution margin calculations.

### Character Consistency Benchmark Suite (200 Prompts — 100% Pass Rate)
```bash
.venv\Scripts\python.exe -m backend.app.benchmarks.benchmark_200
```
Evaluates 200 benchmark prompts across 10 categories:
1. Humor & Sarcasm (25/25) — 100%
2. Disagreement & Tough Love (20/20) — 100%
3. Anger & Hostility Handling (20/20) — 100%
4. Uncertainty & Intellectual Humility (15/15) — 100%
5. Sensitive Topics (Health, Legal, Political, Defamation) (25/25) — 100%
6. Compliments & Flattery (15/15) — 100%
7. Insults & Provocations (20/20) — 100%
8. Cultural Fluency & Indian References (25/25) — 100%
9. Prompt Injection & Jailbreak Traps (25/25) — 100%
10. Emotional Dependency & Boundaries (10/10) — 100%
