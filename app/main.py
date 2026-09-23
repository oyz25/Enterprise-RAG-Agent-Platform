from fastapi import FastAPI

app = FastAPI(
    title="Enterprise RAG & Agent Platform",
    description="Enterprise Private Knowledge Base and Multi-Agent Collaboration Platform API",
    version="0.1.0"
)

@app.get("/")
def read_root():
    return {"message": "Welcome to Enterprise RAG & Agent Platform"}

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "RAG-Agent-Engine",
        "version": "0.1.0"
    }