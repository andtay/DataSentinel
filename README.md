# 🛡️ DataSentinel: Agentic API Ingestion & Validation Framework

**DataSentinel** is a modular framework designed to drastically accelerate the software development lifecycle in Data Science environments. Leveraging the autonomous reasoning capabilities of **IBM Bob**, the system automates the creation of ingestion, validation, and documentation layers for APIs, eliminating human error and ensuring data integrity.

## 🚀 The Problem
Data Scientists and Engineers spend up to 80% of their time on "data plumbing": reading API documentation, writing manual data models, and debugging unexpected breaks caused by **Schema Drift**.

## 🧠 The Agentic Solution
DataSentinel uses **IBM Bob** as a proactive architect that:
1.  **Scans & Maps:** Analyzes any endpoint (REST/GraphQL) and auto-generates robust data contracts using **Pydantic V2**.
2.  **Guarantees Quality:** Implements a real-time validation layer to catch inconsistencies before they hit the processing pipeline.
3.  **Accelerates Development:** Instantly creates **Mock Factories** to allow parallel development without dependency on live APIs.
4.  **Self-Documents:** Generates technical documentation and output interfaces via **FastAPI** on the fly.

## 🛠️ Tech Stack
* **Agentic Engine:** IBM Bob
* **Validation:** Pydantic V2 (Strict Mode)
* **Networking:** HTTPX (Asynchronous)
* **API Interface:** FastAPI
* **Testing & Mocks:** Polyfactory / Pytest
* **Logging:** Loguru

## 🏗️ Architecture
DataSentinel follows a **Provider Pattern** to remain protocol-agnostic:
- `core/`: Base logic for retries, authentication, and logging.
- `providers/`: Specialized adapters for REST, GraphQL, and Webhooks.
- `schemas/`: Auto-generated Pydantic models serving as the "Source of Truth".
- `app/`: FastAPI wrapper to expose validated data as a service.

## 🗺️ Project Roadmap

### Phase 1: Foundation (Hackathon MVP)
- [ ] Core **BaseProvider** architecture with `httpx` async support.
- [ ] Automated **Pydantic V2** model generation from JSON samples.
- [ ] Basic REST support (GET/POST) with API Key/Bearer authentication.
- [ ] Integrated **FastAPI** wrapper for real-time data serving.

### Phase 2: Resilience & Complexity
- [ ] **Schema Drift Detection**: Automatic alerts and impact reports when API structures change.
- [ ] **Advanced Pagination**: Support for offset, limit, and cursor-based navigation.
- [ ] **Mock Factory**: One-click synthetic data generation using `polyfactory`.
- [ ] OAuth2 session management and token refreshing.

### Phase 3: Expansion (Future)
- [ ] **GraphQL Adapter**: Native support for complex queries, fragments, and mutations.
- [ ] **Data Profiling**: Automatic statistical summaries (null counts, outliers, distributions).
- [ ] **Event-Driven Ingestion**: Webhook listeners for real-time data streams.
- [ ] **Cloud-Native Deployment**: One-click Dockerization for AWS/Azure/GCP.

## ⚖️ License
This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.

## 👥 Team
- Andrew Rober Taylor - *Lead Data Architect & AI Automation* Focus: Designing agentic data ingestion pipelines, schema validation with Pydantic, and bridging the gap between raw API data and production-ready Data Science environments.
- Vicente García Sánchez - *Reliability & Integration Engineer* Focuses on robust API consumption, error handling strategies (retries/backoff), and automated testing suites.
