# Security Policy & Threat Model (STRIDE)

## Security Architecture Overview

The **Personal Finance Agent** is architected for public deployment with strong multi-tenant data isolation, field-level encryption at rest, rate limiting, and prompt injection containment.

## STRIDE Threat Model & Mitigations

| Threat Category | Description | Applied Security Mitigation Controls |
| :--- | :--- | :--- |
| **Spoofing** | Unauthorized user identity impersonation or JWT forgery. | Argon2id password hashing, short-lived JWT access tokens (15 min), httpOnly Secure refresh cookies, token type claims validation. |
| **Tampering** | Modifying parameters to access another user's financial data (IDOR). | Repository layer forces `user_id` query scoping on all operations; PostgreSQL Row-Level Security (RLS) policies enforced. |
| **Repudiation** | Denying sensitive administrative or user actions. | Immutable audit log table (`audit_logs`) tracking action timestamps, IP addresses, and resource IDs without logging PII. |
| **Information Disclosure** | Data leaks in logs, DB dumps, or network transit. | Sensitive fields encrypted at rest using AES-256 (Fernet); account numbers masked (`XXXX-XXXX-1234`); PII redacted in logs; TLS in transit. |
| **Denial of Service** | Resource exhaustion via huge CSV files or LLM API flooding. | File upload cap (5MB, 10k rows max); slowapi rate limits per IP/user; daily LLM token quota per user. |
| **Elevation of Privilege** | Normal user attempting administrative metric access. | Role-Based Access Control (`role == 'admin'`); Admin endpoints return ONLY aggregate, anonymized metrics—never individual transaction records. |
| **Prompt Injection** | Malicious transaction descriptions attempting LLM hijack. | Merchant strings stripped of control text, wrapped in explicit quoted data blocks, and evaluated against strict JSON schemas with template fallback. |

## Vulnerability Disclosure Protocol

If you discover a security vulnerability in this project, please send a detailed security report to `security@personalfinanceagent.example.com`. Do NOT file public GitHub issues for security bugs.
