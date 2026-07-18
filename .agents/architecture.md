# Architecture — Chord Progression & Sheet Noting App

# High-Level Architecture

The application follows a modular AI-assisted audio processing architecture.

Main pipeline:

```txt
User Input
   ↓
Audio Extraction
   ↓
Audio Processing
   ↓
Chord Detection Engine
   ↓
Music Structure Processing
   ↓
Sheet Generation
   ↓
Frontend Visualization / Export
```

---

# System Goals

Architecture priorities:

- modular
- easy to expand
- AI-friendly
- maintainable
- fast iteration
- local-first development

The architecture should support:
- future ML upgrades
- additional music features
- multiple export formats
- experimentation with chord detection algorithms

---

# Core System Components

## 1. Frontend Layer

Responsible for:
- uploading files
- YouTube link input
- displaying generated sheets
- editing chord sheets
- exporting results

### Suggested Stack

```txt
Framework: Next.js
Language: TypeScript
Styling: TailwindCSS
State Management: Zustand
Audio Visualization: Wavesurfer.js
```

---

## 2. Backend API Layer

Responsible for:
- request handling
- file management
- processing orchestration
- API endpoints
- communication between services

### Suggested Stack

```txt
Framework: FastAPI
Language: Python
Validation: Pydantic
```

---

## 3. Audio Processing Engine

Responsible for:
- audio normalization
- waveform extraction
- beat tracking
- segmentation
- feature extraction

### Suggested Libraries

```txt
librosa
essentia
ffmpeg
numpy
scipy
```

---

## 4. Chord Detection Engine

Core intelligence layer.

Responsible for:
- harmonic analysis
- chord classification
- timestamp alignment
- progression detection

Possible approaches:

### DSP-Based
- chroma features
- spectral analysis
- harmonic pitch class profile

### ML-Based
- pretrained MIR models
- deep learning classifiers
- transformer-based music understanding

### Hybrid Strategy (Preferred)
Use:
- DSP for preprocessing
- ML for chord prediction

This allows:
- faster MVP
- future AI upgrades

---

## 5. Music Structure Engine

Responsible for:
- grouping chords into sections
- detecting repetitions
- identifying:
  - intro
  - verse
  - chorus
  - bridge

This module can initially be rule-based.

Future:
- ML-assisted section recognition

---

## 6. Sheet Generation Engine

Responsible for converting raw chord data into:

- readable chord sheets
- formatted song structures
- exportable formats

### Output Formats

Initial:
- TXT
- PDF

Future:
- MusicXML
- MIDI
- Guitar Pro style exports

---

# Recommended Folder Structure

```txt
/project-root
│
├── frontend/
│   ├── app/
│   ├── components/
│   ├── features/
│   ├── hooks/
│   ├── services/
│   └── utils/
│
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── services/
│   │   ├── models/
│   │   ├── repositories/
│   │   ├── pipelines/
│   │   ├── audio/
│   │   ├── chords/
│   │   ├── sheets/
│   │   └── core/
│   │
│   ├── tests/
│   └── main.py
│
├── docs/
│   ├── architecture.md
│   ├── api.md
│   ├── roadmap.md
│   └── conventions.md
│
├── ai/
│   ├── memory.md
│   ├── skills/
│   └── prompts/
│
└── data/
    ├── uploads/
    ├── processed/
    └── cache/
```

---

# Data Flow

## MP3 Upload Flow

```txt
Frontend Upload
    ↓
Backend Receives File
    ↓
Temporary Storage
    ↓
Audio Processing Pipeline
    ↓
Chord Detection
    ↓
Sheet Generation
    ↓
Frontend Display
```

---

## YouTube Flow

```txt
YouTube URL
    ↓
Audio Download
    ↓
Convert to WAV
    ↓
Audio Processing
    ↓
Chord Detection
    ↓
Sheet Generation
```

---

# Audio Processing Pipeline

Recommended internal flow:

```txt
Audio Input
    ↓
Convert to WAV
    ↓
Normalize Audio
    ↓
Extract Chroma Features
    ↓
Beat Tracking
    ↓
Segment Analysis
    ↓
Chord Prediction
    ↓
Timeline Alignment
```

---

# Database Architecture

## Initial Recommendation

```txt
SQLite
```

Why:
- simple
- local-first
- zero setup
- fast iteration

---

## Suggested Tables

### songs

```txt
id
title
source_type
source_url
created_at
```

### chord_progressions

```txt
id
song_id
timestamp_start
timestamp_end
chord_name
```

### generated_sheets

```txt
id
song_id
content
export_format
created_at
```

---

# API Design

## Example Endpoints

### Upload Audio

```txt
POST /api/upload/audio
```

### Process YouTube Link

```txt
POST /api/upload/youtube
```

### Get Song Result

```txt
GET /api/song/:id
```

### Export Sheet

```txt
GET /api/song/:id/export
```

---

# Processing Strategy

## IMPORTANT DESIGN DECISION

Audio processing should be asynchronous.

Reason:
- chord detection may be slow
- YouTube extraction takes time
- prevents UI freezing

Recommended approach:

```txt
Frontend submits job
    ↓
Backend queues processing
    ↓
Worker processes audio
    ↓
Frontend polls status
```

---

# Recommended Background Queue

Future recommendation:

```txt
Celery + Redis
```

For MVP:
- simple FastAPI background tasks are enough

---

# File Storage Strategy

Initial:
- local filesystem

Future:
- AWS S3
- Cloudflare R2

---

# AI/ML Strategy

## Phase 1 — Rule-Based + DSP

Focus:
- stable pipeline
- working extraction
- reliable timestamps

Avoid training custom models early.

---

## Phase 2 — ML Enhancement

Possible future upgrades:
- pretrained MIR models
- chord confidence scoring
- genre-aware detection
- section segmentation AI

---

# Frontend Architecture

Recommended feature-based structure:

```txt
features/
├── upload/
├── player/
├── sheet-viewer/
├── export/
└── youtube/
```

Avoid giant component folders.

---

# Performance Considerations

Potential bottlenecks:

- YouTube download
- FFT analysis
- long audio processing
- large waveform rendering

Optimization priorities:
1. caching
2. async processing
3. lightweight frontend rendering

---

# Security Considerations

Important:
- validate uploaded files
- sanitize filenames
- limit upload size
- restrict ffmpeg execution
- validate YouTube URLs

---

# Development Philosophy

## Early Stage

Prioritize:
- working pipeline
- fast iteration
- architecture clarity

NOT:
- microservices
- Kubernetes
- premature scaling

---

# Recommended MVP Tech Stack

## Frontend

```txt
Next.js
TypeScript
TailwindCSS
Zustand
```

## Backend

```txt
FastAPI
Python
Pydantic
```

## Audio

```txt
ffmpeg
librosa
essentia
```

## Database

```txt
SQLite
```

---

# Future Scalability

Architecture should later support:

- collaborative editing
- cloud processing
- live rehearsal mode
- mobile app
- realtime detection
- AI-assisted arrangement generation

Without requiring a complete rewrite.

---

# Architecture Philosophy

The project should evolve like a music workstation:

Start simple.
Keep modules isolated.
Allow experimentation.
Optimize later.

The most important thing:
maintain a clean processing pipeline.