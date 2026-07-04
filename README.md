# Aporte App

A mobile-first Fintech SaaS engineered to streamline, manage, and automate utility and property-management payments for residential complexes (condominiums). The platform leverages a robust asynchronous distributed architecture combined with intelligent AI agents to automate high-friction operational workflows.

---

## 🚀 Key Features

* **Mobile-First Core Financials:** Seamless management of residential expenses, utility splitting, and transaction accounting tailored for high-growth scalability.
* **AI-Driven Bank Reconciliation:** Powered by LangChain to parse real-world, unformatted bank statements and transaction inputs into clean, deterministic data models.
* **Context-Optimized Token Management:** Utilizes dynamic chunking and execution strategies to handle large financial datasets within LLM context window constraints.
* **Local-First Distributed Lab:** Containerized architecture that runs entirely via Docker, replicating production-grade workloads (queues, caching, and state) on a single local environment.

---

## 🛠️ Architecture & Tech Stack

This project is organized as a unified **Monorepo** to guarantee environment parity and developer efficiency:

* **Backend:** Python + Django REST Framework (DRF) handling core business logic, ORM mappings, and secure API endpoints.
* **Frontend:** Next.js / React for a responsive, mobile-first consumer experience.
* **AI Orchestration:** LangChain for managing agent workflows, structured Pydantic outputs, and evaluation benchmarks.
* **Infrastructure Core:** PostgreSQL as the primary transactional database, and Redis as the caching layer and asynchronous task broker.

---

## 📂 Project Structure

```text
aporte-app/
├── backend/          # Django REST Framework API & AI agent modules
├── frontend/         # Next.js mobile-first client application
├── infrastructure/   # Docker, local development configs, and future IaC (Terraform)
├── .gitignore        # Global git exclusion rules
└── README.md         # Project documentation