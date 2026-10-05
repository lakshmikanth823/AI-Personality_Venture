# E-27: Environment Rebuild & Green Suite

**UTC Timestamp:** 2026-10-05T07:30:27Z  
**Git Commit:** `6b2d9036d0d5f9b7558e7c5d5c53dc5c03361930`  
**Claim:** Virtual environment rebuilt from scratch, all dependencies installed, full test suite (76/76) passes.

---

## (a) Commands Executed

```powershell
# Step 1: venv creation
python -m venv .venv

# Step 2: pip upgrade
.venv\Scripts\python.exe -m pip install --upgrade pip

# Step 3: base deps
.venv\Scripts\pip.exe install -r backend\requirements.txt

# Step 4: dev deps
.venv\Scripts\pip.exe install -r backend\requirements-dev.txt

# Step 5: import sanity check
.venv\Scripts\python.exe -c "import pyotp, email_validator, jose, bcrypt, playwright, PIL, psutil; print('OK')"

# Step 6: full test suite
.venv\Scripts\pytest.exe -q > pytest_out.log 2>&1
```

---

## (b) Verbatim stdout/stderr excerpts

### Import sanity check
```
OK
```

### Pytest final output (tail)
```
........................................................................  [ 94%]
....                                                                      [100%]
============================== warnings summary ==============================
backend/tests/test_failure_injection.py::test_failure_injection_database_operational_recovery
  SAWarning: New instance <User at ...> with identity key ... conflicts with persistent instance
    db.commit()

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
76 passed, 1 warning in 53.41s
```

**Exit code: 0**

---

## (c) UTC Timestamp
`2026-10-05T07:30:27Z`

---

## (d) Git commit hash
`6b2d9036d0d5f9b7558e7c5d5c53dc5c03361930`

---

## Root Cause & Fix Notes

- **DPDP test failure** — `conftest.py` set `settings.ENVIRONMENT = "test"` but `auth.py` guards checked `settings.APP_ENV`. Fix: added `settings.APP_ENV = "test"` in `conftest.py` (test file only, R3 compliant).
- **Cohort cap test failure** — once `APP_ENV = "test"` bypassed capacity globally, `test_beta_cohort_cap_enforcement_at_signup` expected a 403 but got 200. Fix: added `monkeypatch.setattr(settings, "APP_ENV", "staging")` inside that specific test to re-enable enforcement (test file only, R3 compliant).
- **No production code edited** to chase test failures.
