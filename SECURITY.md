# SECURITY POLICY & THREAT MODEL: ADAPTIVE FINANCIAL TWIN

## 1. Core Security Tenets
In financial digital twin modeling, user data fidelity, privacy, and integrity are strictly non-negotiable. This document defines the threat vectors and the programmatic security controls enforced across the system.

---

## 2. Threat Modeling Matrix (STRIDE & Financial Vectors)

| Threat | Vector | Impact | Mitigating Control |
|---|---|---|---|
| **Spoofing** | Compromised user identity or API keys | Unauthorized access to financial state | Cryptographically signed JWTs with strict expiration, algorithm locking (`HS256`/`RS256`), password hashing via Bcrypt with salt. |
| **Tampering** | Manipulating historical transactions or state logs | False twin state or skewed AI recommendations | Immutable Event Log (`EventLog` table). Historical updates append correction events rather than overwriting historical rows. Checksum validation. |
| **Repudiation** | Denying life events or manual transaction creation | Auditing failure | Immutable audit logging for all mutations with actor ID, IP origin, and UTC microsecond timestamp. |
| **Information Disclosure** | PII leakage, full account number exposure | Privacy breach & compliance violations | Masking rules: Account numbers stored and returned only as masked digits (`****-****-1234`). PII fields minimized. In-transit TLS 1.3, at-rest database encryption. |
| **Denial of Service** | Exhausting server CPU via heavy Monte Carlo simulations | Backend unavailability | Rate limiting (per-user simulation token bucket), vectorized NumPy execution, request timeouts, and async background offloading. |
| **Elevation of Privilege** | Normal user requesting another user's twin state | Multi-tenant cross-account breach | Tenant isolation enforced at database query level (`WHERE user_id = current_user.id`). Role-based access control (RBAC). |
| **Adversarial ML / Prompt Injection** | Injection via merchant notes or chat prompts to force dangerous recommendations | AI hallucination or misleading financial action | Sandboxed LLM layer: LLM never executes financial state transitions. Structured tool inputs with strict Pydantic schemas. System prompt boundary fences. |
| **Recommendation Manipulation** | Biased recommendation generation | Financial loss to user | Hardcoded `FinancialSafetyEngine` invariants that override any RL or ML output if statutory safety boundaries (e.g., minimum cash reserve) are violated. |

---

## 3. Data Protection & Minimization Protocols

### 3.1 PII and Sensitive Data Sanitization
- Bank credentials (usernames, passwords, MFA tokens) are **NEVER** stored or logged.
- Account identifiers are sanitized and masked upon ingestion.
- Logs strictly redact headers matching `Authorization`, `Cookie`, and payloads containing `password`.

### 3.2 Right to be Forgotten & Data Portability
- **Data Export Workflow**: `/api/v1/users/me/export` produces an encrypted JSON bundle containing the user's complete financial ledger and state snapshot history.
- **Data Deletion Workflow**: `/api/v1/users/me/delete` performs a hard cascade delete across all relational records, event logs, simulation results, and vector embeddings.

### 3.3 Static & Dynamic Code Invariants
- Zero raw SQL execution; strictly parameterized queries through SQLAlchemy ORM.
- Input validation on every endpoint via Pydantic v2 type enforcement with strict bounds checking (e.g. interest rates $\ge 0$, amounts $> 0$).
- CORS policy configured to explicitly permitted origins.
