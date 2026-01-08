"""
Device detection and hardware abstraction.

This module is responsible for detecting the available compute device
used for Text-to-Speech inference.

Supported backends:
- NVIDIA GPUs via CUDA
- AMD GPUs via ROCm (HIP)
- CPU fallback

The rest of the application must NOT assume any vendor-specific APIs.
All hardware decisions must be centralized here.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class DeviceInfo:
    """
    Describes the detected compute device.
    """
    type: str            # "cuda", "rocm", or "cpu"
    name: str            # Human-readable device name
    torch_device: str    # Torch device string (e.g. "cuda", "cpu")
    details: Optional[str] = None


def detect_device() -> DeviceInfo:
    """
    Detect the best available compute device.

    Detection order:
    1. NVIDIA GPU via CUDA
    2. AMD GPU via ROCm (HIP)
    3. CPU fallback

    Returns:
        DeviceInfo: immutable description of the selected device
    """
    try:
        import torch
    except ImportError:
        # Torch not available; force CPU
        return DeviceInfo(
            type="cpu",
            name="CPU",
            torch_device="cpu",
            details="PyTorch not installed"
        )

    # CUDA available (could be NVIDIA or AMD via ROCm)
    if torch.cuda.is_available():
        # AMD ROCm detection: PyTorch exposes HIP version
        hip_version = getattr(torch.version, "hip", None)

        if hip_version:
            return DeviceInfo(
                type="rocm",
                name=_get_gpu_name(),
                torch_device="cuda",
                details=f"ROCm (HIP {hip_version})"
            )

        # NVIDIA CUDA
        cuda_version = getattr(torch.version, "cuda", None)
        return DeviceInfo(
            type="cuda",
            name=_get_gpu_name(),
            torch_device="cuda",
            details=f"CUDA {cuda_version}"
        )

    # Fallback to CPU
    return DeviceInfo(
        type="cpu",
        name="CPU",
        torch_device="cpu",
        details=None
    )


def _get_gpu_name() -> str:
    """
    Return the name of the first available GPU, if possible.
    """
    try:
        import torch
        return torch.cuda.get_device_name(0)
    except Exception:
        return "Unknown GPU"
