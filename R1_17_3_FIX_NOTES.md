# Audiobook Studio v0.3.0 R1.17.3

## Permanent Full-Book Integrity Repair

R1.17.3 corrects the regression that allowed a partial audiobook to be treated
as complete. The failed 1945 output was only 89.25 seconds long and contained
the opening material through the timeline, while the approved earlier WAV was
414.70 seconds long.

### Root cause

Two protections were missing:

1. An OCR cache could be reused without proving that its text represented every
   page in the source PDF.
2. The final audiobook path could be replaced after merging without proving
   that every expected narration section was present in the merged WAV.

R1.17.1 also changed narration preparation after a known-good WAV had already
been produced. R1.17.3 removes that narration regression and restores the exact
R1.16.2 narration plan, chunker, generator, and merger behavior.

### Permanent safeguards

- OCR cache schema 5 records and validates the real source-page count.
- Cached OCR text must contain one page segment for every PDF page.
- OCR and embedded-text page accounting must equal the source-page count.
- OCR text is protected by SHA-256 and per-page word counts.
- Rejected caches cannot reuse partial page-cache fragments.
- Narration retention is checked before speech generation.
- Every expected chunk number must exist exactly once and be a valid WAV.
- The candidate WAV frame count must equal the sum of all verified chunks.
- Duration is checked against narration word count and selected speed.
- `audiobook.wav` is replaced only after all checks pass.
- An existing WAV is copied into `Previous Audio` before promotion.
- Failed or incomplete candidates are deleted without touching the prior WAV.

### Preserved

The update does not replace `.venv`, optional runtimes, downloaded models,
books, projects, output, local settings, pronunciation rules, voice profiles,
or authorized voice recordings.
