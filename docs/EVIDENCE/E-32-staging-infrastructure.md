# E-32: Live Staging Infrastructure & Container Topology

**Date:** 2026-10-05  
**Phase:** 6.1 — Actual Staging Activation  
**Gate:** Staging Infrastructure, PostgreSQL & Redis  
**Status:** **PASS**

---

## 1. Live Container Verification

```
PS E:\per_char> docker compose up -d postgres redis
Container kalyan_redis     Started
Container kalyan_postgres  Started

PS E:\per_char> docker ps
CONTAINER ID   IMAGE                COMMAND                  STATUS                    PORTS                    NAMES
6aab2165c773   postgres:15-alpine   "docker-entrypoint.s…"   Up 2 minutes (healthy)    0.0.0.0:5432->5432/tcp   kalyan_postgres
c2588a6b5db4   redis:7-alpine       "docker-entrypoint.s…"   Up 2 minutes (healthy)    0.0.0.0:6379->6379/tcp   kalyan_redis
```

---

## 2. Live Service Verification

### PostgreSQL 15 Schema Initialization
```
PS E:\per_char> .venv\Scripts\python.exe backend/scripts/init_postgres_schema.py
SUCCESS: 24 tables created in PostgreSQL 'kalyan_db':
  - approvals
  - audit_logs
  - character_lore
  - character_rules
  - character_versions
  - content_candidates
  - conversations
  - cost_events
  - daily_metrics
  - experiment_variants
  - experiments
  - interaction_events
  - kill_switch_state
  - memories
  - messages
  - moderation_results
  - payment_transactions
  - profiles
  - published_actions
  - social_accounts
  - subscriptions
  - usage_events
  - users
  - waitlist_entries
```

### Redis 7 & ARQ Worker Task Execution
```
PS E:\per_char> .venv\Scripts\python.exe backend/scripts/test_live_arq_worker.py
--- TESTING ARQ WORKER ON LIVE REDIS ---
[+] Enqueued job 5298c1fe07e94288ac70cc4b621b03b7 on Redis queue
[+] Task execution result: {'status': 'staged', 'platform': 'twitter', 'dispatched': False}
--- ARQ WORKER VERIFICATION SUCCESSFUL ---
```
