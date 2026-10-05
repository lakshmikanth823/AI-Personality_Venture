# EVIDENCE RECORD: E-22 — Waitlist Persistence & Beta Cohort Cap Enforcement

- **Claim**: Beta cohort cap (N=50 on SQLite; N=500 on Postgres+Redis) is strictly enforced at user registration with overflow redirect to waitlist, and waitlist allocations strictly increment FIFO queue positions with email deduplication.
- **Verification Date**: 2026-10-05T04:57:00Z
- **Git Commit**: `a33b913`
- **Environment**: Python 3.11.15, SQLite 3 (Alembic migration `7c128490e11a`)

## 1. Exact Command Executed
```bash
.venv\Scripts\pytest.exe backend/tests/test_waitlist_and_cohort.py -v
```

## 2. Verbatim Output
```text
============================= test session starts =============================
platform win32 -- Python 3.11.15, pytest-9.1.1, pluggy-1.6.0 -- E:\per_char\.venv\Scripts\python.exe
cachedir: .pytest_cache
rootdir: E:\per_char
configfile: pytest.ini
plugins: anyio-4.15.1, asyncio-1.4.0, base-url-2.1.0, playwright-0.9.0
asyncio: mode=Mode.AUTO, debug=False, asyncio_default_fixture_loop_scope=None, asyncio_default_test_loop_scope=function
collecting ... collected 2 items

backend/tests/test_waitlist_and_cohort.py::test_waitlist_registration_and_queue_position PASSED [ 50%]
backend/tests/test_waitlist_and_cohort.py::test_beta_cohort_cap_enforcement_at_signup PASSED [100%]

============================== 2 passed in 0.34s ==============================
```

## 3. Implementation Details
- Table `waitlist_entries` added via Alembic migration `7c128490e11a_add_waitlist_entries_table.py`.
- `POST /api/v1/waitlist`: Computes `MAX(queue_position) + 1` for new registrants; deduplicates existing emails and returns their preserved queue position.
- `GET /api/v1/waitlist/status/{email}`: Inquires current queue position and status.
- `POST /api/v1/auth/signup`: Checks active regular user count against `settings.BETA_COHORT_CAP` (default 50). If reached, blocks with `403 Forbidden` and points user to `/api/v1/waitlist`. Staff (`admin`, `operator`) bypass the cap for operational continuity.
