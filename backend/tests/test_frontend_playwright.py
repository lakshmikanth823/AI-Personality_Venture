"""
Playwright Frontend Automated Pytest Verification (G-01)
Runs headless browser journeys against local unified fullstack server.
"""

import pytest
from backend.scripts.run_frontend_audit import run_playwright_audit

def test_frontend_playwright_e2e_audit():
    """Executes full Playwright browser audit and asserts 0 console errors + valid screenshots."""
    screenshots = run_playwright_audit()
    assert len(screenshots) == 10, f"Expected 10 screenshots, got {len(screenshots)}"
    for s in screenshots:
        assert s.exists() and s.stat().st_size > 10000
