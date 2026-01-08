# Roadmap – vox-local-tts

## Purpose

This document outlines the planned evolution of the **vox-local-tts** application.

The roadmap communicates **direction and priorities**, not fixed timelines or guarantees.  
Features are grouped by maturity and impact on real-world usability.

---

## Guiding Principles

All roadmap decisions must respect the following principles:

- Local-first execution
- Privacy by design
- Explicit user control
- Stability over experimentation
- No cloud services
- Non-commercial usage only

Features that violate these principles are out of scope.

---

## Current State (Baseline)

The baseline goal of the project is:

- Local TTS backend running on user hardware
- Firefox extension triggering TTS via context menu
- Neural, human-like voice synthesis
- Audio playback directly in the browser
- No background services
- No telemetry or external dependencies

This baseline must remain stable.

---

## Near-Term Goals (Core Usability)

These features directly improve daily usability and are considered **high priority**.

### Text Handling
- Support reading full paragraphs reliably
- Handle large text selections gracefully
- Improve text normalization for better speech flow

### Playback Control
- Pause and resume playback
- Stop playback explicitly
- Prevent overlapping audio playback

### Voice Management
- Voice selection (when supported by the TTS model)
- Persist selected voice locally (optional)

---

## Mid-Term Goals (Quality & Comfort)

These features improve user experience without increasing architectural complexity.

### Reading Experience
- Sequential reading of multiple paragraphs
- Optional reading order control
- Smooth transitions between audio segments

### Performance
- Optional local audio caching
- Reduced latency for repeated text
- Better GPU utilization on supported hardware

### Configuration
- Simple local configuration file
- User-adjustable speech rate and volume
- Optional hotkeys for common actions

---

## Long-Term Goals (Polish & Distribution)

These goals focus on making the application easier to install and distribute.

### Packaging
- Docker image with CUDA (NVIDIA) and ROCm (AMD) support
- Optional standalone binaries
- Simplified setup for non-technical users

### Extension Improvements
- Improved UI feedback in Firefox
- Better error reporting
- Accessibility improvements

---

## Explicit Non-Goals

The following are intentionally **out of scope**:

- Cloud-based TTS
- SaaS or multi-user deployments
- Real-time audio streaming
- Background audio services
- Browser-native TTS APIs
- Monetization features
- User tracking or analytics

---

## Contribution Alignment

Contributions are welcome when they:

- Improve real-world usability
- Respect architectural invariants
- Maintain local-first guarantees
- Do not introduce external dependencies

Changes that significantly alter scope should be discussed before implementation.

---

## Roadmap Evolution

This roadmap is a living document.

It should be updated when:
- Major features are completed
- Project direction changes
- Architectural constraints evolve

Completed items may be moved to release notes or changelogs.

---

## Relationship to Other Documentation

This document defines **where the project is going**.

Refer to:
- `OVERVIEW.md` for project intent
- `ARCHITECTURE.md` for system structure
- `DATA_FLOW.md` for runtime behavior
- `SECURITY.md` for privacy guarantees
- `README.md` for installation and usage
