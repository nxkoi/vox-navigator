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
        self._default_speaker = os.path.join(
            os.path.dirname(__file__),
            "..",
            "assets",
            "speakers",
            "default_pt.wav"
        )
        self._default_speaker = os.path.abspath(self._default_speaker)
    
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
            
            # Initialize TTS with XTTS v2 model and device placement
            # XTTS v2 requires device to be specified during initialization
            device_str = str(self._torch_device)
            self._tts_model = TTS(
                model_name=self._model_name,
                progress_bar=True,
                gpu=(device_str != "cpu")
            )
            
            # Ensure model components are on the correct device
            # The TTS API handles device placement internally, but we verify
            if hasattr(self._tts_model, 'synthesizer') and hasattr(self._tts_model.synthesizer, 'to'):
                self._tts_model.synthesizer.to(device_str)
            
            self._model_loaded = True
            logger.info(f"XTTS v2 model loaded successfully on {self._torch_device}")
            
        except ImportError as e:
            # Só é erro de instalação se o próprio módulo TTS não existir
            if e.name == "TTS" or e.name.startswith("TTS."):
                raise EngineLoadError(
                    "Coqui TTS library not installed. Install with: pip install TTS"
                ) from e

            # Qualquer outro ImportError é erro REAL do XTTS
            raise EngineLoadError(
                f"XTTS internal ImportError: {type(e).__name__}: {e}"
            ) from e

        except Exception as e:
            # All other exceptions are runtime errors during model loading
            # Preserve the original error message and type
            raise EngineLoadError(
                f"Failed to load XTTS v2 model: {type(e).__name__}: {e}"
            ) from e
    
    def synthesize(
        self,
        text: str,
        output_path: Optional[str] = None
    ) -> str:
        """
        Synthesize speech from text using XTTS v2 and return the path to the audio file.

        XTTS v2 is a voice-cloning model and REQUIRES a reference speaker WAV file.
        """

        # 1. Validate text
        self.validate_text(text)

        # 2. Load model if needed
        if not self._model_loaded:
            self.load_model()

        if self._tts_model is None:
            raise SynthesisError("Model not loaded. Call load_model() first.")

        # 3. Resolve output path (AFTER model is confirmed loaded)
        # This ensures we don't create empty files if model loading fails
        if output_path is None:
            fd, output_path = tempfile.mkstemp(suffix=".wav", prefix="xtts_")
            os.close(fd)
        else:
            output_dir = os.path.dirname(os.path.abspath(output_path))
            if output_dir:
                os.makedirs(output_dir, exist_ok=True)
            output_path = os.path.abspath(output_path)

        # 4. Resolve default speaker (use the one defined in __init__)
        default_speaker = self._default_speaker

        if not os.path.exists(default_speaker):
            raise SynthesisError(
                f"Default speaker file not found: {default_speaker}. "
                "XTTS v2 requires a reference speaker WAV."
            )

        logger.debug(f"Synthesizing with XTTS v2")
        logger.debug(f"Text (preview): {text[:50]}")
        logger.debug(f"Speaker WAV: {default_speaker}")
        logger.debug(f"Output path: {output_path}")
        logger.debug(f"Device: {self._torch_device}")

        try:
            # 5. Perform XTTS v2 synthesis
            # IMPORTANT: XTTS must use tts_to_file with speaker_wav
            try:
                self._tts_model.tts_to_file(
                    text=text,
                    speaker_wav=default_speaker,
                    language="pt",
                    file_path=output_path,
                )
            except Exception as tts_error:
                # Preserve the original XTTS runtime error with full context
                # This could be: invalid speaker_wav, language mismatch, audio backend failure, etc.
                error_type = type(tts_error).__name__
                error_msg = str(tts_error)
                
                # Provide context-specific error messages for common issues
                if "speaker" in error_msg.lower() or "wav" in error_msg.lower():
                    raise SynthesisError(
                        f"XTTS synthesis failed: Invalid speaker reference. "
                        f"Error: {error_type}: {error_msg}. "
                        f"Speaker file: {default_speaker}"
                    ) from tts_error
                elif "language" in error_msg.lower():
                    raise SynthesisError(
                        f"XTTS synthesis failed: Language error. "
                        f"Error: {error_type}: {error_msg}. "
                        f"Requested language: pt-br"
                    ) from tts_error
                elif "audio" in error_msg.lower() or "backend" in error_msg.lower():
                    raise SynthesisError(
                        f"XTTS synthesis failed: Audio backend error. "
                        f"Error: {error_type}: {error_msg}"
                    ) from tts_error
                else:
                    # Generic XTTS runtime error - preserve original message and type
                    raise SynthesisError(
                        f"XTTS synthesis failed: {error_type}: {error_msg}"
                    ) from tts_error

            # 6. Validate output file
            if not os.path.exists(output_path):
                raise SynthesisError(f"Audio file was not created: {output_path}")

            file_size = os.path.getsize(output_path)
            if file_size == 0:
                raise SynthesisError(
                    f"Generated audio file is empty: {output_path}. "
                    "XTTS synthesis did not produce audio."
                )

            logger.debug(
                f"Audio generated successfully: {output_path} ({file_size} bytes)"
            )

            return output_path

        except SynthesisError:
            # Re-raise SynthesisError as-is (already has proper context)
            # Cleanup partial file on failure
            if 'output_path' in locals() and os.path.exists(output_path):
                try:
                    os.remove(output_path)
                except Exception:
                    pass
            raise
        except EngineLoadError:
            # Re-raise EngineLoadError as-is (model loading failure)
            # Cleanup partial file on failure
            if 'output_path' in locals() and os.path.exists(output_path):
                try:
                    os.remove(output_path)
                except Exception:
                    pass
            raise
        except Exception as e:
            # Cleanup partial file on failure
            if 'output_path' in locals() and os.path.exists(output_path):
                try:
                    os.remove(output_path)
                except Exception:
                    pass

            # Wrap unexpected errors but preserve original type and message
            raise SynthesisError(
                f"Unexpected error during XTTS synthesis: {type(e).__name__}: {e}"
            ) from e

