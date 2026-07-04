# Software Design Document (SDD) - Aporte App

**Project Phase:** MVP / Proof of Concept (Local Distributed Lab)  
**Target Architecture:** Multi-tenant Asynchronous Fintech SaaS

---

## 1. System Overview & Business Goals

### 1.1 Business Objective (Aporte Core)

Aporte is a mobile-first Fintech SaaS engineered to manage and automate utility and property-management payments for residential complexes (condominiums) in Venezuela. The primary product goal is to eliminate the high-friction, error-prone operational bottleneck faced by property managers: manual verification and data entry of bank transfers and "Pago Móvil" reported by residents.

### 1.2 Core Architectural Challenges

- **Multi-tenancy:** Complete logical isolation between independent residential clusters (e.g., "Los Sauces" vs. "Ávila") sharing the same compute and database instances.
- **Deterministic AI Automation:** Leveraging Large Language Models (LLMs) via LangChain to parse unformatted financial data chunks without introducing hallucinations or unpredictable states into the financial ledger.
- **Resilience:** Preventing system-wide failures if external AI providers or orchestrators experience high latencies or service blackouts.

---

## 2. Security, Authentication & Multi-Tenancy

To balance a frictionless experience for day-to-day users with enterprise-grade security for financial operators, the system enforces strict segregation at both the authentication and data layers.

### 2.1 Bifurcated Authentication Flows & Context Switching

The platform implements an adaptable authorization path inside Django REST Framework (DRF) and Next.js based on the sensitivity of the operation rather than a rigid fixed account:

1. **Resident/Neighbor Operation Context (Low Friction):**
   - **Mechanism:** Passwordless login using a combination of **Cédula de Identidad** (National ID) and **Phone Number**.
   - **Scope:** Standard ledger viewing and payment reporting. If an Administrator utilizes a deep link from an SMS to check or pay their individual personal unit's balance, the system authenticates them strictly under this low-friction resident scope. No password or 2FA is requested.
2. **Administrative Operation Context (High Security / Step-up Auth):**
   - **Mechanism:** Email + Strong Password + Mandatory **Two-Factor Authentication (2FA)**.
   - **Dynamic Trigger:** When a unified user with administrative privileges attempts to elevate their context from the personal resident dashboard to the global financial backend panel, the Next.js frontend intercepts the route and enforces a **Step-up Authentication** challenge. The user must provide their password and validate a temporary 5-minute OTP dispatched via Redis before global financial access tokens are granted.

### 2.2 Multi-Tenant Data Isolation Strategy

Aporte employs a **Shared Database, Isolated Schemas / Shared Schema with Tenant Discriminator** design inside PostgreSQL to map distinct real estate entities.

- **Tenant Resolution:** The Next.js frontend captures the target cluster context via subdomains or route prefixes (e.g., `lossauces.aporte.com`).
- **API Isolation Contract:** Every HTTP request dispatched to the DRF API must contain a mandatory custom header: `X-Tenant-ID: <tenant-uuid>`.
- **Backend Middleware Enforcement:** A global scoping middleware intercepts inbound requests, validates the cryptographic token, and enforces a strict structural filter on all active ORM queries (`QuerySet.filter(tenant_id=current_tenant)`), ensuring cross-tenant data leaks are mathematically impossible.

---

## 3. Asynchronous AI Bank Reconciliation Pipeline

### 3.1 UX/UI Ingest & Client-Side Processing

To eliminate manual data entry, the system uses a hybrid approach to transform physical visual evidence into structured strings.

1. **Native Hardware Access:** The mobile-first Next.js UI uses native standard HTML5 capture mechanisms (`<input type="file" accept="image/*">`) to trigger native file explorer windows in desktop environments (Windows/macOS) and native camera/gallery drawers on mobile platforms (iOS/Android).
2. **Client-Side Optical Character Recognition (OCR):** Selected receipts are processed entirely within the user's browser device using `Tesseract.js` (compiled to WebAssembly).
3. **Reactive Form Fields:**
   - **Scenario A (Success):** If the client-side OCR parses text matching standard banking transaction patterns via local Regular Expressions, it dynamically autofills a visible `reference_last_4` placeholder field.
   - **Scenario B (Degraded):** If the receipt image is blurred or low-light, the client-side engine fails silently without blocking the interface. The `reference_last_4` input is instantly unlocked for standard, manual key-in input from the user.
