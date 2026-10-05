# Evidence E-18: Sliding Window Rate Limiting and IP Spoofing Defense

- **ID**: `E-18`
- **Gap Closed**: `G-18` (Global Rate Limiter Middleware & Anti-Spoofing Architecture)
- **Date/Time (UTC)**: `2026-10-05T04:01:12Z`
- **Git Commit**: `dc568fc222eb9ba3221c3280fdbc64f6fec87390`
- **Command**: `.venv\Scripts\pytest.exe backend/tests/test_phase3_security_hardening.py -k "rate_limiter" -v`
- **Status**: **VERIFIED PASSED**

## Verbatim Output

```text
============================= test session starts =============================
platform win32 -- Python 3.11.15, pytest-9.1.1, pluggy-1.6.0 -- E:\per_char\.venv\Scripts\python.exe
cachedir: .pytest_cache
rootdir: E:\per_char
configfile: pytest.ini
plugins: anyio-4.15.1, asyncio-1.4.0, base-url-2.1.0, playwright-0.9.0
asyncio: mode=Mode.AUTO, debug=False, asyncio_default_fixture_loop_scope=None, asyncio_default_test_loop_scope=function
collecting ... collected 9 items / 8 deselected / 1 selected

backend/tests/test_phase3_security_hardening.py::test_rate_limiter_sliding_window_and_spoof_defense PASSED [100%]

======================= 1 passed, 8 deselected in 0.02s =======================
```

## Security & Verification Analysis

1. **Sliding Window Burst Control**:
   - `SlidingWindowRateLimiter` enforces granular rate limits (120 req/min general API, 15 req/min login, 10 req/min signup).
   - Once threshold is breached within the 60-second rolling sliding window, requests are throttled with HTTP 429 Too Many Requests.
2. **Spoofed X-Forwarded-For Defense**:
   - The test verified that incoming `X-Forwarded-For` headers are strictly ignored unless the application is explicitly declared behind a trusted reverse proxy (`behind_trusted_proxy=True`).
   - When `behind_trusted_proxy=False`, the socket IP (`request.client.host`) is used, preventing attackers from bypassing IP throttling by spoofing random header values.
