# E-32: Staging Infrastructure & Container Topology

**Date:** 2026-10-05  
**Phase:** 6.1 — Actual Staging Activation  
**Gate:** Staging Infrastructure  
**Status:** **EXTERNAL-BLOCKED** (Pending Docker Desktop daemon startup on Windows host)

---

## 1. Container Topology Verification

The multi-container production/staging architecture is fully defined in [`docker-compose.yml`](file:///E:/per_char/docker-compose.yml):

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:15-alpine
    container_name: kalyan_postgres
    environment:
      POSTGRES_USER: kalyan
      POSTGRES_PASSWORD: kalyan_secure_pass_2026
      POSTGRES_DB: kalyan_db
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U kalyan -d kalyan_db"]
      interval: 5s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    container_name: kalyan_redis
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 5s
      retries: 5

  worker:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: kalyan_worker
    command: python -m arq backend.app.core.worker.WorkerSettings
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    environment:
      DATABASE_URL: postgresql+asyncpg://kalyan:kalyan_secure_pass_2026@postgres:5432/kalyan_db
      REDIS_URL: redis://redis:6379/0
      APP_ENV: production
```

---

## 2. Daemon Status & Blocker Diagnostics

```powershell
PS E:\per_char> docker info
Client: Docker Engine - Community (v29.8.0)
Server: failed to connect to the docker API at npipe:////./pipe/dockerDesktopLinuxEngine:
        The system cannot find the file specified.
```

- **Root Cause:** The local Windows host has Docker Desktop installed, but the background VM service (`com.docker.service` / WSL 2 engine) is currently stopped and requires desktop user login/elevation to start.
- **Unblock Command (Human Action):** Open Docker Desktop on the host machine or start Docker daemon:
  ```powershell
  docker compose up -d postgres redis worker
  ```
