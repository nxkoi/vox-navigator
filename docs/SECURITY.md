# Security & Privacy – vox-local-tts

## Purpose

This document describes the **security and privacy model** of the **vox-local-tts** application.

Security in this project is enforced primarily through **architectural constraints**, explicit non-goals, and minimal attack surface, rather than complex authentication or network mechanisms.

The goal is to ensure that:
- User data never leaves the local machine
- The system is predictable and auditable
- Privacy is preserved by default

---

## Security Model Overview

vox-local-tts follows a **local-trust model**:

- The user controls the local machine
- The browser and backend run on the same host
- No external parties are involved in data processing

Security assumptions are explicit and documented to avoid false guarantees.

---

## Trust Boundaries

The system has exactly **two trust domains**:

    [ User / Local Machine ]
    |
    | (localhost only)
    |
    [ Local TTS Backend ]


Everything outside the local machine is considered **untrusted and irrelevant** to the system.

---

## Data Exposure Surface

The application minimizes data exposure by design.

### Exposed Interfaces

- One local HTTP endpoint
- Bound to `localhost` only
- No public network exposure
- No inbound connections from external hosts

### Non-Exposed Interfaces

- No cloud endpoints
- No third-party APIs
- No browser-native TTS services
- No telemetry endpoints

---

## Network Security

### Localhost Binding

The backend must:
- Bind exclusively to `127.0.0.1` or `localhost`
- Never listen on external interfaces
- Never expose ports publicly

This prevents:
- Remote access
- Network scanning
- Accidental exposure on LAN/WAN

---

## Data Handling and Privacy

### User Text

- User-selected text is processed in memory only
- Text exists only for the duration of synthesis
- No persistent storage of text
- No logging of user-provided content

### Audio Output

- Generated audio exists temporarily
- Audio files are not persisted by default
- Audio is returned immediately to the browser
- No caching unless explicitly implemented by the user

---

## Logging Policy

Logs are strictly limited to:

- Startup information
- Hardware detection status
- Error diagnostics (technical only)

Logs must never include:
- User-selected text
- Generated audio content
- Full request payloads

---

## GPU and Hardware Security

- GPU usage is local and process-bound
- No GPU sharing across users
- No remote GPU access
- CUDA (NVIDIA) and ROCm (AMD) detection is explicit and controlled
- CPU fallback ensures operation when GPU is unavailable

Hardware is treated as a trusted local resource.

---

## Browser Security Considerations

### Untrusted DOM

The Firefox extension must assume:
- Arbitrary webpage content
- Potentially malicious DOM structures

Mitigations:
- Defensive text extraction
- No execution of page scripts
- No injection of page-level code beyond extraction

---

### User-Controlled Execution

- Audio generation is triggered only by explicit user action
- No automatic reading
- No background monitoring of pages
- No persistent permissions beyond extension scope

---

## Absence of Authentication

The system does **not** implement authentication or authorization.

This is intentional.

Reasons:
- Single-user, local-only usage
- No multi-user access
- No remote clients

Adding authentication would increase complexity without improving security under the defined trust model.

---

## Threat Model

### In-Scope Threats

- Accidental data leakage
- Unintended network exposure
- Logging of sensitive user content
- Misuse of browser-native APIs

### Out-of-Scope Threats

- Compromised operating system
- Malicious local user
- Physical access attacks
- Browser-level exploits unrelated to the extension

---

## Security Invariants

The following invariants must always hold:

- No data leaves the local machine
- Backend binds to localhost only
- No telemetry or analytics
- No cloud services
- No persistent storage of user content

Violating any of these is considered a **security regression**.

---

## Future Security Considerations

Potential future enhancements (non-mandatory):

- Optional local authentication token
- Configurable rate limiting
- Sandboxed backend execution
- Explicit permission prompts for extended features

These must never compromise the local-first and privacy-first model.

---

## Relationship to Other Documentation

This document defines **how security and privacy are enforced**.

Refer to:
- `OVERVIEW.md` for project intent
- `ARCHITECTURE.md` for structural boundaries
- `DATA_FLOW.md` for runtime data movement
- `README.md` for installation and usage
