"""
Base TTS engine interface.

This module defines the abstract base class that all Text-to-Speech engines
must implement. The interface is designed to be:

- Model-agnostic: Works with any TTS model (XTTS, VITS, etc.)
- Device-agnostic: No assumptions about GPU, CUDA, or ROCm
- File-based: Returns filesystem paths to generated audio files
- Production-oriented: Clear contracts and error expectations

Concrete implementations must handle:
- Model loading and initialization
- Text preprocessing (if needed)
- Audio synthesis
- Audio file writing (WAV format)
- Device-specific optimizations (internally)
"""

from abc import ABC, abstractmethod
from typing import Optional

from core.errors import SynthesisError, TTSError


class BaseTTSEngine(ABC):
    """
    Abstract base class for Text-to-Speech engines.
    
    This class defines the contract that all TTS engine implementations
    must follow. It ensures consistent behavior across different models
    and hardware configurations.
    
    Responsibilities:
    - Synthesize speech from text input
    - Generate audio files in WAV format
    - Handle errors gracefully
    - Work on any compute device (CPU, GPU via CUDA/ROCm)
    
    Non-responsibilities:
    - Device detection (handled by engine manager)
    - File path management (handled by engine manager)
    - HTTP request handling (handled by API layer)
    """
    
    def __init__(self, device: str = "cpu"):
        """
        Initialize the TTS engine.
        
        Args:
            device: Compute device identifier ('cuda', 'rocm', or 'cpu').
                   The engine should use this internally but not assume
                   any specific hardware capabilities.
        
        Note:
            Model loading may happen here or in a separate method,
            depending on the implementation.
        """
        self.device = device
        self._model_loaded = False
    
    @abstractmethod
    def synthesize(self, text: str, output_path: Optional[str] = None) -> str:
        """
        Synthesize speech from text and return the path to the audio file.
        
        This is the primary method that concrete engines must implement.
        It should:
        1. Validate and preprocess the input text
        2. Perform neural inference to generate audio
        3. Write the audio to a WAV file
        4. Return the filesystem path to that file
        
        Args:
            text: Input text to synthesize. Must be non-empty.
            output_path: Optional path where the audio file should be written.
                        If None, the engine should generate a unique path.
        
        Returns:
            str: Absolute filesystem path to the generated WAV audio file.
                 The file must exist and be readable when this method returns.
        
        Raises:
            SynthesisError: If synthesis fails for any reason, including:
                - Empty or invalid text input
                - Model not loaded
                - Inference failure
                - Audio file writing failure
                - Device-specific errors (e.g., GPU out of memory)
            TTSError: For other TTS-related errors
        
        Note:
            - The returned file must be in WAV format
            - The file should be complete and valid when returned
            - The engine is responsible for creating the output directory if needed
            - Concurrent calls should be safe if the implementation supports it
        """
        pass
    
    @abstractmethod
    def load_model(self, model_path: Optional[str] = None) -> None:
        """
        Load the TTS model into memory.
        
        This method should load the neural model and prepare it for inference.
        It may be called during initialization or lazily on first synthesis.
        
        Args:
            model_path: Optional path to model files. If None, the engine
                      should use a default or configured model path.
        
        Raises:
            EngineLoadError: If model loading fails, including:
                - Model files not found
                - Invalid model format
                - Insufficient memory
                - Device initialization failure
            TTSError: For other TTS-related errors
        
        Note:
            - This method should be idempotent (safe to call multiple times)
            - Model loading may be slow and should be done once
            - The engine should set _model_loaded = True on success
        """
        pass
    
    def is_model_loaded(self) -> bool:
        """
        Check if the model has been loaded.
        
        Returns:
            bool: True if model is loaded and ready for synthesis, False otherwise
        """
        return self._model_loaded
    
    def get_device(self) -> str:
        """
        Get the compute device identifier for this engine.
        
        Returns:
            str: Device identifier ('cuda', 'rocm', or 'cpu')
        """
        return self.device
    
    def validate_text(self, text: str) -> None:
        """
        Validate text input before synthesis.
        
        This is a helper method that concrete engines can use or override.
        It performs basic validation that applies to all engines.
        
        Args:
            text: Text to validate
        
        Raises:
            SynthesisError: If text is invalid (empty, too long, etc.)
        """
        if not text:
            raise SynthesisError("Text input cannot be empty")
        
        if not isinstance(text, str):
            raise SynthesisError(f"Text input must be a string, got {type(text)}")
        
        text_stripped = text.strip()
        if not text_stripped:
            raise SynthesisError("Text input cannot be empty or whitespace only")
        
        # Reasonable upper limit to prevent resource exhaustion
        # Concrete engines can override this if needed
        max_length = 10000  # characters
        if len(text_stripped) > max_length:
            raise SynthesisError(
                f"Text input exceeds maximum length of {max_length} characters"
            )