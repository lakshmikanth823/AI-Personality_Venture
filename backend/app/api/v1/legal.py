"""
Legal, Compliance & Privacy Endpoints (G-19)
Implements Digital Personal Data Protection (DPDP) Act 2023 compliance notice,
Grievance Redressal mechanism, and Character Terms of Service.
"""

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter(tags=["legal"])

PRIVACY_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Privacy Policy - Kalyan AI (DPDP Act 2023 Compliant)</title>
  <style>
    body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #0a0b0e; color: #e2e8f0; line-height: 1.6; max-width: 800px; margin: 0 auto; padding: 40px 20px; }
    h1 { color: #f97316; border-bottom: 2px solid #334155; padding-bottom: 12px; }
    h2 { color: #fdba74; margin-top: 32px; }
    .badge { display: inline-block; background: #166534; color: #bbf7d0; padding: 4px 10px; border-radius: 9999px; font-size: 12px; font-weight: bold; margin-bottom: 16px; }
    a { color: #38bdf8; }
    .box { background: #1e293b; border: 1px solid #334155; border-radius: 8px; padding: 16px; margin: 16px 0; }
  </style>
</head>
<body>
  <div class="badge">DPDP ACT 2023 COMPLIANT</div>
  <h1>Privacy Notice & Data Principal Rights</h1>
  <p><strong>Effective Date:</strong> October 2026 | <strong>Entity:</strong> Kalyan AI Personality Venture</p>
  
  <div class="box">
    <strong>Grievance Redressal Officer:</strong><br>
    Data Protection Officer, Kalyan AI Venture<br>
    Email: <a href="mailto:grievance@kalyan.ai">grievance@kalyan.ai</a><br>
    Address: Ameerpet Metro Station Road, Hyderabad, Telangana, India - 500016
  </div>

  <h2>1. Data We Collect</h2>
  <p>Under the Digital Personal Data Protection (DPDP) Act 2023, we collect personal data strictly on the basis of informed, explicit consent provided at registration:</p>
  <ul>
    <li><strong>Account Information:</strong> Username, email address, password hash.</li>
    <li><strong>Conversational Interactions:</strong> User prompts, messages, and feedback.</li>
    <li><strong>Personalization Memory (Optional):</strong> Preferences and topical interests you share. You can turn off personalization or erase all memories at any time in your Settings.</li>
  </ul>

  <h2>2. Purpose of Processing</h2>
  <ul>
    <li>Providing culturally contextual, entertaining, and witty conversational responses in Kalyan's persona.</li>
    <li>Preventing platform abuse, prompt injection attacks, and ensuring safety boundaries.</li>
    <li>Calculating aggregated usage metrics and server performance telemetry.</li>
  </ul>

  <h2>3. Data Principal Rights</h2>
  <ul>
    <li><strong>Right to Access:</strong> View all stored interactions and memories via the Chat and Memory interfaces.</li>
    <li><strong>Right to Correction & Erasure:</strong> Delete any individual memory or wipe your entire memory profile instantly.</li>
    <li><strong>Right of Grievance Redressal:</strong> Submit inquiries or grievances to our Data Protection Officer at grievance@kalyan.ai. Responses guaranteed within 72 business hours.</li>
    <li><strong>Right to Nominate:</strong> You may designate another individual to exercise your rights in accordance with the DPDP rules.</li>
  </ul>
</body>
</html>
"""

TERMS_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Terms of Service - Kalyan AI</title>
  <style>
    body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #0a0b0e; color: #e2e8f0; line-height: 1.6; max-width: 800px; margin: 0 auto; padding: 40px 20px; }
    h1 { color: #f97316; border-bottom: 2px solid #334155; padding-bottom: 12px; }
    h2 { color: #fdba74; margin-top: 32px; }
    .helpline-box { background: #7c2d12; border: 1px solid #ea580c; border-radius: 8px; padding: 16px; margin: 20px 0; }
  </style>
</head>
<body>
  <h1>Terms of Service & Character Disclosure</h1>
  <p><strong>Effective Date:</strong> October 2026</p>

  <div class="helpline-box">
    <strong>EMERGENCY & CRISIS DISCLOSURE:</strong><br>
    Kalyan is an artificial intelligence character designed for entertainment, cultural humor, and satirical career reality checks. Kalyan is NOT a licensed therapist, doctor, lawyer, or financial advisor.<br><br>
    If you or someone you know is struggling or in crisis, help is available. Speak with someone today:<br>
    • <strong>Tele-MANAS (Govt of India):</strong> Call <strong>14416</strong> or <strong>1800-891-4416</strong> (24/7, Toll-Free)<br>
    • <strong>Kiran Mental Health Helpline:</strong> Call <strong>1800-599-0019</strong>
  </div>

  <h2>1. Character Nature & Brutal Honesty</h2>
  <p>Kalyan uses satirical, irreverent, and filterless humor rooted in Hyderabad / Ameerpet tech culture. His roasts, opinions, and banter are character expressions and do not constitute defamatory statements or verified facts.</p>

  <h2>2. Acceptable Use Policy</h2>
  <p>Users agree not to:</p>
  <ul>
    <li>Attempt jailbreaks, prompt injection, or weaponization of the persona.</li>
    <li>Submit hazardous, self-harm, sexually explicit, abusive, or defamatory content.</li>
    <li>Harass, dox, or extract confidential server configuration.</li>
  </ul>

  <h2>3. In-App Reporting</h2>
  <p>If you encounter inappropriate, policy-violating, or unexpected behavior from the AI, please use the in-app "Report Content" tool or contact <a href="mailto:safety@kalyan.ai" style="color: #38bdf8;">safety@kalyan.ai</a>.</p>
</body>
</html>
"""

@router.get("/privacy", response_class=HTMLResponse)
def get_privacy_policy():
    return HTMLResponse(content=PRIVACY_HTML)

@router.get("/terms", response_class=HTMLResponse)
def get_terms_of_service():
    return HTMLResponse(content=TERMS_HTML)
