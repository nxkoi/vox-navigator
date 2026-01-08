"""
Audio file writing utilities.

This module provides functions for writing audio waveform data to WAV files
on disk. It is designed to be:

- Engine-agnostic: Works with any audio source
- Format-specific: WAV format only
- Reliable: Never returns partial or corrupted files
- Simple: Minimal dependencies, clear interface

The module handles:
- Converting raw audio data (numpy arrays or lists) to WAV format
- Writing to temporary or specified file paths
- Ensuring valid, playable WAV files
- Error handling and cleanup

Default audio characteristics:
- Format: WAV (PCM)
- Channels: Mono (1 channel)
- Sample rate: 22050 Hz (configurable)
- Bit depth: 16-bit
"""

import os
import tempfile
import wave
from typing import Union, Optional, List

from core.errors import TTSError


class AudioWriteError(TTSError):
    """Raised when audio file writing fails."""
    pass


# Default audio parameters
DEFAULT_SAMPLE_RATE = 22050  # Hz
DEFAULT_CHANNELS = 1  # Mono
DEFAULT_SAMPLE_WIDTH = 2  # 16-bit (2 bytes per sample)


def write_wav(
    audio_data: Union[List[float], List[int], 'numpy.ndarray'],
    output_path: Optional[str] = None,
    sample_rate: int = DEFAULT_SAMPLE_RATE,
    channels: int = DEFAULT_CHANNELS
) -> str:
    """
    Write audio waveform data to a WAV file.
    
    This function converts raw audio samples to a valid WAV file and writes
    it to disk. The function ensures the file is complete and valid before
    returning the path.
    
    Args:
        audio_data: Audio samples as:
                   - List of floats (normalized to [-1.0, 1.0])
                   - List of integers (16-bit range: -32768 to 32767)
                   - NumPy array (will be converted to list)
        output_path: Optional path where the WAV file should be written.
                     If None, a temporary file is created in the system temp
                     directory with a unique name.
        sample_rate: Sample rate in Hz. Default is 22050 Hz.
        channels: Number of audio channels. Default is 1 (mono).
                 Must be 1 or 2 (stereo).
    
    Returns:
        str: Absolute filesystem path to the written WAV file.
             The file is guaranteed to exist and be valid when returned.
    
    Raises:
        AudioWriteError: If writing fails for any reason, including:
            - Invalid audio data
            - File system errors
            - Invalid parameters
        TTSError: For other TTS-related errors
    
    Note:
        - The output file is always overwritten if it exists
        - If writing fails, any partial file is cleaned up
        - The function validates audio data before writing
        - NumPy arrays are automatically converted to lists
    """
    # Validate parameters
    if sample_rate <= 0:
        raise AudioWriteError(f"Invalid sample rate: {sample_rate} Hz")
    
    if channels not in (1, 2):
        raise AudioWriteError(f"Unsupported channel count: {channels} (must be 1 or 2)")
    
    if not audio_data:
        raise AudioWriteError("Audio data cannot be empty")
    
    # Convert numpy array to list if needed
    try:
        import numpy as np
        if isinstance(audio_data, np.ndarray):
            audio_data = audio_data.tolist()
    except ImportError:
        # NumPy not available, assume it's already a list
        pass
    
    # Validate audio data type
    if not isinstance(audio_data, (list, tuple)):
        raise AudioWriteError(
            f"Audio data must be a list, tuple, or numpy array, got {type(audio_data)}"
        )
    
    # Determine output path
    if output_path is None:
        # Create temporary file
        fd, output_path = tempfile.mkstemp(suffix='.wav', prefix='tts_')
        os.close(fd)  # Close file descriptor, we'll open it with wave module
    else:
        # Ensure output directory exists
        output_dir = os.path.dirname(os.path.abspath(output_path))
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.abspath(output_path)
    
    # Convert audio data to 16-bit PCM bytes
    try:
        pcm_bytes = _audio_to_pcm_bytes(audio_data)
    except Exception as e:
        raise AudioWriteError(f"Failed to convert audio data to PCM: {e}") from e
    
    # Write WAV file
    try:
        _write_wav_file(
            output_path=output_path,
            pcm_data=pcm_bytes,
            sample_rate=sample_rate,
            channels=channels
        )
    except Exception as e:
        # Clean up partial file on error
        if os.path.exists(output_path):
            try:
                os.remove(output_path)
            except Exception:
                pass
        raise AudioWriteError(f"Failed to write WAV file to {output_path}: {e}") from e
    
    # Verify file was written successfully
    if not os.path.exists(output_path):
        raise AudioWriteError(f"WAV file was not created at {output_path}")
    
    if os.path.getsize(output_path) == 0:
        os.remove(output_path)
        raise AudioWriteError(f"WAV file is empty at {output_path}")
    
    return output_path


def _audio_to_pcm_bytes(audio_data: List[Union[float, int]]) -> bytes:
    """
    Convert audio samples to 16-bit PCM bytes.
    
    Handles both normalized float arrays ([-1.0, 1.0]) and integer arrays
    (16-bit range: -32768 to 32767).
    
    Args:
        audio_data: List of audio samples (floats or integers)
    
    Returns:
        bytes: 16-bit PCM audio data (little-endian)
    
    Raises:
        AudioWriteError: If conversion fails
    """
    pcm_samples = []
    
    for sample in audio_data:
        # Handle float samples (normalized to [-1.0, 1.0])
        if isinstance(sample, float):
            # Clamp to valid range
            sample = max(-1.0, min(1.0, sample))
            # Convert to 16-bit integer
            pcm_sample = int(sample * 32767)
        # Handle integer samples (assumed to be in 16-bit range)
        elif isinstance(sample, int):
            # Clamp to 16-bit range
            pcm_sample = max(-32768, min(32767, sample))
        else:
            raise AudioWriteError(
                f"Invalid sample type: {type(sample)} (must be float or int)"
            )
        
        pcm_samples.append(pcm_sample)
    
    # Convert to bytes (little-endian, 16-bit signed integers)
    pcm_bytes = b''.join(
        pcm_sample.to_bytes(2, byteorder='little', signed=True)
        for pcm_sample in pcm_samples
    )
    
    return pcm_bytes


def _write_wav_file(
    output_path: str,
    pcm_data: bytes,
    sample_rate: int,
    channels: int
) -> None:
    """
    Write PCM audio data to a WAV file.
    
    Args:
        output_path: Path where the WAV file should be written
        pcm_data: 16-bit PCM audio data as bytes
        sample_rate: Sample rate in Hz
        channels: Number of audio channels (1 or 2)
    
    Raises:
        AudioWriteError: If writing fails
    """
    try:
        with wave.open(output_path, 'wb') as wav_file:
            # Set WAV file parameters
            wav_file.setnchannels(channels)
            wav_file.setsampwidth(DEFAULT_SAMPLE_WIDTH)  # 16-bit = 2 bytes
            wav_file.setframerate(sample_rate)
            
            # Write audio data
            wav_file.writeframes(pcm_data)
    except Exception as e:
        raise AudioWriteError(f"Failed to write WAV file: {e}") from e