4. **Validation Constraint:** The payload layout explicitly demands both the physical `evidence_file` image and the structured `reference_last_4` string before enabling form submission.

### 3.2 Data Flow & Deterministic LangChain Execution

Once data hits the backend, the processing is offloaded to a background task runner to handle long-running LLM completions gracefully.

- **Data Masking (Privacy Mitigations):** Before passing the raw text strings to external LLM providers, Django runs a local sanitization pipeline using localized regex filters to strip Personally Identifiable Information (PII) like full names or bank account prefixes, substituting them with internal placeholder keys (`[CLIENT_A]`, `[ID_A]`).
- **Context Window Strategy:** Large unformatted bank statement strings are segmented into targeted data chunks via LangChain text splitters. The agent implements a Map-Reduce structural flow to parse groups of transactions iteratively without exhausting context windows.
- **Guaranteed Determinism:** The agent model parameters force a `temperature = 0`. LangChain enforces structural serialization constraints using **Pydantic Model Validations**. If the LLM output deviates from the strict structural schema layout defined for financial items, the payload fails structural validation checks before making any state updates.
- **Collision Handling & Context Resemblance:** In massive residential sectors where identical final reference chains match (e.g., two neighbors submitting different payments both ending in reference `4589`), the backend crosses reference tokens with the metadata inside the authenticated resident's profile (Cédula, specific phone origin, or contextual names found inside the enmasked image) to automatically and safely resolve the account ownership.

### 3.3 Resilience & Graceful Performance Degradation

The infrastructure treats external AI connectivity errors as expected events, ensuring zero operational downtime for the core business entity.

- **Exponential Backoff:** If the AI agent worker throws connectivity errors (`HTTP 503` or timeout thresholds), the Redis task pipeline retains the state and automatically schedules re-execution loops with randomized backoff parameters.
- **Degraded Manual Fallback:** If API failures persist outside safe operational boundaries, the backend automatically sets the transaction status flags to `PENDING_MANUAL_REVIEW`. The record is moved out of the automation loop and appended to a specialized manual ledger inside the administrator's operational interface, allowing standard manual click-to-approve execution.

---

## 4. Property Census Ingest & Outbound Notifications

### 4.1 Coproprietor Ingest Module (Onboarding)

To guarantee the data completeness needed for the passwordless strategy, the system provides flexible, high-fidelity intake mechanics for administrators.

- **Individual Entry:** A reactive Next.js form utilizing strict, normalized real estate dropdown fields (`Torre` ➔ `Piso` ➔ `Apartamento`) to ensure data sanitization.
- **Bulk Ingest Pipeline (Excel/CSV):** Administrators can leverage a structured batch ingestion tool. The frontend reads the file locally, rendering an interactive structural table with instant cell-by-cell data type verification before dispatching a `Bulk Create` transaction payload to the backend database layer.

### 4.2 Outbound Notification Channels (Frictionless SMS)

The platform prioritizes SMS over standard mobile applications or push notifications to optimize delivery and minimize user friction. By deploying a mobile-responsive web platform accessible via standard mobile browsers, the system guarantees 100% device compatibility without forcing users to download application packages from digital stores.

- **Message Structure Constraint:** Messages must strictly fit within the standard 160-character single-SMS threshold to minimize operational routing costs.
- **Dynamic Query-Param Pre-loading (Deep Linking):** To maintain the passwordless paradigm with minimal user friction, notification links are synthesized dynamically, appending user credentials directly into the URL parameters.
- **Deep Linking Flow:** When an SMS is received (e.g., "Your Avila condominium bill is ready. Tap to view and report your payment: http://aporte.com/login?c=123456&t=04125555555"), tapping the link opens the default mobile browser. The Next.js framework extracts 'c' (Cédula) and 't' (Phone) from the active URL query state, automatically injects values into the form fields, and presents a pre-filled layer requiring a single-tap authorization.

### 4.3 In-House URL Shortener Technical Specification

To decouple the platform from third-party routing dependencies and optimize infrastructure costs, the Django backend implements an internal URL shortening utility.

