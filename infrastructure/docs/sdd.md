# Software Design Document (SDD) - Aporte App
**Project Phase:** MVP / Proof of Concept (Local Distributed Lab)  
**Target Architecture:** Multi-tenant Asynchronous Fintech SaaS  

---

## 1. System Overview & Business Goals

### 1.1 Business Objective (Aporte Core)
Aporte is a mobile-first Fintech SaaS engineered to manage and automate utility and property-management payments for residential complexes (condominiums) in Venezuela. The primary product goal is to eliminate the high-friction, error-prone operational bottleneck faced by property managers: manual verification and data entry of bank transfers and "Pago Móvil" reported by residents.

### 1.2 Core Architectural Challenges
* **Multi-tenancy:** Complete logical isolation between independent residential clusters (e.g., "Los Sauces" vs. "Ávila") sharing the same compute and database instances.
* **Deterministic AI Automation:** Leveraging Large Language Models (LLMs) via LangChain to parse unformatted financial data chunks without introducing hallucinations or unpredictable states into the financial ledger.
* **Resilience:** Preventing system-wide failures if external AI providers or orchestrators experience high latencies or service blackouts.

---

## 2. Security, Authentication & Multi-Tenancy

To balance a frictionless experience for day-to-day users with enterprise-grade security for financial operators, the system enforces strict segregation at both the authentication and data layers.

### 2.1 Bifurcated Authentication Flows
The platform implements two entirely separate authorization paths inside Django REST Framework (DRF) and Next.js:

1. **Resident/Neighbor Profile (Low Friction):**
   * **Mechanism:** Passwordless login using a combination of **Cédula de Identidad** (National ID) and **Phone Number**.
   * **Authorization Level:** Limited strictly to reading their own properties' balance, historical ledger, and accessing the "Report Payment" module. They hold no visibility over global condominium balances or configuration parameters.
2. **Administrator Profile (High Security):**
   * **Mechanism:** Standard Email + Strong Password combinations, reinforced with mandatory **Two-Factor Authentication (2FA)**.
   * **Verification Flow:** Upon successful password verification, an asynchronous worker dispatches a temporary, 5-minute One-Time Password (OTP) via Redis to the Admin's registered device. The frontend session is locked behind a verification screen until the OTP is validated in the backend.

### 2.2 Multi-Tenant Data Isolation Strategy
Aporte employs a **Shared Database, Isolated Schemas / Shared Schema with Tenant Discriminator** design inside PostgreSQL to map distinct real estate entities.

* **Tenant Resolution:** The Next.js frontend captures the target cluster context via subdomains or route prefixes (e.g., `lossauces.aporte.com`).
* **API Isolation Contract:** Every HTTP request dispatched to the DRF API must contain a mandatory custom header: `X-Tenant-ID: <tenant-uuid>`.
* **Backend Middleware Enforcement:** A global scoping middleware intercepts inbound requests, validates the cryptographic token, and enforces a strict structural filter on all active ORM queries (`QuerySet.filter(tenant_id=current_tenant)`), ensuring cross-tenant data leaks are mathematically impossible.

---

## 3. Asynchronous AI Bank Reconciliation Pipeline

### 3.1 UX/UI Ingest & Client-Side Processing
To eliminate manual data entry, the system uses a hybrid approach to transform physical visual evidence into structured strings.

1. **Native Hardware Access:** The mobile-first Next.js UI uses native standard HTML5 capture mechanisms (`<input type="file" accept="image/*">`) to trigger native file explorer windows in desktop environments (Windows/macOS) and native camera/gallery drawers on mobile platforms (iOS/Android).
2. **Client-Side Optical Character Recognition (OCR):** Selected receipts are processed entirely within the user's browser device using `Tesseract.js` (compiled to WebAssembly). 
3. **Reactive Form Fields:**
   * **Scenario A (Success):** If the client-side OCR parses text matching standard banking transaction patterns via local Regular Expressions, it dynamically autofills a visible `reference_last_4` placeholder field.
   * **Scenario B (Degraded):** If the receipt image is blurred or low-light, the client-side engine fails silently without blocking the interface. The `reference_last_4` input is instantly unlocked for standard, manual key-in input from the user.
4. **Validation Constraint:** The payload layout explicitly demands both the physical `evidence_file` image and the structured `reference_last_4` string before enabling form submission.

### 3.2 Data Flow & Deterministic LangChain Execution
Once data hits the backend, the processing is offloaded to a background task runner to handle long-running LLM completions gracefully.

