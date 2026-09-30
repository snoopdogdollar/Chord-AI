# AGENTS.md

Agents working in this repository must preserve the documented MVP scope.

## MVP Rules

- Can introduce deep learning.
- Do not add manual editing, transposition, MusicXML, MIDI, realtime processing, authentication, cloud sync, or collaboration.
- Keep API routes thin. Business logic belongs in services.
- Keep DSP, chord detection, sheet generation, and export generation separate.
- Background processing must not block HTTP request handlers.
- Supported exports are `txt` and `pdf`.

## Pipeline

```text
Input
Extraction
Normalization
Feature extraction
Beat detection
Chord detection
Timeline smoothing
Sheet generation
Export
```

## Quality Bar

Every change should be small, testable, and consistent with the modular monolith architecture.
