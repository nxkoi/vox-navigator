"""
Main FastAPI application for Vox Navigator TTS server.

Handles:
- HTTP API endpoints
- Request/response handling
- Server lifecycle management
"""

from fastapi import FastAPI
from api.tts import router as tts_router

app = FastAPI(title="Vox Navigator TTS Server")

app.include_router(tts_router)

@app.get("/")
def root():
    """Health check endpoint."""
    return {"status": "ok"}

@app.get("/health")
def health():
    """Health check endpoint."""
    return {"status": "healthy"}
