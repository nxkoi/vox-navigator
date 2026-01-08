"""
FastAPI application exposing the local XTTS engine.

Minimal HTTP API that wires POST /tts → EngineManager.synthesize()
"""

import os
import sys
from pathlib import Path

# Add parent directory to path to allow imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from core.engine_manager import EngineManager
from core.errors import SynthesisError, EngineLoadError, TTSError

# Initialize FastAPI app
app = FastAPI(title="Vox Navigator TTS Server")

# Shared EngineManager instance (singleton)
_engine_manager: EngineManager = None


def get_engine_manager() -> EngineManager:
    """Get or create the shared EngineManager instance."""
    global _engine_manager
    if _engine_manager is None:
        _engine_manager = EngineManager()
    return _engine_manager


# Request model
class TTSRequest(BaseModel):
    """Request body for TTS synthesis."""
    text: str = Field(..., min_length=1)


@app.post("/tts", response_class=FileResponse)
def synthesize_tts(request: TTSRequest) -> FileResponse:
    """
    POST /tts - Synthesize speech from text.
    
    Input: JSON { "text": "<string>" }
    Output: WAV file as audio/wav
    
    Returns HTTP 400 if text is missing/empty.
    Returns HTTP 500 if synthesis fails.
    """
    # Validate input: non-empty text
    text = request.text.strip()
    if not text:
        raise HTTPException(status_code=400, detail="Text cannot be empty")
    
    # Get shared EngineManager instance
    engine_manager = get_engine_manager()
    
    # Call EngineManager.synthesize() - this handles all TTS logic
    try:
        audio_path = engine_manager.synthesize(text=text)
        
        # Verify file was created
        if not os.path.exists(audio_path):
            raise HTTPException(
                status_code=500,
                detail=f"Audio file was not created: {audio_path}"
            )
        
        # Return WAV file as audio/wav
        return FileResponse(
            path=audio_path,
            media_type="audio/wav",
            filename=os.path.basename(audio_path)
        )
        
    except SynthesisError as e:
        raise HTTPException(status_code=500, detail=f"TTS synthesis failed: {str(e)}") from e
    except EngineLoadError as e:
        raise HTTPException(status_code=500, detail=f"TTS engine failed to load: {str(e)}") from e
    except TTSError as e:
        raise HTTPException(status_code=500, detail=f"TTS error: {str(e)}") from e
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error: {type(e).__name__}: {e}"
        ) from e


@app.get("/")
def root():
    """Health check endpoint."""
    return {"status": "ok", "service": "Vox Navigator TTS Server"}


@app.get("/health")
def health():
    """
    Health check endpoint with engine status.
    
    Returns:
        dict: Health status and engine initialization state
    """
    try:
        engine_manager = get_engine_manager()
        is_initialized = engine_manager.is_initialized()
        device_info = engine_manager.get_current_device()
        
        return {
            "status": "healthy",
            "engine_initialized": is_initialized,
            "device": device_info.type if device_info else None,
            "device_name": device_info.name if device_info else None
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": f"{type(e).__name__}: {e}"
        }


if __name__ == "__main__":
    """
    Run the FastAPI application with uvicorn.
    
    Usage:
        python api/app.py
        
    Or with uvicorn directly:
        uvicorn api.app:app --host 127.0.0.1 --port 8000
    """
    import uvicorn
    
    # Bind to localhost only (127.0.0.1)
    # Port 8000 is the default FastAPI port
    uvicorn.run(
        "api.app:app",
        host="0.0.0.0",
        port=8000,
        reload=False,  # Disable auto-reload for production-like behavior
        log_level="info"
    )
