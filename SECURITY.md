# CodeSage AI — Security Policy & Disclosure Guidelines

Security is a fundamental design requirement for **CodeSage AI**. This document outlines our security architecture, data protection controls, and vulnerability reporting procedures.

---

## 1. Supported Versions

| Version | Supported | Notes |
| :--- | :---: | :--- |
| `v1.0.x` | Yes | Active production release |
| `< v1.0` | No | Pre-release development builds |

---

## 2. Security Architecture & Controls

### Authentication & Authorization (RBAC)
- **GitHub App OAuth 2.0 & App Tokens**: Secure authentication utilizing signed GitHub tokens and HTTP-only session cookies.
- **Role-Based Access Control (RBAC)**: Enforces role permissions (`admin`, `member`, `viewer`) across project settings and repository management APIs.

### Webhook Security & Idempotency
- **Cryptographic Signature Verification**: Incoming GitHub Webhooks must present a valid `X-Hub-Signature-256` computed via timing-safe HMAC SHA-256 comparisons (`hmac.compare_digest`). Unsigned or invalid webhooks are rejected immediately (`HTTP 401`).
- **Delivery Idempotency**: `X-GitHub-Delivery` LRU tracking prevents duplicate job processing and replay attacks.

### Sensitive Data Scrubbing & Audit Safety
- **Automated Metadata Redaction**: All audit events pass through recursive sanitization. Any dictionary keys matching sensitive tokens (`token`, `secret`, `password`, `authorization`, `cookie`, `api_key`, `private_key`) are replaced with `[REDACTED_SENSITIVE_DATA]`.
- **Secret Finding Masking**: Hardcoded secrets detected by the Policy Engine are masked (`sec_1234************`) before being rendered in PR summary reviews or stored in database logs.

### Multi-Tenant Isolation
- Database records, vector embeddings (`CodeChunk`), policy rules, and audit logs enforce tenant constraints. Database queries include explicit `repository_id` or `organization_id` filters to prevent cross-tenant data leakage.

### Network & Infrastructure Security
- **Security Headers Middleware**: Enforces `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Strict-Transport-Security`, and restrictive `Content-Security-Policy` headers.
- **Rate Limiting**: Protects backend endpoints against brute-force and denial-of-service attempts.

---

## 3. Reporting a Vulnerability

If you discover a security vulnerability within **CodeSage AI**:

1. **Do NOT open a public GitHub issue.**
2. Report the details confidentially to the maintainers via security advisory channels.
3. Include a detailed proof-of-concept description, steps to reproduce, and impacted components.
4. We aim to acknowledge reports within 48 hours and provide a resolution timeline within 7 days.
