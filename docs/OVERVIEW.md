# Overview – vox-local-tts

## Purpose

**vox-local-tts** is a local-first Text-to-Speech (TTS) application designed to provide high-quality, human-like speech synthesis directly from the Firefox browser using the user's own hardware.

The system allows a user to select text or paragraphs on any webpage and trigger neural Text-to-Speech synthesis executed locally, with the resulting audio played immediately in the browser.

The project prioritizes privacy, usability, and voice quality, avoiding all cloud services and external dependencies.

---

## What the Application Does

At a high level, vox-local-tts:

- Integrates with Firefox via a WebExtension
- Captures user-selected text or contextual paragraphs
- Sends text to a local backend via localhost
- Generates neural speech using a GPU-accelerated TTS model
- Plays the generated audio back in the browser

All processing occurs on the local machine.

---

## What the Application Is Not

vox-local-tts is explicitly **not**:

- A research prototype
- An experimental sandbox
- A cloud-based service
- A browser-native TTS wrapper
- A background audio daemon
- A commercial product

Design decisions intentionally avoid:
- Cloud APIs
- Browser-native speech synthesis
- Telemetry or analytics
- Always-on background services
- Real-time audio streaming

---

## Target Use Cases

The application is intended for:

- Reading articles, documentation, and long-form text
- Reviewing technical or academic content
- Assisting users who prefer listening over reading
- Private, offline or semi-offline usage
- Personal productivity and accessibility workflows

The system is designed for **daily use**, not one-off demonstrations.

---

## Design Principles

### Local-First
All computation, including neural inference, runs locally. No user text leaves the machine.

### Privacy by Design
User-selected text is processed only in memory for the duration of synthesis. No logging or storage of user content is performed by default.

### Voice Quality First
Natural-sounding speech is prioritized over synthesis speed or minimal resource usage.

### Explicit User Control
Audio generation and playback are always triggered by explicit user action. There is no automatic reading or background behavior.

### Simple, Clear Architecture
The system is split into clearly defined components with minimal coupling.

---

## High-Level Components

The application consists of two primary components:

### Firefox Extension
Responsible for:
- Detecting user interaction
- Extracting text safely from the DOM
- Exposing a context menu action
- Triggering audio playback

The extension contains no TTS logic.

### Local TTS Backend
Responsible for:
- Receiving text input
- Managing TTS models
- Detecting GPU availability
- Performing neural speech synthesis
- Returning audio to the caller

The backend is exposed only on localhost.

---

## Text-to-Speech Model

The default reference model is:

- **XTTS v2 (Coqui TTS)**

Key characteristics:
- Neural, high-quality voice synthesis
- Multilingual support
- Strong support for Portuguese (PT-BR)
- GPU acceleration via CUDA (NVIDIA) or ROCm (AMD)
- CPU fallback when GPU is unavailable
- Deterministic, file-based output

The architecture allows model replacement or extension in the future.

---

## Audio Characteristics

- Output format: WAV
- Playback: Mono (default)
- Sample rate: Fixed and documented
- One request produces exactly one audio output
- No audio post-processing unless explicitly added

---

## Platform Assumptions

- Linux is the primary target environment
- Windows is supported as a secondary target
- NVIDIA GPUs with CUDA support are preferred for best performance
- AMD GPUs with ROCm support may be used, though support may be experimental depending on hardware and drivers
- CPU fallback is always available when GPU is unavailable or unsupported

---

## Distribution and Usage Model

The project is distributed as source code.

Users are expected to:
- Run the backend locally
- Load the Firefox extension manually or via packaging
- Control their own environment and hardware

The project license explicitly forbids commercial use.

---

## Long-Term Vision

vox-local-tts aims to be:

- A stable, reliable local TTS tool
- A reference implementation for local-first browser-integrated TTS
- A privacy-respecting alternative to cloud-based voice services

Future development focuses on improving usability and robustness without compromising the core principles.

---

## Documentation Scope

This document describes **what the application is and why it exists**.

For other concerns, refer to:
- `README.md` for installation and usage
- `ARCHITECTURE.md` for technical structure
- `DATA_FLOW.md` for runtime behavior
- `SECURITY.md` for privacy and security decisions
- `.cursor/project_instructions.md` for AI development guidance
