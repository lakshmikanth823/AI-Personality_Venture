# Evidence Record E-13: Mock vs Live Doctrine Verification

- **Requirement Reference**: G-13 (Mock vs Live Doctrine and Fixture Contracts)
- **UTC Timestamp**: 2026-10-05T04:18:00Z
- **Git Commit Hash**: `310e73f128f18c6fbf9b1abb23b8f914b8adf0c2`
- **Status**: CLOSED

---

## 1. Specification & Protocol

The **Mock vs Live Doctrine** governs LLM provider invocation across all environments:
1. **Mock Mode (`--mode mock` / Default CI/CD)**: Deterministic evaluation using recorded provider fixtures and in-memory mock responses. All unit tests and safety benchmark assertions run against deterministic fixtures without external network dependencies.
2. **Live Mode (`--mode live`)**: Dynamically invokes live APIs (OpenAI, Gemini, Anthropic) if API keys are configured. If API keys are absent, the system intercepts execution cleanly with `[EXTERNAL-BLOCKED]` and exits code 0, preventing CI pipeline failure due to unconfigured third-party secrets.
3. **Fixture Contracts**: Recorded responses from OpenAI `gpt-4o`, Google `gemini-1.5-pro`, and Anthropic `claude-3-5-sonnet` are stored in `backend/tests/fixtures/provider_responses/` and validated against Pydantic schema contracts.

---

## 2. Test Execution & Verbatim Evidence

### Execution A: Multi-Turn Adversarial in Live Mode (Without API Keys)
- **Command**:
  ```powershell
  $env:PYTHONPATH="."; .venv\Scripts\python.exe -m backend.app.benchmarks.benchmark_multiturn_adversarial --mode live
  ```
- **Verbatim Stdout**:
  ```
  [EXTERNAL-BLOCKED] Live provider API keys (OPENAI_API_KEY, GEMINI_API_KEY, ANTHROPIC_API_KEY) are not configured in environment. Skipping live evaluation per mock/live doctrine.
  ```
- **Exit Code**: 0

### Execution B: Adversarial 100 in Live Mode (Without API Keys)
- **Command**:
  ```powershell
  $env:PYTHONPATH="."; .venv\Scripts\python.exe -m backend.app.benchmarks.benchmark_adversarial_100 --mode live
  ```
- **Verbatim Stdout**:
  ```
  [EXTERNAL-BLOCKED] Live provider API keys (OPENAI_API_KEY, GEMINI_API_KEY, ANTHROPIC_API_KEY) are not configured in environment. Skipping live evaluation per mock/live doctrine.
  ```
- **Exit Code**: 0

### Execution C: Provider Fixture Contract Tests
- **Command**:
  ```powershell
  $env:PYTHONPATH="."; .venv\Scripts\pytest.exe backend/tests/test_provider_fixture_contracts.py
  ```
- **Verbatim Stdout**:
  ```
  ============================= test session starts =============================
  platform win32 -- Python 3.11.15, pytest-9.1.1, pluggy-1.6.0
  rootdir: E:\per_char
  configfile: pytest.ini
  plugins: anyio-4.15.1, asyncio-1.4.0, base-url-2.1.0, playwright-0.9.0
  asyncio: mode=Mode.AUTO, debug=False, asyncio_default_fixture_loop_scope=None, asyncio_default_test_loop_scope=function
  collected 3 items

  backend\tests\test_provider_fixture_contracts.py ...                     [100%]

  ============================== 3 passed in 0.01s ==============================
  ```
- **Exit Code**: 0

---

## 3. Conclusion

The Mock vs Live Doctrine is strictly implemented and verified. Provider responses are contract-tested against recorded fixtures, and live benchmarking handles unconfigured API credentials gracefully via `[EXTERNAL-BLOCKED]`.