- **Database Schema (`ShortURL`):** A high-performance lookup table mapping a unique short alphanumeric token directly to the target tenant destination URL string.
- **Token Generation Algorithm (Base62 Encoding):** The system avoids utilizing standard incremental integers or heavy UUIDs for public routing keys. It converts internal surrogate keys or hashes into a Base62 alphabet (`[a-zA-Z0-9]`). A 5-character token constraint yields 62^5 = 916,132,832 discrete permutations, guaranteeing minimal payload footprints within the 160-character SMS limit.
- **Caching Layer Isolation:** To protect the primary transactional PostgreSQL instance from redundant redirect I/O bottlenecks during mass monthly billing notifications, successfully resolved tokens are cached in **Redis** with an expiration window, enabling sub-millisecond redirection operations directly from memory.

---

## 5. Database Schema & Entity-Relationship Model (PostgreSQL)

The database layers are structured to support multi-tenancy logical isolation, passwordless authentication for residents, and multi-role unified profiles for administrators who are also property owners.

### 5.1 Core Tables Specification

#### 5.1.1 `Tenant` (Condominium Clusters)

Represents the independent residential complexes.

- `id`: `UUID` (Primary Key)
- `name`: `VARCHAR(150)` (e.g., "Condominio Avila")
- `slug`: `VARCHAR(100)` (Unique, URL safe, e.g., "avila")
- `created_at`: `TIMESTAMP`

#### 5.1.2 `CustomUser` (Unified Identity Table)

Handles authentication and core profile data.

- `id`: `UUID` (Primary Key)
- `tenant_id`: `UUID` (Foreign Key -> Tenant)
- `national_id`: `VARCHAR(20)` (Cédula de Identidad, e.g., "V-12345678")
- `phone_number`: `VARCHAR(20)` (e.g., "+584125555555")
- `email`: `VARCHAR(255)` (Nullable, required only for Admin elevation)
- `password`: `VARCHAR(255)` (Nullable, hashed, required only for Admin elevation)
- `first_name`: `VARCHAR(100)`
- `last_name`: `VARCHAR(100)`
- `role`: `VARCHAR(20)` (Enum: `['RESIDENT', 'ADMIN', 'SUPERADMIN']`)
- `is_active`: `BOOLEAN` (Default: `True`)

_Constraints:_ `Unique(tenant_id, national_id)` and `Unique(tenant_id, phone_number)`. This ensures credentials are unique inside a single condominium, but allows the same phone/cédula to exist in different tenants if a user owns properties in multiple complexes.

#### 5.1.3 `Property` (Real Estate Units)

Represents physical apartments, townhouses, or shops.

- `id`: `UUID` (Primary Key)
- `tenant_id`: `UUID` (Foreign Key -> Tenant)
- `owner_id`: `UUID` (Foreign Key -> CustomUser, Nullable if empty)
- `building_tower`: `VARCHAR(50)` (e.g., "Torre A")
- `floor`: `VARCHAR(20)` (e.g., "Piso 4")
- `unit_number`: `VARCHAR(50)` (e.g., "Apto 42")
- `current_balance`: `NUMERIC(12, 2)` (Default: `0.00`)

#### 5.1.4 `Transaction` (Financial Reconciliation Ledger)

Tracks reported customer payments and automated reconciliation outcomes.

- `id`: `UUID` (Primary Key)
- `tenant_id`: `UUID` (Foreign Key -> Tenant)
- `property_id`: `UUID` (Foreign Key -> Property)
- `reported_by_id`: `UUID` (Foreign Key -> CustomUser)
- `amount`: `NUMERIC(12, 2)`
- `reference_last_4`: `VARCHAR(4)` (Deterministic user input / OCR index key)
- `evidence_file_url`: `VARCHAR(512)` (Stored receipt path link)
- `status`: `VARCHAR(30)` (Enum: `['PENDING_AI', 'APPROVED_AUTO', 'PENDING_MANUAL_REVIEW', 'APPROVED_MANUAL', 'REJECTED']`)
- `ai_confidence_score`: `NUMERIC(5, 2)` (Nullable, validation metadata)
- `created_at`: `TIMESTAMP`
