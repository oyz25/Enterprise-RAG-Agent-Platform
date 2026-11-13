# System Architecture & Engineering Design (`ARCHITECTURE.md`)

This document outlines the production architecture, multi-stage retrieval pipeline, engineering tradeoffs, security controls, and observability design of the **Enterprise RAG & Agent Platform**.

---

## 1. High-Level System Topology

The platform is deployed as a containerized 4-service stack orchestrated via Docker Compose, communicating over an isolated internal bridge network with persistent volumes for vector indices, relational chat state, and local HuggingFace model weights.

```mermaid
flowchart TB
    Client[Browser / API Consumer]

    subgraph Docker_Compose_Network [Docker Compose Bridge Network]
        Frontend["Next.js 16 Frontend<br/>(rag_frontend :3000)"]

        subgraph Backend_Service ["FastAPI Backend (rag_backend :8000)"]
            direction TB
            ObsMW["1. Outer: ObservabilityMiddleware<br/>(X-Request-ID, JSON Logs, P95 Latency)"]
            CorsMW["2. Middle: CORSMiddleware<br/>(Origin Allowlist)"]
            RateMW["3. Inner: RateLimitMiddleware<br/>(Sliding-Window Per-IP Quota)"]
            Guard["Security Layer<br/>(X-API-Key Auth + Input Guardrails)"]
            Router["Multi-Agent Intent Router & Tool Registry"]
            RAG["3-Stage Advanced RAG Engine"]
            Synth["Dual-Mode Citation Synthesizer"]

            ObsMW --> CorsMW --> RateMW --> Guard --> Router
            Router --> RAG --> Synth
        end

        Qdrant[("Qdrant Vector DB<br/>(rag_qdrant :6333)")]
        Postgres[("PostgreSQL 16<br/>(rag_postgres :5432)")]
    end

    Ollama["Optional Local Ollama / OpenAI Endpoint<br/>(host.docker.internal :11434)"]

    Client -->|"HTTP / SSE"| Frontend
    Client -->|"REST / SSE"| ObsMW
    Frontend -->|"POST /api/v1/agent/stream<br/>GET/DELETE /api/v1/sessions"| ObsMW
    RAG <-->|"384-d Cosine Search"| Qdrant
    Router <-->|"Session & Message State"| Postgres
    Synth -.->|"Optional LLM Synthesis"| Ollama