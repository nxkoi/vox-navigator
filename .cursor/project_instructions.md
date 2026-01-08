# Project Instructions – vox-local-tts

You are an AI coding assistant working on the project **vox-local-tts**.

This project is a **final, user-facing application**, not a research or experimental system.

It is a **local-first, privacy-preserving, strictly non-commercial Text-to-Speech application** that integrates a Firefox extension with a local GPU-accelerated neural TTS backend.

All decisions must favor real usability, stability, and maintainability.

---

## Project Nature

This is a production-oriented application intended for daily personal use and redistribution to other users.

Avoid:
- Research-style exploration
- Experimental features
- Alternative designs without implementation
- Partially implemented ideas

When uncertain:
- Make a reasonable production decision
- Implement it cleanly
- Document the assumption briefly

---

## Core Principles

- Local-first architecture
- All processing runs locally
- No cloud services
- No SaaS APIs
- No telemetry
- No external APIs
- Privacy by design
- GPU acceleration when available
- Non-commercial usage only

---

## Project Goal

Allow users to select text or paragraphs in Firefox and trigger a local neural Text-to-Speech engine that produces **human-like speech** using the user's own hardware (GPU when available).

The generated audio must be played directly in the browser as a direct result of explicit user interaction.

---

## Architecture

### Frontend
- Firefox WebExtension
- Context menu integration
- DOM-safe and defensive text extraction
- User-triggered actions only

### Backend
- Local HTTP API
- FastAPI preferred
- GPU detection with graceful CPU fallback
- One request produces exactly one audio output
- Backend must bind to localhost only

### TTS Engine
- Neural TTS only
- XTTS v2 as the default reference model
- WAV output
- Multilingual support with PT-BR as a first-class target

---

## Coding Guidelines

- Prefer clarity over cleverness
- Write production-ready code
- Avoid pseudo-code and placeholders
- Modularize only when it improves clarity or maintainability
- Avoid hidden global state
- Use explicit configuration
- Document non-obvious decisions in comments

---

## Security & Privacy

- Backend must bind to localhost only
- Never transmit user data externally
- No analytics
- No telemetry
- No logging of user-provided text content

---

## Output Expectations

When generating code:
- Prefer complete, runnable files over fragments
- Include comments explaining design decisions when needed
- Avoid TODOs unless explicitly requested

When modifying existing code:
- Preserve working behavior
- Refactor conservatively
- Avoid breaking user-facing functionality

---

## TTS & Audio Guidelines

Text-to-Speech quality is a **first-class concern** in this project.

### TTS Engine Rules
- Neural TTS only
- XTTS v2 is the default reference model
- Voice naturalness has priority over raw synthesis speed
- Prefer stable and reproducible output

### Audio Output
- Default format: WAV
- Mono audio unless explicitly required otherwise
- Sample rate must be consistent and documented
- One request generates exactly one audio file
- Never return partial or corrupted audio

### Text Handling
- Assume arbitrary text length
- Normalize text only if required by the TTS engine
- Do not silently truncate text
- Preserve punctuation and textual structure whenever possible

### Performance
- Load TTS models once at application startup
- Avoid reinitializing models per request
- Use GPU when available
- Avoid blocking the main API thread during synthesis

### Error Handling
- Fail explicitly and clearly on synthesis errors
- Return meaningful error messages
- Never mask or silently ignore failures

### Browser Playback
- Audio playback must always be triggered by explicit user action
- Do not auto-play without user intent
- Prefer simple and predictable `Audio()` playback

---

## Explicit Non-goals

- No browser-native TTS APIs
- No cloud-based TTS
- No third-party audio streaming
- No real-time streaming TTS (for now)
- No voice morphing unless explicitly requested
- No background or persistent audio services
