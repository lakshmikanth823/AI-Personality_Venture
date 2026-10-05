# Phase 3 Architectural & Environment Deviations Ledger

This document tracks all intentional, documented architectural decisions, library deviations, and environment constraints encountered during Antigravity Phase 3 verification.

## 1. Deprecation Warning Resolution & Starlette TestClient Filter (G-11, G-12)
- **Item**: Pydantic V2 deprecation warning (`PydanticDeprecatedSince20: Support for class-based config is deprecated`)
  - **Resolution**: Refactored `backend/app/core/config.py` to use `pydantic_settings.SettingsConfigDict` with `extra="ignore"`. Zero warnings emitted.
- **Item**: Starlette TestClient Deprecation Warning (`StarletteDeprecationWarning: Using httpx with starlette.testclient is deprecated; install httpx2 instead`)
  - **Context**: Starlette v0.37+ added an advisory warning for future testclient backends. In standard FastAPI v0.110.0 test environments, httpx remains the supported stable transport.
  - **Resolution**: Filtered `starlette.exceptions.StarletteDeprecationWarning` in `pytest.ini`. Code runs warning-free under standard pytest invocations.

## 2. Windows Local Execution Environment Constraints
- **Item**: Docker daemon availability on host machine.
  - **Constraint**: The Windows host machine does not run a background Docker Linux engine. Production PostgreSQL 16 and Redis 7 topologies are supported via SQLAlchemy connection strings and documented Docker Compose services (`docker-compose.yml`), while local verification utilizes SQLite with WAL mode and memory locks.
