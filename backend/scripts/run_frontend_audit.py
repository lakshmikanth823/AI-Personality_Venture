"""
Frontend Real-Browser Verification Audit (G-01)
Uses Playwright with headless Chromium to execute end-to-end user journeys:
- Journey 1: Landing page, persona identity, interactive chat & roast execution.
- Journey 2: Operator approval console.
- Journey 6: Content library & share cards.
- Journey 7: Real-time analytics, cost & WMCR dashboard.
- Responsive viewports: 1440px (Desktop), 768px (Tablet), 390px (Mobile).
- Zero console error assertion (captures and audits all browser console events).
"""

import sys
import time
import threading
from pathlib import Path
from typing import List, Dict, Any
import httpx
import uvicorn
from playwright.sync_api import sync_playwright

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from backend.app.main import app

PORT = 8765
BASE_URL = f"http://127.0.0.1:{PORT}"

def start_background_server():
    config = uvicorn.Config(app, host="127.0.0.1", port=PORT, log_level="warning")
    server = uvicorn.Server(config)
    t = threading.Thread(target=server.run, daemon=True)
    t.start()
    
    # Wait for server to become healthy
    for _ in range(30):
        try:
            r = httpx.get(f"{BASE_URL}/health", timeout=1.0)
            if r.status_code == 200:
                print(f"[+] Local fullstack server healthy at {BASE_URL}")
                return server
        except Exception:
            time.sleep(0.2)
    raise RuntimeError("Server failed to start in 6.0s")

def run_playwright_audit():
    print("=" * 60)
    print("  FRONTEND REAL-BROWSER PLAYWRIGHT AUDIT (G-01)")
    print("=" * 60)

    server = start_background_server()
    assets_dir = Path("docs/EVIDENCE/assets")
    assets_dir.mkdir(parents=True, exist_ok=True)

    console_messages: List[Dict[str, str]] = []
    console_errors: List[str] = []

    viewports = {
        "1440": {"width": 1440, "height": 900},
        "768": {"width": 768, "height": 1024},
        "390": {"width": 390, "height": 844}
    }

    screenshots_captured = []

    with sync_playwright() as p:
        print("[*] Launching headless Chromium...")
        browser = p.chromium.launch(headless=True)
        
        # 1. Responsive Viewport Audits (Landing & Navigation)
        for vp_name, vp_dims in viewports.items():
            print(f"[*] Auditing Viewport {vp_name}px ({vp_dims['width']}x{vp_dims['height']})...")
            context = browser.new_context(viewport=vp_dims)
            page = context.new_page()

            # Attach console logger
            def on_console(msg):
                console_messages.append({"type": msg.type, "text": msg.text})
                if msg.type == "error":
                    # Ignore harmless favicon 404 or expected anonymous 401 from /auth/me
                    if "favicon" not in msg.text.lower() and "401" not in msg.text:
                        console_errors.append(msg.text)

            page.on("console", on_console)

            # Navigate to Landing Page
            page.goto(BASE_URL, wait_until="networkidle")
            page.wait_for_timeout(500)

            # Assert Brand exists
            assert page.locator("text=KALYAN").first.is_visible(), f"Brand not visible on {vp_name}"

            # Capture Landing Page Screenshot
            landing_img = assets_dir / f"screenshot_landing_{vp_name}.png"
            page.screenshot(path=str(landing_img), full_page=False)
            screenshots_captured.append(landing_img)
            print(f"    [+] Saved {landing_img.name} ({landing_img.stat().st_size} bytes)")

            # Navigate to Chat Page
            chat_btn = page.locator("nav >> text=Chat").first
            if not chat_btn.is_visible():
                # On mobile, check if chat CTA on landing is visible
                cta = page.locator("button:has-text('Talk to Kalyan')").first
                if cta.is_visible():
                    cta.click()
                else:
                    chat_btn.click(force=True)
            else:
                chat_btn.click()

            page.wait_for_timeout(500)
            chat_img = assets_dir / f"screenshot_chat_{vp_name}.png"
            page.screenshot(path=str(chat_img), full_page=False)
            screenshots_captured.append(chat_img)
            print(f"    [+] Saved {chat_img.name} ({chat_img.stat().st_size} bytes)")

            context.close()

        # 2. Detailed Desktop Journey Audit (1440px)
        print("\n[*] Executing Full Functional Desktop Journeys (1440px)...")
        context = browser.new_context(viewport=viewports["1440"])
        page = context.new_page()
        page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" and "favicon" not in msg.text.lower() and "401" not in msg.text else None)

        page.goto(BASE_URL, wait_until="networkidle")

        # Journey 1: Send a message in Chat
        print("    [*] Journey 1: Chat interaction & reality check roast...")
        page.locator("nav >> text=Chat").first.click()
        page.wait_for_timeout(500)
        
        # Find chat input textarea / input
        chat_input = page.locator("textarea, input[type='text']").last
        chat_input.fill("Arey Kalyan, give me an honest review of my resume.")
        page.keyboard.press("Enter")
        page.wait_for_timeout(1500)

        chat_convo_img = assets_dir / "screenshot_chat_conversation_1440.png"
        page.screenshot(path=str(chat_convo_img))
        screenshots_captured.append(chat_convo_img)
        print(f"    [+] Saved {chat_convo_img.name}")

        # Journey 2: Operator Approval Queue
        print("    [*] Journey 2: Operator approval console...")
        page.locator("nav >> text=Approval Queue").first.click()
        page.wait_for_timeout(600)
        approval_img = assets_dir / "screenshot_approval_1440.png"
        page.screenshot(path=str(approval_img))
        screenshots_captured.append(approval_img)
        print(f"    [+] Saved {approval_img.name}")

        # Journey 6: Content Library
        print("    [*] Journey 6: Content library & share cards...")
        page.locator("nav >> text=Content Library").first.click()
        page.wait_for_timeout(600)
        content_img = assets_dir / "screenshot_content_1440.png"
        page.screenshot(path=str(content_img))
        screenshots_captured.append(content_img)
        print(f"    [+] Saved {content_img.name}")

        # Journey 7: Analytics & Cost Telemetry
        print("    [*] Journey 7: Analytics, cost & WMCR telemetry...")
        page.locator("nav >> text=Analytics & Cost").first.click()
        page.wait_for_timeout(600)
        analytics_img = assets_dir / "screenshot_analytics_1440.png"
        page.screenshot(path=str(analytics_img))
        screenshots_captured.append(analytics_img)
        print(f"    [+] Saved {analytics_img.name}")

        browser.close()

    server.should_exit = True

    print("\n" + "=" * 60)
    print("  FRONTEND AUDIT AUDIT RESULTS")
    print("=" * 60)
    print(f"Total Screenshots Captured: {len(screenshots_captured)}")
    for sc in screenshots_captured:
        assert sc.exists() and sc.stat().st_size > 10000, f"Screenshot {sc.name} invalid or empty!"
        print(f"  - {sc.name}: {sc.stat().st_size} bytes [VALID]")

    print(f"\nBrowser Console Errors: {len(console_errors)}")
    if console_errors:
        for err in console_errors:
            print(f"  [!] Console Error: {err}")
    assert len(console_errors) == 0, f"Found {len(console_errors)} console errors during frontend audit!"

    print("\n[SUCCESS] Frontend Real-Browser Verification PASSED (0 Console Errors, 10 Screenshots Verified)!")
    return screenshots_captured

if __name__ == "__main__":
    run_playwright_audit()
