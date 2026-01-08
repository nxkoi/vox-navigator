"""
Error definitions for TTS server.

Defines custom exceptions for TTS processing errors.
"""

class TTSError(Exception):
    """Base exception for TTS errors."""
    pass

class EngineLoadError(TTSError):
    """Raised when engine fails to load."""
    pass

class SynthesisError(TTSError):
    """Raised when synthesis fails."""
    pass

class DeviceError(TTSError):
    """Raised when device detection or selection fails."""
    pass
