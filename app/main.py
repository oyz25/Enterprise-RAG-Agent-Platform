from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.database import engine, Base
from app.middleware.observability import ObservabilityMiddleware
from app.middleware.rate_limiter import RateLimitMiddleware
from app.routers import (
    documents,
    chunking,
    ingestion,
    search,
    rag,
    sparse_search,
    hybrid_search,
    rerank,
    compression,
    advanced_search,
    agent,
    sessions,
    evaluation,
    metrics,
)

# Auto-create PostgreSQL database tables on startup
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Enterprise RAG & Agent Platform",
    description="Production-Ready Private Knowledge Base & Multi-Agent Collaboration Platform",
    version="1.0.0",
)

# 1. Inner: Per-IP Sliding-Window Rate Limiter
app.add_middleware(RateLimitMiddleware)

# 2. Middle: CORS Policy for Next.js Frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 3. Outer: Structured JSON Access Logs, Correlation ID & Latency Telemetry
app.add_middleware(ObservabilityMiddleware)

# Register Routers
app.include_router(documents.router)
app.include_router(chunking.router)
app.include_router(ingestion.router)
app.include_router(search.router)
app.include_router(rag.router)
app.include_router(sparse_search.router)
app.include_router(hybrid_search.router)
app.include_router(rerank.router)
app.include_router(compression.router)
app.include_router(advanced_search.router)
app.include_router(agent.router)
app.include_router(sessions.router)
app.include_router(evaluation.router)
app.include_router(metrics.router)


@app.get("/")
def read_root():
    return {
        "message": "Welcome to Enterprise RAG & Agent Platform API",
        "version": "1.0.0",
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "RAG-Agent-Engine",
        "version": "1.0.0",
    }