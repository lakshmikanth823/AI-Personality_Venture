# E-29: Live Memory Isolation & Multi-Tenant Security

**Date:** 2026-10-05  
**Phase:** 6 — Controlled Production Activation  
**Gate:** Memory Isolation  
**Status:** **PASS**  
**Evidence Command:** `.venv\Scripts\pytest.exe backend/tests/test_memory.py backend/tests/test_phase3_security_hardening.py -k "memory"`

---

## 1. Multi-Tenant Isolation Verification

The memory subsystem enforces multi-tenant boundary isolation using authenticated user IDs:

| Actor | Action | Target Resource | Result | HTTP Code |
|---|---|---|---|---|
| **User A** | Create durable fact (`dream_job`) | User A Profile | Created | `200 OK` |
| **User A** | Query personal memory facts | User A Profile | Returned (1 fact) | `200 OK` |
| **User B** | Query personal memory facts | User B Profile | Empty (0 facts) | `200 OK` |
| **User B** | Attempt to read User A's conversation | Conversation A | **Access Denied** | `403 Forbidden` |
| **User B** | Attempt to delete User A's memory record | Memory A (`mem-a-...`) | **Not Found** | `404 Not Found` |
| **User A** | Delete personal memory record | Memory A | Deleted | `200 OK` |

---

## 2. Distinction Between User Memory and Character Canon

- **User Memory (`Memory` table)**: Dynamic facts extracted per user (`user_id` foreign key).
- **Character Canon (`CharacterLore` / `CharacterVersion` tables)**: Immutable Kalyan backstory and persona rules, seeded centrally and protected from unauthorized runtime write operations.

---

## 3. Test Traceability

- Automated in [`backend/tests/test_memory.py`](file:///E:/per_char/backend/tests/test_memory.py) and [`backend/tests/test_phase3_security_hardening.py`](file:///E:/per_char/backend/tests/test_phase3_security_hardening.py).
- All 13 memory and tenant isolation tests pass with zero leaks.
