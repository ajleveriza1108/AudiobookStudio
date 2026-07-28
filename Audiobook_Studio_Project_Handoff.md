# Audiobook Studio — Project Handoff

## Project purpose

Audiobook Studio is a local, offline-first Windows desktop application that converts PDF and EPUB books into narrated WAV, MP3, and M4B audiobooks.

## Source-of-truth rule

The user's uploaded/local project is authoritative. Preserve its architecture and workflow. Improvements must be delivered as complete replacement files or a complete update package with backup, verification, and rollback.

## Supported production stack

- Python 3.12
- PySide6 desktop GUI
- Kokoro local TTS
- WAV section generation
- FFmpeg for MP3 and M4B packaging
- PDF through PyMuPDF
- Offline scanned-PDF OCR through RapidOCR and ONNX Runtime, with local Tesseract fallback
- EPUB through EbookLib and Beautiful Soup
- Windows 11 primary development target

Piper and XTTS remain extension points, but their current implementations are incomplete and are disabled in v0.3.0. Do not present them as working production engines until their modules, voices, tests, and installers are complete.

## Behavior that must remain compatible

- PDF and EPUB import
- Existing `Books`, `Projects`, `Output`, `Models`, `Voices`, `Cache`, `Logs`, and `Temp` folders
- Layered `config.json` and private `config.local.json`
- Private `library.local.json`
- Existing `voices.json` and `pronunciation.json`
- Kokoro voice IDs, speed, and pitch
- Queue, pause, resume, stop, progress, logs, and statistics
- WAV, MP3, and M4B choices
- Existing valid narration sections when their fingerprints still match

## v0.3.0 production pipeline

1. Read embedded text or run cached/local OCR for scanned pages.
2. Preserve paragraphs while cleaning extraction artifacts.
3. Create a preparation report.
4. Detect chapters and apply the user's include, exclude, rename, and reorder plan.
5. Apply language-aware pronunciation rules.
6. Build narration chunks that never cross chapter boundaries.
7. Save project metadata, chapter plan, narration plan, and narration text atomically.
8. Generate zero-padded WAV sections.
9. Reuse a section only when its text, voice, speed, pitch, engine package/module/manifest fingerprint, file name, size, frames, sample rate, channels, and sample width still match.
10. Stream-merge sections without loading the whole book into RAM.
11. Export tagged MP3 and chapter-aware M4B when requested.
12. Create a final audio-quality report.
13. Clear active progress only after successful completion.


## R1.5 scanned-document rule

- A PDF with no embedded text is a supported scanned document, not an empty or invalid book.
- OCR must run locally and cache its result under `Cache/OCR`.
- Preserve embedded text on mixed PDFs and OCR only image-only pages.
- A book without printed headings must receive one included `Full Book` section.
- Do not block narration merely because chapter headings are absent.
- Reopening a scanned book after OCR must load the cached text and chapter detection immediately.

## Safety rules

- Never overwrite `config.local.json`, `library.local.json`, `voices.json`, or `pronunciation.json` during an update.
- Never delete personal books, models, projects, output, logs, or voice files.
- Keep the verified WAV master when MP3 or M4B packaging fails.
- Do not silently skip corrupt, missing, stale, or differently formatted narration sections.
- Do not merge nonstandard files that merely begin with `chunk_`.
- Use atomic writes for user state and production metadata.

## Interface direction

- Responsive at approximately 1366×768 and larger
- OLED Black and Dirty White themes
- Resizable library, book workspace, settings, and activity areas
- Overview, Cleaned Text, Preparation, and Chapters tabs
- Generation controls remain visible
- Friendly narrator names while retaining original engine IDs
- Buyer-friendly errors with technical details saved to Logs

## Validation requirement

Before release, run:

```powershell
.\run_phase3_checks.ps1
```

Also run a real short Kokoro generation on the target Windows computer because model, PyTorch, CUDA, audio playback, and FFmpeg behavior depend on that machine.
