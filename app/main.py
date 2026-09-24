from fastapi import FastAPI
from app.routers import documents, chunking

app = FastAPI(
    title="Enterprise RAG & Agent Platform",
    description="Enterprise Private Knowledge Base & Multi-Agent Collaboration Platform",
    version="0.1.0"
)

# Register Routers
app.include_router(documents.router)
app.include_router(chunking.router)


@app.get("/")
def read_root():
    return {"message": "Welcome to Enterprise RAG & Agent Platform API"}


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "RAG-Agent-Engine",
        "version": "0.1.0"
    }