"""
TTS engine manager.

This module provides the single point of control for TTS engine lifecycle
and device selection. It ensures that:

- Device detection is centralized
- Engine instantiation happens lazily
- A single shared engine instance is used per process
- Graceful fallback occurs when GPU initialization fails
- Explicit errors are raised when no engine can be initialized

The manager abstracts away vendor-specific details (CUDA, ROCm) and
provides a unified interface for the API layer.
"""

import hashlib
import logging
import os
import tempfile
import time
from typing import Optional

from core.device import detect_device, DeviceInfo
from core.errors import EngineLoadError, DeviceError, SynthesisError
from engines.xtts_engine import XTTSEngine

logger = logging.getLogger(__name__)


class EngineManager:
    """
    Manages TTS engine instances with lazy initialization and device selection.
    
    This class implements a singleton-like pattern where a single engine
    instance is shared across all requests. The engine is initialized on
    first use, not at import time.
    
    Device selection follows this priority:
    1. GPU (CUDA or ROCm) if available
    2. CPU fallback if GPU fails or is unavailable
    """
    
    _instance: Optional['EngineManager'] = None
    _engine: Optional[XTTSEngine] = None
    _device_info: Optional[DeviceInfo] = None
    _initialized: bool = False
    
    def __new__(cls):
        """
        Ensure only one EngineManager instance exists per process.
        """
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """
        Initialize the engine manager.
        
        Note: Engine is not loaded here. Use get_engine() for lazy initialization.
        """
        if not self._initialized:
            self._engine = None
            self._device_info = None
            self._initialized = True
    
    def get_device_info(self) -> DeviceInfo:
        """
        Get the detected device information.
        
        Returns:
            DeviceInfo: Information about the selected compute device
            
        Raises:
            DeviceError: If device detection fails completely
        """
        if self._device_info is None:
            try:
                self._device_info = detect_device()
                logger.info(
                    f"Device detected: {self._device_info.name} "
                    f"({self._device_info.type})"
                )
                if self._device_info.details:
                    logger.info(f"Device details: {self._device_info.details}")
            except Exception as e:
                logger.error(f"Device detection failed: {e}")
                raise DeviceError(f"Failed to detect compute device: {e}") from e
        
        return self._device_info
    
    def get_engine(self) -> XTTSEngine:
        """
        Get or initialize the TTS engine (lazy initialization).
        
        The engine is initialized on first call. If GPU initialization fails,
        the manager automatically falls back to CPU.
        
        Returns:
            XTTSEngine: Initialized TTS engine instance
            
        Raises:
            EngineLoadError: If engine initialization fails on all devices
        """
        if self._engine is not None:
            return self._engine
        
        device_info = self.get_device_info()
        
        # Try to initialize engine with detected device
        try:
            self._engine = self._initialize_engine(device_info)
            logger.info(f"Engine initialized successfully on {device_info.name}")
            return self._engine
        except Exception as e:
            logger.warning(
                f"Engine initialization failed on {device_info.name}: {e}"
            )
            
            # Fallback to CPU if GPU failed
            if device_info.type != "cpu":
                logger.info("Attempting CPU fallback...")
                try:
                    cpu_device = DeviceInfo(
                        type="cpu",
                        name="CPU",
                        torch_device="cpu",
                        details="CPU fallback after GPU failure"
                    )
                    self._engine = self._initialize_engine(cpu_device)
                    logger.info("Engine initialized successfully on CPU (fallback)")
                    self._device_info = cpu_device
                    return self._engine
                except Exception as cpu_error:
                    logger.error(f"CPU fallback also failed: {cpu_error}")
                    raise EngineLoadError(
                        f"Engine initialization failed on both {device_info.type} "
                        f"and CPU: {e}; CPU error: {cpu_error}"
                    ) from cpu_error
            else:
                # Already on CPU, no fallback possible
                raise EngineLoadError(
                    f"Engine initialization failed on CPU: {e}"
                ) from e
    
    def _initialize_engine(self, device_info: DeviceInfo) -> XTTSEngine:
        """
        Initialize a TTS engine for the given device.
        
        Args:
            device_info: Device information for engine initialization
            
        Returns:
            XTTSEngine: Initialized engine instance
            
        Raises:
            EngineLoadError: If engine initialization fails
        """
        try:
            engine = XTTSEngine(device=device_info.type)
            # Model loading will be implemented later
            # For now, engine is instantiated but not fully loaded
            logger.debug(
                f"Engine instance created for device: {device_info.type}"
            )
            return engine
        except Exception as e:
            raise EngineLoadError(
                f"Failed to create engine for device {device_info.type}: {e}"
            ) from e
    
    def synthesize(self, text: str, output_dir: Optional[str] = None) -> str:
        """
        Synthesize speech from text and return the path to the audio file.
        
        This is the main interface method for the API layer. It handles:
        - Engine initialization (lazy)
        - Text synthesis
        - Audio file generation
        - File path management
        
        Args:
            text: Input text to synthesize
            output_dir: Optional directory for output files. If None, uses
                       a temporary directory.
        
        Returns:
            str: Path to the generated WAV audio file
            
        Raises:
            EngineLoadError: If engine cannot be initialized
            SynthesisError: If synthesis fails
        """
        if not text or not text.strip():
            raise SynthesisError("Text input cannot be empty")
        
        engine = self.get_engine()
        
        # Determine output directory
        if output_dir is None:
            output_dir = tempfile.gettempdir()
        else:
            os.makedirs(output_dir, exist_ok=True)
        
        # Generate unique filename
        text_hash = hashlib.md5(text.encode()).hexdigest()[:8]
        timestamp = int(time.time())
        filename = f"tts_{timestamp}_{text_hash}.wav"
        output_path = os.path.join(output_dir, filename)
        
        # Synthesize audio using the engine
        try:
            # Call engine.synthesize() to perform actual TTS synthesis
            audio_path = engine.synthesize(text=text, output_path=output_path)
            
            logger.debug(f"Audio file created: {audio_path}")
            return audio_path
            
        except ImportError as e:
            # Só é erro de instalação se o módulo TTS não existir
            if e.name == "TTS" or e.name.startswith("TTS."):
                raise EngineLoadError(
                    "Coqui TTS library not installed. "
                    "Install with: pip install TTS"
                ) from e

            # Qualquer outro ImportError é erro REAL de runtime
            raise EngineLoadError(
                f"XTTS failed during import phase: {type(e).__name__}: {e}"
            ) from e


        except SynthesisError:
            # Erro de síntese real → propagar
            if 'output_path' in locals() and os.path.exists(output_path):
                try:
                    os.remove(output_path)
                except Exception:
                    pass
            raise

        except EngineLoadError:
            # Erro de carregamento real → propagar
            if 'output_path' in locals() and os.path.exists(output_path):
                try:
                    os.remove(output_path)
                except Exception:
                    pass
            raise

        except Exception as e:
            # ERRO REAL NÃO RELACIONADO À INSTALAÇÃO
            if 'output_path' in locals() and os.path.exists(output_path):
                try:
                    os.remove(output_path)
                except Exception:
                    pass

            raise SynthesisError(
                f"Unexpected TTS runtime error: {type(e).__name__}: {e}"
            ) from e
    
    def is_initialized(self) -> bool:
        """
        Check if the engine has been initialized.
        
        Returns:
            bool: True if engine is initialized, False otherwise
        """
        return self._engine is not None
    
    def get_current_device(self) -> Optional[DeviceInfo]:
        """
        Get the currently selected device information.
        
        Returns:
            DeviceInfo if device has been detected, None otherwise
        """
        return self._device_info
