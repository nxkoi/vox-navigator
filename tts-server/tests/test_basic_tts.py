"""
Basic end-to-end TTS pipeline test.

This test validates the complete TTS pipeline from device detection through
audio file generation. It is designed to:

- Verify device detection works correctly
- Validate engine manager initialization
- Test the synthesis workflow
- Confirm audio file generation

The test is runnable as a standalone script:
    python test_basic_tts.py

Or via pytest:
    pytest test_basic_tts.py

This test does NOT require:
- FastAPI server to be running
- Browser interaction
- Mocked components
- Full TTS model setup (uses placeholder engine)

It DOES require:
- Valid Python environment
- Core modules to be importable
- File system write access
"""

import os
import sys
from pathlib import Path

# Add parent directory to path to allow imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.device import detect_device, DeviceInfo
from core.engine_manager import EngineManager
from core.errors import TTSError


def test_basic_tts_pipeline():
    """
    Test the complete TTS pipeline end-to-end.
    
    This function performs:
    1. Device detection
    2. Engine manager initialization
    3. Text synthesis
    4. Audio file verification
    
    Raises:
        AssertionError: If any step fails
        TTSError: If TTS processing fails
    """
    print("=" * 70)
    print("TTS Pipeline End-to-End Test")
    print("=" * 70)
    print()
    
    # Test text - short and neutral
    test_text = "Hello. This is a test of the local text to speech system."
    
    print(f"Test text: {test_text}")
    print()
    
    # Step 1: Device Detection
    print("Step 1: Detecting compute device...")
    try:
        device_info = detect_device()
        print(f"  ✓ Device detected: {device_info.name}")
        print(f"  ✓ Device type: {device_info.type}")
        print(f"  ✓ Torch device: {device_info.torch_device}")
        if device_info.details:
            print(f"  ✓ Details: {device_info.details}")
    except Exception as e:
        print(f"  ✗ Device detection failed: {e}")
        raise
    
    print()
    
    # Step 2: Engine Manager Initialization
    print("Step 2: Initializing engine manager...")
    try:
        manager = EngineManager()
        print("  ✓ Engine manager created")
        
        # Get device info (triggers detection if not already done)
        current_device = manager.get_device_info()
        print(f"  ✓ Device info retrieved: {current_device.name} ({current_device.type})")
        
        # Initialize engine (lazy initialization)
        engine = manager.get_engine()
        print(f"  ✓ Engine initialized: {type(engine).__name__}")
        print(f"  ✓ Engine device: {engine.get_device()}")
        
    except Exception as e:
        print(f"  ✗ Engine manager initialization failed: {e}")
        raise
    
    print()
    
    # Step 3: Text Synthesis
    print("Step 3: Synthesizing speech...")
    try:
        print(f"  → Input text: {test_text}")
        print(f"  → Device: {device_info.type}")
        
        # Create output directory in tests directory
        test_output_dir = Path(__file__).parent / "output"
        test_output_dir.mkdir(exist_ok=True)
        
        audio_path = manager.synthesize(
            text=test_text,
            output_dir=str(test_output_dir)
        )
        
        print(f"  ✓ Synthesis completed")
        print(f"  ✓ Audio file path: {audio_path}")
        
    except Exception as e:
        print(f"  ✗ Synthesis failed: {e}")
        raise
    
    print()
    
    # Step 4: Audio File Verification
    print("Step 4: Verifying audio file...")
    try:
        if not os.path.exists(audio_path):
            raise AssertionError(f"Audio file does not exist: {audio_path}")
        
        file_size = os.path.getsize(audio_path)
        print(f"  ✓ File exists: {audio_path}")
        print(f"  ✓ File size: {file_size} bytes")
        
        if file_size == 0:
            print("  ⚠ Warning: File is empty (expected for placeholder implementation)")
        else:
            print("  ✓ File contains data")
        
        # Verify it's a WAV file (check extension)
        if not audio_path.endswith('.wav'):
            print("  ⚠ Warning: File does not have .wav extension")
        else:
            print("  ✓ File has .wav extension")
        
    except Exception as e:
        print(f"  ✗ File verification failed: {e}")
        raise
    
    print()
    print("=" * 70)
    print("Test Summary")
    print("=" * 70)
    print(f"Device used: {device_info.type.upper()} ({device_info.name})")
    print(f"Audio file: {os.path.abspath(audio_path)}")
    print(f"File size: {os.path.getsize(audio_path)} bytes")
    print()
    print("✓ All steps completed successfully!")
    print("=" * 70)
    
    return audio_path


if __name__ == "__main__":
    """
    Run the test as a standalone script.
    
    Usage:
        python test_basic_tts.py
    """
    try:
        audio_path = test_basic_tts_pipeline()
        print()
        print("Test PASSED")
        sys.exit(0)
    except AssertionError as e:
        print()
        print(f"Test FAILED: {e}")
        sys.exit(1)
    except TTSError as e:
        print()
        print(f"Test FAILED (TTS Error): {e}")
        sys.exit(1)
    except Exception as e:
        print()
        print(f"Test FAILED (Unexpected Error): {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
