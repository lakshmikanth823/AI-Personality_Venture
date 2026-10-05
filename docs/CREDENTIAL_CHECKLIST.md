# Credential Checklist

This document lists all external service credentials required for live operation.
Each entry must be reviewed and populated by a human operator before enabling live features.

## Required Credentials

- **GEMINI_API_KEY**: `OWNER: HUMAN`
- **OPENAI_API_KEY**: `OWNER: HUMAN`
- **ANTHROPIC_API_KEY**: `OWNER: HUMAN`
- **X_API_KEY**: `OWNER: HUMAN`
- **X_API_SECRET**: `OWNER: HUMAN`
- **X_ACCESS_TOKEN**: `OWNER: HUMAN`
- **X_ACCESS_SECRET**: `OWNER: HUMAN`
- **INSTAGRAM_ACCESS_TOKEN**: `OWNER: HUMAN`
- **INSTAGRAM_PAGE_ID**: `OWNER: HUMAN`
- **YOUTUBE_API_KEY**: `OWNER: HUMAN`
- **WHATSAPP_TOKEN**: `OWNER: HUMAN`
- **WHATSAPP_PHONE_NUMBER_ID**: `OWNER: HUMAN`
- **WHATSAPP_VERIFY_TOKEN**: `OWNER: HUMAN` (default provided, should be rotated in production)
- **RAZORPAY_KEY_ID**: `OWNER: HUMAN`
- **RAZORPAY_KEY_SECRET**: `OWNER: HUMAN`
- **RAZORPAY_WEBHOOK_SECRET**: `OWNER: HUMAN`

## Notes
- Credentials marked `OWNER: HUMAN` must never be committed to source control.
- For CI/CD pipelines, use secret injection mechanisms.
- Live social broadcasting is disabled until all above are provided.
