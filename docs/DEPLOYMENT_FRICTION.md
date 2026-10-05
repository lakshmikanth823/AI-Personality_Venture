# FRESH-EYES DEPLOYMENT FRICTION LOG (PHASE 4 SECTION 1.5)

**Drill Execution Timestamp**: 2026-10-05T05:03:00Z  
**Target Environment**: Fresh clean directory (`$env:TEMP\kalyan_fresheyes`)  
**Source Commit**: `1d5ccfb`  
**Execution Time**:
- Git clone: 0.64 seconds
- Alembic database migration (empty state to head): 2.15 seconds
- Pytest suite verification: 61.91 seconds

---

## 1. Friction Log & Remediation Ledger

| ID | Phase / Step | Issue Encountered | Root Cause | Remediation Applied |
|---|---|---|---|---|
| **F-01** | Database Migration | `OperationalError: no such table: main.messages` on `alembic upgrade head` in fresh clone. | Baseline migration `364a0d60c198` had `pass` in `upgrade()`, assuming tables were pre-created by `init_db()`. Subsequent migrations failed when run on blank database. | Updated `364a0d60c198` to run `Base.metadata.create_all(bind=bind)`. Added `sa.inspect(bind)` checks to `a1c31c7dd9aa`, `20ae84738be2`, `7c128490e11a`, and `8d239501f22b` for true idempotent forward migration. |
| **F-02** | Documentation | `docs/DEPLOYMENT.md` Step 3 instructed developers to run `python -c "init_db()"`. | Legacy instructions bypassed versioned migration tracker, leading to schema drift between development and staging. | Updated `docs/DEPLOYMENT.md` to strictly mandate `alembic upgrade head` for zero `create_all` runtime violation in non-test paths. |
| **F-03** | Python Pathing | `ModuleNotFoundError: No module named 'backend'` when running standalone utility scripts in fresh clone. | Python does not automatically add CWD to `sys.path` when running scripts outside installed packages. | Added `$env:PYTHONPATH="."` requirement to runbook instructions and automated test scripts. |
| **F-04** | Static Assets | Frontend dist bundle missing on fresh clone if `.gitignore` ignores `frontend/dist`. | Vite build is required before FastAPI can mount the static frontend directory. | Added verification in `main.py` lifespan and runbook: if `frontend/dist` is missing, serve structured API-only JSON with build instruction banner. |

---

## 2. Sha256 Checksums of Key Artifacts in Fresh Clone

```text
7b3f94e9f7823e20601f01c89078f451f22e85a069df912c75a40a5e840d04c0  alembic.ini
981d3bc58b29ff072a0f8bf3a0784be1a70ccb5bc8b981f4a9bf95d033ef80ba  backend/app/main.py
e792da0d859ec111fbc9c09930960d70b776269b59b583f71df89da0151804fa  backend/app/core/config.py
b2e316d82e1858a221f7c32b5cfcf3216d2f3277b94ce5bb21556637e6f88d4c  docs/INCIDENT_RUNBOOK_P0.md
```

---

## 3. Fresh Clone Status: VERIFIED
The clean-clone deployment now executes with zero manual workarounds from empty disk to fully migrated schema via `alembic upgrade head`.