* **Data Masking (Privacy Mitigations):** Before passing the raw text strings to external LLM providers, Django runs a local sanitization pipeline using localized regex filters to strip Personally Identifiable Information (PII) like full names or bank account prefixes, substituting them with internal deterministic placeholder keys (`[CLIENT_A]`, `[ID_A]`).
* **Context Window Strategy:** Large unformatted bank statement strings are segmented into targeted data chunks via LangChain text splitters. The agent implements a Map-Reduce structural flow to parse groups of transactions iteratively without exhausting context windows.
* **Guaranteed Determinism:** The agent model parameters force a `temperature = 0`. LangChain enforces structural serialization constraints using **Pydantic Model Validations**. If the LLM output deviates from the strict structural schema layout defined for financial items, the payload fails structural validation checks before making any state updates.
* **Collision Handling & Context Resemblance:** In massive residential sectors where identical final reference chains match (e.g., two neighbors submitting different payments both ending in reference `4589`), the backend crosses reference tokens with the metadata inside the authenticated resident's profile (Cédula, specific phone origin, or contextual names found inside the enmasked image) to automatically and safely resolve the account ownership.

### 3.3 Resilience & Graceful Performance Degradation
The infrastructure treats external AI connectivity errors as expected events, ensuring zero operational downtime for the core business entity.

* **Exponential Backoff:** If the AI agent worker throws connectivity errors (`HTTP 503` or timeout thresholds), the Redis task pipeline retains the state and automatically schedules re-execution loops with randomized backoff parameters.
* **Degraded Manual Fallback:** If API failures persist outside safe operational boundaries, the backend automatically sets the transaction status flags to `PENDING_MANUAL_REVIEW`. The record is moved out of the automation loop and appended to a specialized manual ledger inside the administrator's operational interface, allowing standard manual click-to-approve execution.

---

## 4. Property Census Ingest & Outbound Notifications

### 4.1 Coproprietor Ingest Module (Onboarding)
To guarantee the data completeness needed for the passwordless strategy, the system provides flexible, high-fidelity intake mechanics for administrators.

* **Individual Entry:** A reactive Next.js form utilizing strict, normalized real estate dropdown fields (`Torre` ➔ `Piso` ➔ `Apartamento`) to ensure data sanitization.
* **Bulk Ingest Pipeline (Excel/CSV):** Administrators can leverage a structured batch ingestion tool. The frontend reads the file locally, rendering an interactive structural table with instant cell-by-cell data type verification before dispatching a `Bulk Create` transaction payload to the backend database layer.

### 4.2 Outbound Notification Channels (Frictionless SMS)
The platform prioritizes SMS over standard mobile applications or push notifications to optimize delivery and minimize user friction. By deploying a mobile-responsive web platform accessible via standard mobile browsers, the system guarantees 100% device compatibility without forcing users to download application packages from digital stores.

* **Message Structure Constraint:** Messages must strictly fit within the standard 160-character single-SMS threshold to minimize operational routing costs.
* **Dynamic Query-Param Pre-loading (Deep Linking):** To maintain the passwordless paradigm with minimal user friction, notification links are synthesized dynamically, appending user credentials directly into the URL parameters.
* **Deep Linking Flow:** When an SMS is received (e.g., "Your Avila condominium bill is ready. Tap to view and report your payment: http://aporte.com/login?c=123456&t=04125555555"), tapping the link opens the default mobile browser. The Next.js framework extracts 'c' (Cédula) and 't' (Phone) from the active URL query state, automatically injects values into the form fields, and presents a pre-filled layer requiring a single-tap authorization.

### 4.3 In-House URL Shortener Technical Specification
To decouple the platform from third-party routing dependencies and optimize infrastructure costs, the Django backend implements an internal URL shortening utility.

* **Database Schema (`ShortURL`):** A high-performance lookup table mapping a unique short alphanumeric token directly to the target tenant destination URL string.
* **Token Generation Algorithm (Base62 Encoding):** The system avoids utilizing standard incremental integers or heavy UUIDs for public routing keys. It converts internal surrogate keys or hashes into a Base62 alphabet (`[a-zA-Z0-9]`). A 5-character token constraint yields 62^5 = 916,132,832 discrete permutations, guaranteeing minimal payload footprints within the 160-character SMS limit.
* **Caching Layer Isolation:** To protect the primary transactional PostgreSQL instance from redundant redirect I/O bottlenecks during mass monthly billing notifications, successfully resolved tokens are cached in **Redis** with an expiration window, enabling sub-millisecond redirection operations directly from memory.