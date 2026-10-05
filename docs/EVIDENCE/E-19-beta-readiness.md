# Evidence Record E-19: Controlled Beta Readiness & Legal Compliance

- **Requirement Reference**: G-19 (DPDP Act 2023 Consent, Public Legal Pages, Report Button & Deployment Friction Audit)
- **UTC Timestamp**: 2026-10-05T04:36:00Z
- **Git Commit Hash**: `2e34e4cfcf99db2e12ecdb0cf8a2f082c3f33374`
- **Status**: CLOSED

---

## 1. Specification & Protocol

The system was audited against regulatory compliance and controlled-beta readiness:
1. **DPDP Act 2023 Consent Enforcement**: Registrations without explicit consent (`consent_given=False`) are rejected with HTTP 400. Valid consents trigger immutable audit log events (`DPDP_CONSENT_CAPTURED`).
2. **Public Legal Documentation**:
   - `GET /privacy`: DPDP Act 2023 compliant notice identifying Data Fiduciary, purpose of processing, Data Principal rights (access, correction, erasure, withdrawal), and official Grievance Redressal Officer details (`grievance@kalyan.ai`).
   - `GET /terms`: Character disclosure establishing Kalyan as an artificial entertainment and satirical property; includes crisis support helpline notices for Tele-MANAS (`14416`) and Kiran (`1800-599-0019`).
3. **In-App Content Report System**: `POST /api/v1/chat/report` enables users to report inappropriate, hazardous, or policy-violating AI responses. Reports are safety-audited, scored by `SafetyEngine`, and permanently logged for human operator review.
4. **Operational Deployment Friction**: Documented in `docs/DEPLOYMENT_FRICTION.md`.

---

## 2. Test Execution & Verbatim Evidence

- **Command**:
  ```powershell
  $env:PYTHONPATH="."; .venv\Scripts\pytest.exe -v backend/tests/test_beta_readiness.py
  ```
- **Verbatim Stdout**:
  ```
  ============================= test session starts =============================
  platform win32 -- Python 3.11.15, pytest-9.1.1, pluggy-1.6.0 -- E:\per_char\.venv\Scripts\python.exe
  cachedir: .pytest_cache
  rootdir: E:\per_char
  configfile: pytest.ini
  plugins: anyio-4.15.1, asyncio-1.4.0, base-url-2.1.0, playwright-0.9.0
  asyncio: mode=Mode.AUTO, debug=False, asyncio_default_fixture_loop_scope=None, asyncio_default_test_loop_scope=function
  collecting ... collected 3 items

  backend/tests/test_beta_readiness.py::test_dpdp_consent_enforcement_at_signup PASSED [ 33%]
  backend/tests/test_beta_readiness.py::test_privacy_and_terms_endpoints PASSED [ 66%]
  backend/tests/test_beta_readiness.py::test_in_app_content_report_button PASSED [100%]

  ============================== 3 passed in 0.38s ==============================
  ```
- **Exit Code**: 0

---

## 3. Compliance Verification Status

- **DPDP Act 2023 Consent**: Verified active and enforced on registration.
- **Privacy Notice & Grievance Contact**: Verified active at `/privacy`.
- **Character Disclosure & Crisis Helplines**: Verified active at `/terms`.
- **In-App Content Report Tool**: Verified operational at `/api/v1/chat/report`.
- **Deployment Friction Runbook**: Verified and cataloged in `docs/DEPLOYMENT_FRICTION.md`.
