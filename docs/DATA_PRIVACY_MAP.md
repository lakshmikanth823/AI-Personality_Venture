# Kalyan AI Personality Venture — Data Privacy Map & Compliance Architecture

**Date**: October 5, 2026  
**Regulatory Standards**: Digital Personal Data Protection (DPDP) Act 2023 (India) & General Data Protection Regulation (GDPR)  
**Classification**: Enterprise Compliance & Security Baseline

---

## 1. Data Inventory & Entity Mapping

| Entity / Table | Fields Stored | Sensitivity Tier | Purpose of Processing | Retention Policy | Erasure Mechanism |
|---|---|---|---|---|---|
| `users` | `id`, `email`, `username`, `hashed_password`, `role`, `is_active`, `personalization_enabled` | **Confidential** | Authentication, authorization, identity verification, privacy consent state | Account lifetime + 30 days after deletion | Cascading hard delete upon user termination request |
| `profiles` | `id`, `user_id`, `display_name`, `avatar_url`, `preferred_language`, `bio` | **Standard** | UI personalization and cultural code-switching | Account lifetime | Updated or wiped via Profile Settings |
| `conversations` | `id`, `user_id`, `channel`, `title`, `created_at`, `updated_at` | **Confidential** | Session grouping and multi-turn context | 90 days active retention | Cascading delete with user account or manual session wipe |
| `messages` | `id`, `conversation_id`, `role`, `content`, `tokens_input`, `tokens_output`, `latency_ms`, `cost_usd`, `risk_tier` | **Confidential** | Chat history, audit trail, cost accounting | 90 days active retention | Deletion alongside conversation |
| `memories` | `id`, `user_id`, `memory_type`, `key`, `value`, `confidence`, `is_active` | **Sensitive** | L3 durable episodic personalization (e.g., hometown, career goals) | Active until modified or forgotten | User-controlled `DELETE /api/v1/memories/{id}` |
| `subscriptions` | `id`, `user_id`, `plan_tier`, `status`, `started_at`, `expires_at`, `total_paid_inr` | **Confidential** | Subscription state and quota entitlement | 7 years (statutory financial audit) | Anonymized after statutory retention |
| `payment_transactions` | `id`, `subscription_id`, `user_id`, `plan_tier`, `amount_inr`, `currency`, `payment_reference`, `status` | **Confidential** | Payment reconciliation and dispute resolution | 7 years (Indian RBI / Income Tax guidelines) | Retained for financial compliance |
| `audit_logs` | `id`, `actor_id`, `actor_role`, `action`, `target_type`, `target_id`, `details_json`, `ip_address` | **Restricted** | Security audit, kill switch tracking, operator accountability | 1 year rolling audit window | Append-only; no programmatic deletion |
| `content_candidates` | `id`, `channel`, `source_type`, `prompt_context`, `generated_text`, `status`, `risk_tier` | **Internal** | Social content generation and approval queue | 180 days | Archived / pruned by operator |

---

## 2. DPDP Act 2023 & GDPR Rights Implementation

### A. Notice & Consent (DPDP Section 5 & 6)
- **Granular Consent**: Users have an explicit `personalization_enabled` boolean switch on their profile.
- **Immediate Effect**: When `personalization_enabled == False`:
  1. The memory extraction pipeline is completely bypassed.
  2. No L3 durable memories are retrieved or injected into the prompt assembly.
  3. The AI interacts purely ephemerally.

### B. Right to Access & Data Portability (DPDP Section 11 / GDPR Art. 15)
- Users can inspect all stored memories via `GET /api/v1/memories/`.
- Users can review complete conversation histories via `GET /api/v1/chat/conversations`.

### C. Right to Erasure / Right to Be Forgotten (DPDP Section 12 / GDPR Art. 17)
- Users can delete any specific durable memory via `DELETE /api/v1/memories/{memory_id}`.
- Ownership is strictly enforced (`memory.user_id == current_user.id`), preventing unauthorized deletions.
- Memory extraction actively filters out forbidden entities: phone numbers, passwords, PAN/Aadhaar formats, and credit cards are rejected by anti-poisoning defenses before storage.

### D. Multi-Tenant Isolation & Zero Leakage
- Every database query accessing conversations or memories explicitly filters on `current_user.id`.
- Foreign tenant access attempts result in HTTP `403 Forbidden`.
- Automated test `test_memory_multi_tenant_isolation` verifies that User A's memories are never retrieved for User B.

---

## 3. Data Security & Storage Safeguards

1. **Passwords**: Hashed with `bcrypt` (12 work factor rounds) using salt-stretching. Plaintext passwords are never logged or stored.
2. **Webhooks**: Razorpay/Stripe webhooks are validated using HMAC-SHA256 constant-time comparison against `WEBHOOK_SECRET`.
3. **JWT Tokens**: Signed using HMAC-SHA256 with 24-hour expiration. Revocation supported via secret rotation.
4. **Transport Encryption**: All client-server and server-upstream communications require TLS 1.3 in production environments.
5. **Database Security**: SQLite file access permissions restricted to the running system process (`chmod 600` on Linux, ACL inheritance on Windows). Prepared statements used exclusively via SQLAlchemy ORM to prevent SQL injection.
