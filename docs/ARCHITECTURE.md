# Architecture – vox-local-tts

## Architectural Goals

The architecture of **vox-local-tts** is designed to satisfy the following goals:

- Strictly local execution
- Clear separation of responsibilities
- Minimal coupling between components
- Predictable and deterministic behavior
- Easy debugging and long-term maintainability

The system deliberately avoids complex orchestration, background services, or distributed components.

---

## High-Level Architecture

vox-local-tts is composed of two primary subsystems:

    +-----------------------+
    | Firefox Browser |
    | |
    | +-----------------+ |
    | | WebExtension | |
    | | (Frontend) | |
    | +--------+--------+ |
    | | |
    +-----------|-----------+
    |
    | HTTP (localhost)
    |
    +-----------v-----------+
    | Local TTS Backend |
    | |
    | +-----------------+ |
    | | FastAPI Server | |
    | +--------+--------+ |
    | | |
    | +--------v--------+ |
    | | TTS Engine | |
    | | (Neural Model) | |
    | +-----------------+ |
    +-----------------------+


Each subsystem is independently deployable and testable.

---

## Component Boundaries

### Firefox Extension (Frontend)

**Responsibilities:**
- Capture explicit user actions
- Extract text safely from the webpage DOM
- Present a context menu action
- Send text to the backend
- Play generated audio

**Non-responsibilities:**
- Text-to-Speech synthesis
- Audio processing or transformation
- Persistent storage of user data
- Network communication beyond localhost

The extension must assume:
- Untrusted webpage DOM
- Arbitrary page structure
- Explicit user consent for each action

---

### Local TTS Backend

The backend is a local HTTP service bound to `localhost`.

**Responsibilities:**
- Receive text input
- Validate and normalize input when required
- Detect available hardware (GPU / CPU)
- Run neural TTS inference
- Generate audio output
- Return audio to the caller

**Non-responsibilities:**
- User interface
- Authentication
- Session management
- Long-term audio storage
- Background scheduling

---

## Backend Internal Structure

The backend is logically divided into three layers:

    +---------------------+
    | API Layer |
    | (FastAPI) |
    +----------+----------+
    |
    +----------v----------+
    | Application Logic |
    | (Request handling) |
    +----------+----------+
    |
    +----------v----------+
    | TTS Engine Layer |
    | (Model inference) |
    +---------------------+


### API Layer
- Exposes HTTP endpoints
- Performs input validation
- Handles request/response lifecycle
- Does not contain business logic

### Application Logic Layer
- Coordinates requests
- Manages lifecycle of TTS operations
- Handles error propagation
- Ensures one-request–one-output behavior

### TTS Engine Layer
- Loads neural models at startup
- Manages GPU/CPU execution
- Performs actual speech synthesis
- Is isolated from HTTP concerns

---

## Data Flow Between Components

The extension and backend communicate exclusively via HTTP over `localhost`.

- Protocol: HTTP
- Transport: Loopback interface only
- Payload: Plain text input
- Response: Audio file (WAV)

No persistent connections or streaming protocols are used.

---

## Text-to-Speech Model Integration

The default TTS model is **XTTS v2**.

Integration characteristics:
- Model loaded once at backend startup
- Inference performed per request
- Deterministic output per input
- No shared mutable state between requests

The architecture allows:
- Replacing the TTS model
- Adding multiple voices
- Supporting additional languages

without changes to the frontend.

---

## Audio Handling

Audio generation is treated as a terminal operation.

- Audio is generated fully before being returned
- Partial audio responses are not allowed
- No streaming or chunked transfer
- No post-processing unless explicitly added

The backend is responsible only for generating valid audio files.

---

## Error Handling Strategy

### Frontend
- Treat backend failures as recoverable
- Display minimal, clear user feedback
- Never crash or block browser interaction

### Backend
- Fail fast on invalid input
- Return explicit error responses
- Never return partial or corrupted audio
- Log technical errors without logging user text

---

## Security Architecture

Security is enforced primarily through **architectural constraints**, not complex mechanisms.

- Backend binds to localhost only
- No open network ports
- No authentication required
- No persistent user data storage

The threat model assumes:
- The user controls the local machine
- The browser and backend run on the same host

---

## Scalability Considerations

The system is intentionally **not designed for horizontal scaling**.

- One backend instance per user
- One synthesis task per request
- GPU resources managed locally

This simplifies architecture and improves predictability.

---

## Extensibility Boundaries

The architecture supports extension in the following areas:
- Additional TTS models
- Voice selection
- Text preprocessing modules
- Playback control features

It explicitly avoids:
- Distributed processing
- Multi-user orchestration
- Cloud synchronization

---

## Architectural Invariants

The following rules must remain true:

- Frontend and backend are decoupled
- All processing remains local
- TTS is neural and local
- User action always triggers synthesis
- One request produces one audio output

Violating these invariants is considered an architectural regression.

---

## Relationship to Other Documentation

This document defines **how the system is structured**.

Refer to:
- `OVERVIEW.md` for conceptual description
- `DATA_FLOW.md` for runtime behavior
- `SECURITY.md` for privacy and security rationale
- `README.md` for installation and usage
