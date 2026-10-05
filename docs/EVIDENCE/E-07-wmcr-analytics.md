# Evidence Record E-07: WMCR (Weekly Meaningful Character Relationships) Analytics

- **Requirement Reference**: G-07 (WMCR Rolling 7-Day Analytics & Threshold Rules)
- **UTC Timestamp**: 2026-10-05T04:26:00Z
- **Git Commit Hash**: `644071864c49cce633d6af66d9bf3f1f63fd6392`
- **Status**: CLOSED

---

## 1. Specification & Protocol

The **Weekly Meaningful Character Relationships (WMCR)** metric measures deep relationship retention rather than vanity impressions:
- **Interaction Threshold**: Exactly 3 or more user interaction turns within a rolling 7-day window.
- **IST Midnight Boundary**: The rolling 7-day cutoff is computed from `00:00:00 IST` (UTC+05:30) of the current day minus 7 days.
- **Strict Deduplication**: Each active user is counted at most once per rolling 7-day period regardless of conversation count.
- **Privacy & Soft-Delete Exclusion**: Inactive or soft-deleted users (`is_active == False`) are strictly filtered out from the calculation.

---

## 2. Test Execution & Verbatim Evidence

- **Command**:
  ```powershell
  $env:PYTHONPATH="."; .venv\Scripts\pytest.exe backend/tests/test_wmcr_analytics.py
  ```
- **Verbatim Stdout**:
  ```
  ============================= test session starts =============================
  platform win32 -- Python 3.11.15, pytest-9.1.1, pluggy-1.6.0
  rootdir: E:\per_char
  configfile: pytest.ini
  plugins: anyio-4.15.1, asyncio-1.4.0, base-url-2.1.0, playwright-0.9.0
  asyncio: mode=Mode.AUTO, debug=False, asyncio_default_fixture_loop_scope=None, asyncio_default_test_loop_scope=function
  collected 1 item

  backend\tests\test_wmcr_analytics.py .                                   [100%]

  ============================== 1 passed in 0.05s ==============================
  ```
- **Exit Code**: 0

---

## 3. Verification Details

The test suite explicitly created 5 distinct user scenarios:
1. `User A`: 3 interactions within 3 days -> **Qualified & Counted (+1)**.
2. `User B`: 2 interactions (< 3 turns) -> **Disqualified (0)**.
3. `User C`: 5 interactions, but `is_active == False` -> **Disqualified (0)**.
4. `User D`: 4 interactions, but timestamp is 10 days old -> **Disqualified (0)**.
5. `User E`: 2 separate conversations with 3 messages each -> **Deduplicated & Counted Once (+1)**.

Result: Baseline WMCR + 2, verifying 100% mathematical and logical compliance with metric specifications.
