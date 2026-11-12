from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.database import engine, Base
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
    agent
)

# Auto-create PostgreSQL database tables on startup
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Enterprise RAG & Agent Platform",
    description="Enterprise Private Knowledge Base & Multi-Agent Collaboration Platform",
    version="0.3.0"
)

# Enable CORS for Next.js frontend integration
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


@app.get("/")
def read_root():
    return {"message": "Welcome to Enterprise RAG & Agent Platform API"}


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "RAG-Agent-Engine",
        "version": "0.3.0"
    }