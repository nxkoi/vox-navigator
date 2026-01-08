# Project Structure

This document describes the structure and organization of the **vox-local-tts** repository.

The goal of this structure is to:
- Keep responsibilities clearly separated
- Support long-term maintenance
- Make the project easy to understand for new contributors
- Avoid mixing application code with AI configuration or documentation

---

## Root Directory

The root of the repository contains only global, project-wide files:

    vox-local-tts/
    ├── LICENSE
    ├── .gitignore
    ├── README.md
    ├── .cursorrules
    ├── .cursor/
    └── docs/


### Root files purpose

- **LICENSE**  
  Defines the legal terms of use (non-commercial).

- **.gitignore**  
  Prevents generated files, models, and artifacts from being committed.

- **README.md**  
  Public-facing documentation:
  - What the project is
  - How to install it
  - How to use it

- **.cursorrules**  
  Hard constraints that guide the Cursor AI behavior.

- **.cursor/project_instructions.md**  
  Detailed instructions that define how the Cursor should reason about this project.

---

## Application Code

Application code is intentionally separated by responsibility.

    extension-firefox/
    tts-server/


### `extension-firefox/`
Contains the Firefox WebExtension responsible for:
- Capturing user text selections
- Exposing the context menu entry
- Sending text to the local TTS backend
- Playing generated audio

### `tts-server/`
Contains the local backend responsible for:
- Receiving text input
- Running neural TTS locally
- Managing GPU usage
- Returning generated audio

Frontend and backend must remain decoupled and communicate only via localhost.

---

## Documentation (`docs/`)

The `docs/` directory contains **technical and architectural documentation**.

It is intentionally separated from:
- AI configuration
- Public README
- Code

This documentation explains **how the application works**, not how to install it.

    docs/
    ├── OVERVIEW.md
    ├── ARCHITECTURE.md
    ├── DATA_FLOW.md
    ├── SECURITY.md
    ├── ROADMAP.md
    └── PROJECT_STRUCTURE.md


---

## Why a `docs/` directory exists

The `docs/` directory exists to:
- Capture design decisions
- Document architecture and data flow
- Prevent architectural knowledge from being lost
- Avoid forcing contributors to reverse-engineer the system from code

This documentation is authoritative and should be updated when major design changes occur.

---

## Documentation Guidelines

- Documents in `docs/` describe **what the system does and why**
- The README describes **how to install and use**
- The code describes **how it is implemented**
- AI configuration files describe **how the Cursor should behave**

Keep these concerns separate.

---

## Contribution Note

When modifying architecture or core behavior:
- Update the relevant document in `docs/`
- Keep documentation consistent with the actual code
