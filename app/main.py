from fastapi import FastAPI
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
    advanced_search
)

app = FastAPI(
    title="Enterprise RAG & Agent Platform",
    description="Enterprise Private Knowledge Base & Multi-Agent Collaboration Platform",
    version="0.2.0"
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


@app.get("/")
def read_root():
    return {"message": "Welcome to Enterprise RAG & Agent Platform API"}


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "RAG-Agent-Engine",
        "version": "0.2.0"
    }