"""
Main FastAPI Application Entrypoint.
Initializes routers, static file mounting, CORS, and system health checks.
"""
from pathlib import Path
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.web.routes import api_router

app = FastAPI(
    title="AI Document Generation Engine",
    description="Intelligent PDF Analysis + Word Template Preservation + Automated DOCX Generation",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API endpoints
app.include_router(api_router)

# Mount Static UI
static_dir = Path(__file__).resolve().parent / "web" / "static"
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

@app.get("/")
async def serve_index():
    return FileResponse(static_dir / "index.html")

@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "gemini_configured": bool(settings.GEMINI_API_KEY),
        "ollama_model": settings.OLLAMA_MODEL,
        "memory_dir": str(settings.MEMORY_DIR)
    }
