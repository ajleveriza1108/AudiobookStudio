# Audiobook Studio v0.3.0 - Studio Preparation Update

## Added

- Book preparation analyzer and saved preparation report.
- Editable chapter include, exclude, rename, and reorder plan.
- Chapter-boundary narration planning.
- Pronunciation Manager with safe matching options and legacy migration.
- Background local voice-preview dialog with playback.
- Friendly Kokoro voice labels.
- Export metadata and bitrate controls.
- MP3 metadata and optional cover embedding.
- M4B chapter metadata generated from real audio durations.
- Final WAV audio-quality analysis and saved quality report.
- New core regression tests and complete project-pipeline simulation.

## Improved

- Main book workspace now has Overview, Cleaned Text, Preparation, and Chapters tabs.
- Large cleaned-text previews are capped in the GUI without truncating generation input.
- Cover previews use the Temp folder instead of writing beside the source book.
- Project, metadata, chapter, narration-plan, and report files use safe writes.
- Queue jobs carry the current book's chapter plan and metadata.
- Installation preserves local pronunciation and voice-profile data.

## Retained

- PDF and EPUB import.
- Kokoro narration and optional engine manifests.
- Existing folder layout and local JSON files.
- Pause, resume, stop, batch queue, live progress, and statistics.
- WAV, MP3, and M4B output choices.
- Fingerprint-based chunk recovery and streaming WAV merge from v0.2.0.
- Engine package/module/manifest fingerprinting and detailed WAV-record validation.
- Optional Piper and XTTS placeholders are now disabled instead of appearing production-ready.
- Exact chunk filename filtering prevents unrelated WAV files from entering a merge.
- Voice profile writes now use portable project paths and atomic storage.

## R1.2 Windows compatibility repair

- Replaced instance-level `QHeaderView.ResizeToContents` and `Stretch` access with Qt 6 scoped enums.
- Added `install_dependencies.ps1`, which works with either a project `.venv` or the installed Python 3.12 runtime.
- Added Windows font-directory configuration for pip-installed PySide6 builds.
- Added regression checks for Qt header enum compatibility.
- Improved verification output so it identifies the Python runtime in use.

## R1.4 permanent runtime repair

- Added missing portable Temp, Books, and Voices paths.
- Made cover extraction optional and non-fatal.
- Added old/new batch queue API compatibility.
- Added engine-aware Generate readiness and accurate lazy-load status.
- Added actual PDF import to full verification.
- Added regression tests for both reported runtime exceptions.

## R1.5 scanned PDF and chapterless-book repair

- Added local RapidOCR + ONNX Runtime integration and a Tesseract fallback.
- Added OCR cache reuse for scanned PDFs.
- Added mixed-PDF page handling that retains embedded text and OCRs image-only pages.
- Added Full Book fallback when no chapter heading exists.
- Added scanned-book preparation messaging instead of an empty chapter table.
- Added an offline OCR installer and full Windows OCR smoke verification.
- Repaired recent-book restoration so the Library count remains accurate.
- Kept the header status concise instead of displaying the complete filename.

## R1.14 — Structured OCR Reading Order

- Preserved OCR coordinates instead of flattening recognized lines.
- Added month timeline detection and cell-by-cell narration.
- Added strong multi-column ordering.
- Invalidated unsafe pre-layout OCR caches.
- Added page layout reports and timeline regression verification.
- Kept R1.13 GUI-thread dispatch safeguards.

## R1.14.1 — Staged Preflight Process Repair

- Separated offscreen unit tests from the real Windows GUI dispatch probe.
- Prevented native child status codes from collapsing into an unexplained installer exit code `-1`.
- Added signed and hexadecimal Windows exit diagnostics.
- Kept R1.14 structured OCR and R1.13 queued GUI callbacks unchanged.



## R1.14.2 Windows test-process teardown repair

- Preserved the real pytest result after successful Qt tests.
- Added deterministic QObject/QThread probe cleanup.
- Added a guarded test harness for Windows PySide interpreter teardown.
- Reordered worker deletion before QThread shutdown.

## R1.14.3 GUI probe lifetime repair

- Guards every post-event-loop QThread operation with `shiboken6.isValid()`.
- Removes the unconditional second `thread.quit()` that failed after Qt had already deleted the QThread.
- Adds a focused regression test for deleted Qt wrapper handling.
- Preserves structured timeline OCR and GUI-thread queued connections.
