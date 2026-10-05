# Kalyan AI Personality Venture — Production Deployment Runbook

**Version**: 2.0-Production-Ready  
**Date**: October 5, 2026  
**Audience**: DevOps Engineers, Site Reliability Engineers, Platform Architects

---

## 1. System Architecture & Prerequisites

### Infrastructure Requirements
- **Host**: Linux (Ubuntu 22.04 LTS / 24.04 LTS recommended) or Windows Server 2022
- **Compute**: Minimum 2 vCPU, 4 GB RAM (4 vCPU, 8 GB RAM recommended for >500 concurrent sessions)
- **Storage**: 20 GB SSD (NVMe preferred for SQLite write throughput)
- **Runtimes**:
  - Python 3.11+
  - Node.js v20+ / v24+
  - Optional: PostgreSQL 16+ (for horizontal scaling beyond single-host SQLite)

---

## 2. Environment Variables & Secrets Management

Create `/etc/kalyan/production.env` (or `.env` in the project root with `chmod 600`):

```bash
# Core Application Settings
ENVIRONMENT=production
PROJECT_NAME="Kalyan AI Personality"
DEBUG=False
SECRET_KEY="REPLACE_WITH_64_CHAR_HEX_SECRET_KEY"
ALGORITHM="HS256"
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# Database Configuration
# For SQLite (default single-host):
DATABASE_URL="sqlite:///./kalyan_personality.db"
# For PostgreSQL (horizontal cluster):
# DATABASE_URL="postgresql://kalyan_user:REPLACE_WITH_DB_PASSWORD@db.internal:5432/kalyan_db"

# LLM Model Provider Keys
MODEL_PROVIDER="live_gemini"  # Options: live_gemini | live_openai | live_anthropic | mock
GEMINI_API_KEY="REPLACE_WITH_GEMINI_API_KEY"
OPENAI_API_KEY="REPLACE_WITH_OPENAI_API_KEY"
ANTHROPIC_API_KEY="REPLACE_WITH_ANTHROPIC_API_KEY"

# Cost Model Accounting (USD per 1,000 tokens)
COST_PER_1K_INPUT_TOKENS_USD=0.00015
COST_PER_1K_OUTPUT_TOKENS_USD=0.00060

# Payment Gateway (Razorpay / Stripe)
RAZORPAY_KEY_ID="rzp_live_REPLACE_WITH_KEY_ID"
RAZORPAY_KEY_SECRET="REPLACE_WITH_RAZORPAY_LIVE_SECRET"
RAZORPAY_WEBHOOK_SECRET="REPLACE_WITH_RAZORPAY_WEBHOOK_SECRET"

# Social Platform API Credentials (when transitioning to live broadcast)
X_API_KEY="REPLACE_WITH_X_API_KEY"
X_API_SECRET="REPLACE_WITH_X_API_SECRET"
X_ACCESS_TOKEN="REPLACE_WITH_X_ACCESS_TOKEN"
X_ACCESS_SECRET="REPLACE_WITH_X_ACCESS_SECRET"
INSTAGRAM_ACCESS_TOKEN="REPLACE_WITH_INSTAGRAM_ACCESS_TOKEN"
YOUTUBE_API_KEY="REPLACE_WITH_YOUTUBE_API_KEY"
```

---

## 3. Step-by-Step Installation & Build

### Step 1: Clone Repository & Virtual Environment
```bash
git clone https://github.com/organization/kalyan-ai-personality.git /app/kalyan
cd /app/kalyan

python3.11 -m venv .venv
source .venv/bin/activate  # Or on Windows: .venv\Scripts\Activate.ps1
pip install --upgrade pip
pip install -r requirements.txt
```

### Step 2: Build Production Frontend
```bash
cd frontend
npm install
npm run build
cd ..
```
*Note: Vite compiles the SPA to `frontend/dist`. FastAPI automatically serves these static files and maps index routes.*

### Step 3: Initialize Database Schema via Alembic Migrations
```bash
# Run versioned database migrations to head (zero create_all in non-test runtime)
alembic upgrade head

# Optional: Seed default canonical character lore & demo profiles
python -c "from backend.app.core.database import SessionLocal; from backend.app.services.persona_engine import PersonaEngine; db = SessionLocal(); PersonaEngine(db).get_or_create_default_character(); db.close()"
```
This automatically establishes all 24 database tables through versioned migrations and bootstraps Kalyan's canonical lore.

---

## 4. Process Supervision (systemd Services)

### Service 1: FastAPI Web Application (`/etc/systemd/system/kalyan-web.service`)
```ini
[Unit]
Description=Kalyan AI Personality Web Application
After=network.target

[Service]
Type=simple
User=kalyan
WorkingDirectory=/app/kalyan
EnvironmentFile=/etc/kalyan/production.env
ExecStart=/app/kalyan/.venv/bin/uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --workers 4 --proxy-headers
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

### Service 2: Content Scheduler & Autonomous Worker (`/etc/systemd/system/kalyan-scheduler.service`)
```ini
[Unit]
Description=Kalyan Autonomous Content Scheduler & Publisher Worker
After=kalyan-web.service

[Service]
Type=simple
User=kalyan
WorkingDirectory=/app/kalyan
EnvironmentFile=/etc/kalyan/production.env
ExecStart=/app/kalyan/.venv/bin/python -m backend.app.services.scheduler
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### Enable & Start Services
```bash
sudo systemctl daemon-reload
sudo systemctl enable --now kalyan-web
sudo systemctl enable --now kalyan-scheduler
```

---

## 5. Reverse Proxy Configuration (Nginx)

```nginx
server {
    listen 80;
    server_name kalyan.ai www.kalyan.ai;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl http2;
    server_name kalyan.ai www.kalyan.ai;

    ssl_certificate /etc/letsencrypt/live/kalyan.ai/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/kalyan.ai/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    client_max_body_size 10M;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_buffering off;
        proxy_read_timeout 60s;
    }
}
```

---

## 6. Operational Procedures & Disaster Recovery

### Emergency Kill Switch Execution
If an anomalous behavior or safety breach is detected:
1. **Via API**:
   ```bash
   curl -X POST https://kalyan.ai/api/v1/admin/kill-switch/activate \
     -H "Authorization: Bearer <ADMIN_JWT_TOKEN>" \
     -H "Content-Type: application/json" \
     -d '{"reason": "Emergency halt: viral hallucination detected"}'
   ```
2. **Immediate Effect**:
   - `KillSwitchManager.is_kill_switch_active()` returns `True`.
   - The Content Scheduler immediately ceases all publishing dispatches.
   - All outgoing social dispatches are blocked.
   - Audit log records operator ID, timestamp, and IP address.

### Daily Backup Routine
```bash
# Automated SQLite Hot Backup via cron (runs at 02:00 UTC daily)
sqlite3 /app/kalyan/kalyan_personality.db ".backup '/backups/kalyan_$(date +\%F).db'"
find /backups/ -name "kalyan_*.db" -mtime +14 -exec rm {} \;
```

### Health Check Verification
```bash
curl -f http://localhost:8000/api/v1/admin/kill-switch/status || exit 1
```
