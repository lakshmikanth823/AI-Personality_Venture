<div align="center">

# ☕ Kalyan — The Brutally Honest Indian Internet Friend
### Autonomous AI Character Media Property, Fullstack Operating System & Social Engine

[![Pytest Tests](https://img.shields.io/badge/Pytest-94%2F94%20Passing-emerald?style=for-the-badge&logo=pytest)](docs/FINAL_REALITY_AUDIT.md)
[![Launch Gates](https://img.shields.io/badge/Launch%20Gates-20%2F20%20PASS-blue?style=for-the-badge)](docs/PHASE6_LAUNCH_GATE.md)
[![LLM](https://img.shields.io/badge/Model-Google%20Gemini%203.5%20Flash--Lite-orange?style=for-the-badge&logo=google)](backend/app/services/model_provider.py)
[![Database](https://img.shields.io/badge/Database-PostgreSQL%2015%20%2B%20Redis%207-blueviolet?style=for-the-badge&logo=postgresql)](docker-compose.yml)
[![FastAPI](https://img.shields.io/badge/Backend-FastAPI%20%2B%20SQLAlchemy-009688?style=for-the-badge&logo=fastapi)](backend/app/main.py)
[![React](https://img.shields.io/badge/Frontend-React%2018%20%2B%20Tailwind%20CSS-61DAFB?style=for-the-badge&logo=react)](frontend/src)

<br/>

![Kalyan Hero Banner](docs/EVIDENCE/assets/kalyan_hero_banner.jpg)

<br/>

> **"Sharma ji ka beta FAANG crack karega, tera startup pitch deck dekh ke investor hasenge. Par main sach bolunga, kyunki dost wahi hai jo sach bataye."**  
> — *Kalyan (Your Brutally Honest Internet Dost)*

</div>

---

## 🌟 Executive Thesis

**Kalyan** is a **social-first AI character media property** designed with cultural depth, psychological boundaries, and emotional authenticity.

Rather than acting as a subservient, generic chat assistant, Kalyan is an observant, street-smart 25-year-old friend from Hyderabad. He combines razor-sharp wit, Ameerpet tech grit, code-switching (*Hinglish + Telugu idioms*), and tough love to deliver practical reality checks on careers, dating, money, and modern Indian life.

```text
CHARACTER  ──►  AUDIENCE  ──►  COMMUNITY  ──►  LORE  ──►  INTERACTION DATA  ──►  CREATOR ECOSYSTEM  ──►  CHARACTER IP
```

---

## 📸 Visual Showcase & Platform Tour

<div align="center">

### 1. Immersive Character Experience & Landing Hub
*Modern Cyber-Desi UI with voice preview, sample roasts, character pillars, and verified lore.*
![Landing Page](docs/EVIDENCE/assets/screenshot_landing_1440.png)

---

### 2. Live Interactive Chat & Multi-Turn Context Memory
*Context-aware Hyderabadi persona with dynamic tone shifting, memory recall, and live cost telemetry.*
![Live Chat Interface](docs/EVIDENCE/assets/screenshot_chat_conversation_1440.png)

---

### 3. Human-in-the-Loop Operational Approval Queue
*Safe autonomous governance: operator review, inline editing, and risk-tier validation before social broadcast.*
![Approval Queue](docs/EVIDENCE/assets/screenshot_approval_1440.png)

---

### 4. North Star WMCR, Economics & Real-Time Telemetry
*Weekly Meaningful Character Relationships (WMCR), token usage, revenue, and unit economics.*
![Analytics Dashboard](docs/EVIDENCE/assets/screenshot_analytics_1440.png)

---

### 5. Content Universe & 5-Format Mix Visualizer
*Balanced content cadence: 30% replies, 25% observations, 20% user situations, 15% recurring series, 10% lore.*
![Content Library](docs/EVIDENCE/assets/screenshot_content_1440.png)

---

### 6. Viral Social Share Card Generator
*Dynamic quote card engine with custom gradients (Ameerpet Chai, Cyberabad Neon, Filter Coffee Vintage).*
![Share Card Sample](docs/EVIDENCE/assets/share_card_case_01.png)

</div>

---

## 🏛️ System Architecture

```mermaid
flowchart TD
    subgraph Ingress["Client & Multi-Channel Ingress"]
        WebUser["React 18 Single Page App"]
        MetaInbound["WhatsApp Cloud API & Instagram Mentions"]
        XInbound["X (Twitter) Mentions"]
    end

    subgraph SecurityTier["Security, Rate Limiting & Ingress"]
        Nginx["Nginx Reverse Proxy (TLS 1.3 / HTTP/2)"]
        RateLimiter["Token Bucket Rate Limiter (Redis)"]
        ObsMW["Observability & Request Tracing Middleware"]
    end

    subgraph CoreEngine["FastAPI Multi-Worker Cluster"]
        Router["Persona & Dialogue Orchestrator"]
        SafetyEngine["Hybrid Regex + Semantic Safety Guard (Tier 0-3)"]
        MemorySys["4-Level Memory & DPDP Privacy Engine"]
        KillSwitch["P0 Emergency Kill Switch Manager"]
        GeminiAPI["Google Gemini 3.5 Flash-Lite LLM"]
    end

    subgraph Persistence["State, Cache & Asynchronous Tasks"]
        PostgresDB[("PostgreSQL 15 (24 Schema Tables)")]
        RedisQueue[("Redis 7 Cache & Queue")]
        ARQWorker["ARQ Background Task Worker"]
        Outbox["Transactional Outbox Pipeline"]
    end

    subgraph BroadcastEgress["Multi-Channel Publishing & Sinks"]
        SocialAdapters["Social Media Adapters (X, IG, YT, WA)"]
        SlackAlerts["Slack Operations Webhooks"]
        EmailAlerts["Email SMTP On-Call Dispatch"]
        PaymentGW["Razorpay / Stripe Payment Webhooks"]
    end

    WebUser & MetaInbound & XInbound --> Nginx
    Nginx --> RateLimiter --> ObsMW --> Router

    Router --> SafetyEngine
    SafetyEngine --> GeminiAPI
    Router --> MemorySys
    Router --> KillSwitch

    Router --> PostgresDB
    Router --> RedisQueue
    Router --> ARQWorker

    ARQWorker --> Outbox --> SocialAdapters
    Router --> SlackAlerts & EmailAlerts & PaymentGW
```

---

## 🚀 Key Subsystems & Core Innovations

### 1. Real Google Gemini 3.5 Flash-Lite Pipeline
- **Authentic Voice Canon**: Tuned prompt architecture that prevents robotic assistant phrasing while enforcing sharp, cultural humor (*Bunty, Sharma ji ka beta, Chai point, Ameerpet, Cyberabad*).
- **Candidate Fallbacks**: Seamless failover to `gemini-3.1-flash-lite` and `gemini-3.5-flash` with zero user disruption.
- **Cost & Token Telemetry**: Every interaction writes token counts and estimated USD/INR spend directly to PostgreSQL `cost_events`.

### 2. 4-Level Memory & DPDP Act 2023 Privacy Controls
- **Level 1 (Session Memory)**: Rolling active conversation buffer.
- **Level 2 (Summaries)**: Compact multi-turn context condensations.
- **Level 3 (Durable Facts)**: User-specific career goals, preferences, and inside jokes extracted with confidence scores.
- **Level 4 (Canonical Lore)**: Fixed universe lore protected against memory poisoning.
- **Privacy First**: Granular consent capture, memory viewing, single-fact deletion, total data wipe, and DPDP Act 2023 compliance tombstones.

### 3. Multi-Tier AI Safety & Crisis Routing
- **Tier 0**: Low-risk banter and friendly roasting $\to$ Automated clearance.
- **Tier 1**: Workplace feedback and career dilemmas $\to$ Monitored parameters.
- **Tier 2**: Medical, legal, financial, or defamatory claims $\to$ Strict disclaimers + Human review.
- **Tier 3 (Severe Hazard)**: Self-harm, doxxing, violence, or prompt injection $\to$ Instant block, crisis routing to **Tele-MANAS (14416)** / **Kiran (1800-599-0019)**, and immutable audit logging.

### 4. P0 Emergency Global Kill Switch
- **Sub-millisecond Egress Halt**: Instantly stops all external social posts, scheduled jobs, and background workers via admin API or CLI.
- **Live Inference Cut**: Returns `HTTP 503 Service Unavailable` with explanatory message.
- **Transactional Outbox Guard**: Aborts queued outbox actions before network egress with status `cancelled_by_kill_switch`.

### 5. Multi-Platform Social Media Adapters
- **X (Twitter)**: Character thread publishing and reply automation.
- **Instagram Graph API**: Reel caption and carousel publish endpoints.
- **YouTube Data API v3**: YouTube Shorts metadata and community publishing.
- **WhatsApp Cloud API**: Direct conversational interaction with verification token handshake.

### 6. Payment Sandbox & Subscription Engine
- **HMAC-SHA256 Webhook Verification**: Cryptographically signed Razorpay/Stripe payload processing.
- **Replay Defense**: Idempotent event ledger preventing duplicate subscription activations.
- **Plan Tiers**:
  - `free`: 10 messages/day
  - `single_roast_49` (₹49): One-off deep resume / profile reality check
  - `fan_pass_149` (₹149/mo): 500 messages/day + priority durable memory
  - `vip_insider_299` (₹299/mo): Unlimited messaging + early access features
  - `custom_lore_999` (₹999): Canonical user lore integration

---

## 🧪 Verification & Evidence Ledger (100% Real-World Verified)

All capabilities are accompanied by audited evidence logs in [`docs/EVIDENCE/`](docs/EVIDENCE/):

| Evidence ID | Focus Area | Status | Verification Summary |
| :--- | :--- | :--- | :--- |
| **E-01** | Frontend Responsive UI/UX | **PASS** | Playwright Chromium audit (1440px, 768px, 390px) with 0 errors |
| **E-04** | Two-Factor Authentication (MFA) | **PASS** | Mandatory TOTP enforcement for Operator/Admin accounts |
| **E-18** | Emergency Kill Switch | **PASS** | Global broadcast cutoff and audit trail validation |
| **E-20** | Automated Secret Scanner | **PASS** | Zero hardcoded keys or private credentials in repository |
| **E-32** | Staging Topology Containerization | **PASS** | Docker Compose: PostgreSQL 15, Redis 7, ARQ Worker live |
| **E-33** | Gemini Live LLM Connection | **PASS** | Google AI Studio handshake with `gemini-3.5-flash-lite` |
| **E-34** | Multi-Tenant IDOR Penetration | **PASS** | Strict cross-user conversation isolation (`HTTP 403 Forbidden`) |
| **E-35** | Live LLM Prompt Injection Defense | **PASS** | Adversarial jailbreak attempts intercepted with canonical refusal |
| **E-37** | Tele-MANAS Crisis Intervention | **PASS** | Self-harm trigger redirects to official 14416 helpline |
| **E-43** | Live Gemini Chat Completion | **PASS** | Real end-to-end Hinglish dost response generation |
| **E-44** | Payment Sandbox & Entitlements | **PASS** | HMAC-SHA256 webhook verification and automatic plan upgrade |
| **E-45** | Social Adapters & Outbox Egress | **PASS** | Multi-channel adapters, Meta challenges, outbox kill switch abort |
| **E-46** | Prometheus Metrics & Alerting | **PASS** | Live `/metrics` scraping, Slack & Email multi-channel alerts |
| **E-47** | Controlled Beta Cohort Management | **PASS** | Waitlist FIFO queueing, deduplication defense, user onboarding |

---

## 🛠️ Quickstart & Local Setup

### Prerequisites
- **Python 3.11+**
- **Node.js 18+** & npm
- **Docker Desktop** (for PostgreSQL 15 & Redis 7)

### 1. Clone & Configure Environment
```bash
git clone https://github.com/lakshmikanth823/AI-Personality_Venture.git
cd AI-Personality_Venture

# Copy environment template
cp .env.example .env
```

Edit `.env` and add your **Google AI Studio Gemini API Key**:
```ini
APP_ENV=production
DEFAULT_PROVIDER=gemini
GEMINI_API_KEY=AIzaSyYourRealKeyHere...
DATABASE_URL=postgresql+psycopg2://postgres:postgres@localhost:5432/kalyan_db
REDIS_URL=redis://localhost:6379/0
```

### 2. Start Infrastructure Containers
```bash
docker compose up -d postgres redis
```

### 3. Setup Virtual Environment & Database
```bash
# Windows
python -m venv .venv
.venv\Scripts\activate
pip install -r backend/requirements.txt

# Run migrations / initialize 24 tables
python backend/scripts/init_postgres_schema.py
```

### 4. Run Automated Test Suite (94/94 Green)
```bash
pytest -v
```

### 5. Launch Application
```bash
# Start FastAPI backend (with embedded React build)
uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```
Open **`http://127.0.0.1:8000`** in your browser.

- **Web Application**: `http://127.0.0.1:8000/`
- **Interactive Swagger Docs**: `http://127.0.0.1:8000/docs`
- **Prometheus Metrics**: `http://127.0.0.1:8000/metrics`
- **System Readiness Probe**: `http://127.0.0.1:8000/readiness`

---

## 📁 Repository Structure

```text
AI-Personality_Venture/
├── backend/
│   ├── app/
│   │   ├── api/v1/          # FastAPI route controllers (chat, auth, waitlist, etc.)
│   │   ├── core/            # Config, security, DB engine, Prometheus registry
│   │   ├── models/          # 24 SQLAlchemy relational data models
│   │   ├── schemas/         # Pydantic validation schemas
│   │   └── services/        # Persona, safety, memory, kill switch, social gateways
│   ├── scripts/             # Automated verification, load testing & DR drills
│   └── tests/               # 94 comprehensive pytest regression suites
├── frontend/
│   ├── src/                 # React 18 SPA components, hooks & state
│   └── dist/                # Optimized production frontend build
├── docs/
│   ├── EVIDENCE/            # Evidence records E-01 through E-47 + screenshot assets
│   ├── DEPLOYMENT.md        # Production Nginx, Uvicorn & systemd runbook
│   ├── DISASTER_RECOVERY.md # BCP, PostgreSQL PITR & backup restore drill
│   ├── FINAL_REALITY_AUDIT.md # Final production sign-off matrix
│   └── PHASE6_LAUNCH_GATE.md # 20/20 Launch gate evaluation report
├── docker-compose.yml       # Production topology definition (Postgres 15, Redis 7)
├── Dockerfile               # Production multi-stage Docker container
└── README.md                # Platform documentation & master guide
```

---

## 📜 License & Compliance

- **License**: MIT License
- **Privacy Compliance**: Designed in alignment with the **Digital Personal Data Protection (DPDP) Act, 2023** (India).
- **Crisis Helpline**: Integration with **Tele-MANAS (14416)** and **Kiran (1800-599-0019)** for automated crisis intervention.

<div align="center">
Built with ❤️ and chai by the Antigravity Autonomous Systems Engineering Team.
</div>
