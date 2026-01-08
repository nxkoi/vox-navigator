# Data Flow – vox-local-tts

## Purpose

This document describes the runtime data flow of the **vox-local-tts** application, detailing how user-selected text is transformed into audible speech.

The focus is on:
- Data movement
- Component interactions
- Execution boundaries
- Error propagation

Implementation details are intentionally abstracted unless they affect behavior or guarantees.

---

## High-Level Flow

At runtime, the data flow follows a strict, linear sequence:

    User Action
    ↓
    Text Selection
    ↓
    Context Menu Trigger
    ↓
    HTTP Request (localhost)
    ↓
    Text-to-Speech Inference
    ↓
    Audio Generation
    ↓
    HTTP Response
    ↓
    Browser Playback


Each step is triggered explicitly and completes fully before the next begins.

---

## Step-by-Step Data Flow

### 1. User Interaction

The flow begins with an explicit user action:

- The user selects text or a paragraph in Firefox
- The user opens the context menu
- The user selects the “Read with human voice” action

No automatic or background triggers exist.

---

### 2. Text Extraction (Frontend)

The Firefox extension extracts text from the webpage.

Key properties:
- Text is extracted from the current DOM context
- Only user-selected or explicitly targeted text is used
- No text is modified unless required for transport
- Text extraction assumes an untrusted DOM

The extracted text exists only in memory.

---

### 3. Request Construction

The extension constructs an HTTP request:

- Method: POST
- Target: `http://localhost:<port>/tts`
- Payload: Plain text or JSON-wrapped text
- Headers: Minimal, explicit

The request is created only as a result of user action.

---

### 4. Local Transport

The request is sent over:

- Loopback network interface (`localhost`)
- No external routing
- No proxy involvement

The transport layer is assumed to be reliable and low-latency.

---

### 5. Request Reception (Backend API)

The backend API receives the request.

Responsibilities at this stage:
- Validate request format
- Validate text payload
- Reject invalid or empty input
- Prepare the request for processing

No TTS inference occurs at this layer.

---

### 6. Application Logic

The application logic layer orchestrates the request:

- Assigns a unique request context
- Ensures one-request–one-output semantics
- Coordinates model invocation
- Handles synchronous execution

Requests are handled independently.

---

### 7. Hardware Detection

Before synthesis begins:

- The backend checks for GPU availability
- CUDA (NVIDIA) availability is detected explicitly
- ROCm (AMD) availability is detected when CUDA is unavailable
- A CPU fallback path is selected if no GPU is available or supported

This decision is made per process, not per request.

---

### 8. Text-to-Speech Inference

The TTS engine performs neural inference.

Characteristics:
- Model is already loaded in memory
- Inference is synchronous per request
- No shared mutable state is modified
- Text is converted into an audio waveform

Partial inference results are not exposed.

---

### 9. Audio Generation

The waveform is converted into an audio file.

Properties:
- Output format: WAV
- File is generated fully before returning
- Sample rate and channels are fixed and documented
- Audio file exists temporarily

No post-processing is applied unless explicitly enabled.

---

### 10. Response Construction

The backend constructs the HTTP response:

- Status: Success or explicit failure
- Payload: Audio file (binary)
- Headers: Content-Type set appropriately

On failure:
- No audio is returned
- An explicit error response is sent

---

### 11. Response Transport

The response is sent back to the Firefox extension via localhost.

- No retries are performed automatically
- Errors propagate directly to the frontend

---

### 12. Audio Playback (Frontend)

The extension receives the response and:

- Creates a browser-safe audio object
- Initiates playback
- Releases audio resources after playback

Playback is:
- Immediate
- User-initiated
- Non-persistent

---

## Error Propagation

Errors propagate strictly forward.

### Backend Errors
- Invalid input
- Model failure
- Hardware failure

Result in:
- HTTP error response
- No audio output

### Frontend Errors
- Network failure
- Playback failure

Result in:
- User-visible feedback
- No retries unless explicitly triggered

---

## Data Lifetime

| Data Type | Lifetime |
|----------|----------|
| Selected text | In-memory, per request |
| Audio file | Temporary, per request |
| Logs | Technical only, no user text |

No user data is persisted by default.

---

## Concurrency Model

- Each request is processed independently
- No shared mutable state between requests
- GPU resources are serialized by the TTS engine
- No request batching or streaming

---

## Non-Goals of the Data Flow

The data flow explicitly avoids:

- Background processing
- Streaming audio
- Partial audio delivery
- Long-lived sessions
- Cross-request state sharing

---

## Data Flow Invariants

The following invariants must always hold:

- User action triggers the flow
- Text is processed locally only
- One request produces one audio output
- No partial or streamed responses
- Playback occurs only after full synthesis

Breaking these invariants is considered a design regression.

---

## Relationship to Other Documents

This document describes **how data moves at runtime**.

Refer to:
- `OVERVIEW.md` for conceptual intent
- `ARCHITECTURE.md` for structural design
- `SECURITY.md` for data protection rationale
- `README.md` for usage instructions
