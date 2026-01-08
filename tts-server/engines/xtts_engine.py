"""
XTTS engine implementation.

This module implements the XTTS v2 (Coqui TTS) Text-to-Speech engine.
It handles:

- XTTS v2 model loading and initialization
- GPU/CPU inference using PyTorch
- Audio waveform generation
- Integration with audio writer utilities

The engine supports:
- CUDA (NVIDIA GPUs)
- ROCm (AMD GPUs via HIP)
- CPU fallback

Model: XTTS v2 from Coqui TTS
Default language: English (can be configured)
"""

import logging
import os
import tempfile
from typing import Optional

import torch

from engines.base import BaseTTSEngine
from core.errors import EngineLoadError, SynthesisError
from audio.writer import write_wav, DEFAULT_SAMPLE_RATE

logger = logging.getLogger(__name__)


class XTTSEngine(BaseTTSEngine):
    """
    XTTS v2 neural TTS engine implementation.
    
    This engine uses Coqui TTS XTTS v2 model for high-quality,
    multilingual text-to-speech synthesis.
    """
    
    def __init__(self, device: str = "cpu"):
        """
        Initialize XTTS engine.
        
        Args:
            device: Compute device ('cuda', 'rocm', or 'cpu').
                   Note: Both 'cuda' and 'rocm' map to torch.device('cuda')
                   since ROCm uses the CUDA API via HIP.
        
        Note:
            Model is not loaded here. Call load_model() explicitly or
            it will be loaded lazily on first synthesis.
        """
        super().__init__(device)
        self._tts_model = None
        self._torch_device = self._map_device(device)
        self._model_name = "tts_models/multilingual/multi-dataset/xtts_v2"
    
    def _map_device(self, device: str) -> torch.device:
        """
        Map device string to torch.device.
        
        Args:
            device: Device identifier ('cuda', 'rocm', or 'cpu')
        
        Returns:
            torch.device: PyTorch device object
        """
        if device in ("cuda", "rocm"):
            # Both CUDA and ROCm use torch.device('cuda')
            # ROCm exposes CUDA API via HIP
            if torch.cuda.is_available():
                return torch.device("cuda")
            else:
                logger.warning(
                    f"Device '{device}' requested but CUDA not available, "
                    "falling back to CPU"
                )
                return torch.device("cpu")
        else:
            return torch.device("cpu")
    
    def load_model(self, model_path: Optional[str] = None) -> None:
        """
        Load the XTTS v2 model into memory.
        
        This method loads the Coqui TTS XTTS v2 model and prepares it
        for inference. The model is downloaded automatically on first use
        if not already present.
        
        Args:
            model_path: Optional path to model files. If None, uses the
                      default XTTS v2 model from Coqui TTS.
        
        Raises:
            EngineLoadError: If model loading fails
        """
        if self._model_loaded:
            logger.debug("Model already loaded, skipping")
            return
        
        try:
            from TTS.api import TTS
            
            logger.info(f"Loading XTTS v2 model on device: {self._torch_device}")
            logger.info("This may take a few minutes on first run (model download)...")
            
            # Initialize TTS with XTTS v2 model
            self._tts_model = TTS(
                model_name=self._model_name,
                progress_bar=True
            )
            
            # Move model to appropriate device
            if hasattr(self._tts_model, 'to'):
                self._tts_model = self._tts_model.to(str(self._torch_device))
            
            self._model_loaded = True
            logger.info(f"XTTS v2 model loaded successfully on {self._torch_device}")
            
        except ImportError as e:
            raise EngineLoadError(
                "Coqui TTS library not installed. "
                "Install with: pip install TTS"
            ) from e
        except Exception as e:
            raise EngineLoadError(
                f"Failed to load XTTS v2 model: {e}"
            ) from e
    
    def synthesize(
        self,
        text: str,
        output_path: Optional[str] = None
    ) -> str:
        """
        Synthesize speech from text and return the path to the audio file.
        
        This method performs the complete synthesis pipeline:
        1. Validates input text
        2. Loads model if not already loaded (lazy loading)
        3. Generates audio waveform using XTTS v2
        4. Writes audio to WAV file
        5. Returns file path
        
        Args:
            text: Input text to synthesize. Must be non-empty.
            output_path: Optional path where the audio file should be written.
                       If None, a temporary file is created.
        
        Returns:
            str: Absolute filesystem path to the generated WAV audio file.
        
        Raises:
            SynthesisError: If synthesis fails for any reason
        """
        # Validate text input
        self.validate_text(text)
        
        # Load model if not already loaded (lazy loading)
        if not self._model_loaded:
            self.load_model()
        
        if self._tts_model is None:
            raise SynthesisError("Model not loaded. Call load_model() first.")
        
        # Generate output path if not provided
        if output_path is None:
            fd, output_path = tempfile.mkstemp(suffix='.wav', prefix='xtts_')
            os.close(fd)
        else:
            # Ensure output directory exists
            output_dir = os.path.dirname(os.path.abspath(output_path))
            if output_dir:
                os.makedirs(output_dir, exist_ok=True)
            output_path = os.path.abspath(output_path)
        
        try:
            logger.debug(f"Synthesizing text: {text[:50]}...")
            logger.debug(f"Output path: {output_path}")
            logger.debug(f"Device: {self._torch_device}")
            
            # Generate audio waveform using XTTS
            # tts() returns the audio array, which we'll write using our writer
            audio_waveform = self._tts_model.tts(
                text=text,
                speaker_wav=None,  # Use default voice
                language="en"  # Default to English, can be made configurable
            )
            
            # Convert to numpy array if needed and ensure it's a 1D array
            import numpy as np
            if not isinstance(audio_waveform, np.ndarray):
                audio_waveform = np.array(audio_waveform)
            
            # Flatten to 1D if needed (handle multi-channel audio)
            if audio_waveform.ndim > 1:
                audio_waveform = audio_waveform.flatten()
            
            # Get sample rate from TTS model (XTTS v2 uses 24000 Hz)
            # We'll use the model's sample rate or default
            sample_rate = getattr(self._tts_model, 'output_sample_rate', 24000)
            
            # Write audio to WAV file using our audio writer
            output_path = write_wav(
                audio_data=audio_waveform,
                output_path=output_path,
                sample_rate=sample_rate,
                channels=1  # Mono
            )
            
            # Verify file was created and is non-empty
            if not os.path.exists(output_path):
                raise SynthesisError(f"Audio file was not created: {output_path}")
            
            file_size = os.path.getsize(output_path)
            if file_size == 0:
                raise SynthesisError(f"Generated audio file is empty: {output_path}")
            
            logger.debug(f"Audio generated successfully: {output_path} ({file_size} bytes)")
            
            return output_path
            
        except Exception as e:
            # Clean up partial file on error
            if os.path.exists(output_path):
                try:
                    os.remove(output_path)
                except Exception:
                    pass
            
            if isinstance(e, SynthesisError):
                raise
            else:
                raise SynthesisError(
                    f"XTTS synthesis failed: {e}"
                ) from e
