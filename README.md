# Audiobook Studio

Audiobook Studio is a local, offline-first desktop workspace for converting PDF and EPUB books into narrated WAV, MP3, and M4B audiobooks.

Version 0.3.0 preserves the existing PySide6, Kokoro, project, queue, resume, and export architecture while adding a safer book-preparation and audiobook-production workflow.

## Main workflow

1. Import a PDF or EPUB.
2. Review the book overview and cleaned narration text.
3. Read the preparation report for possible scanned pages, footnotes, web addresses, damaged layout, and missing chapters.
4. Rename, reorder, include, or exclude detected chapters.
5. Choose a local narration engine, voice, speed, and pitch.
6. Add pronunciation rules for names, abbreviations, numbers, and unusual terms.
7. Choose WAV, tagged MP3, or chapter-aware M4B export.
8. Generate, pause, resume, stop safely, or reopen an interrupted production.





## R1.16 compact interface and optional Voice Studio

- Adds Wide, Compact, and Focus layouts. On smaller windows, Library and Settings switch one at a time instead of squeezing or cropping the main book workspace.
- Adds panel buttons and shortcuts: `Ctrl+L` for Library, `Ctrl+,` for Settings, and `Ctrl+J` for Activity.
- Makes paths single-line and selectable with full tooltips, wraps crowded action rows into compact grids, and places advanced export metadata in collapsible sections.
- Adds **Voice Studio** for local voice profiles created from recordings the user owns or is authorized to use. No celebrity recordings are included.
- Adds an optional isolated Chatterbox runtime under `.voice-venv`; the verified Kokoro/OCR `.venv` remains untouched.
- Supports Nano and Turbo for English, plus the larger Multilingual V3 model for supported languages.

## R1.15 verified narration and OCR accuracy repair

- Audited the complete generated WAV against all 10 scanned pages of the supplied *Remember When 1945* booklet.
- Applies a content-matched verified narration profile for that exact scanned edition.
- Corrects cover-art noise, merged columns, table row pairing, song titles, omitted news items, sports text, and the birth-notice biography order.
- Fixes Tesseract TSV parsing when recognized text contains apostrophes or quotation marks.
- Prevents biography pages with scattered month/date labels from being mistaken for calendar timelines.
- Invalidates older OCR caches so corrected narration is regenerated automatically.

## R1.5 scanned PDF repair

- Automatically detects image-only and mixed scanned PDFs.
- Runs local RapidOCR + ONNX Runtime during generation.
- Caches OCR text locally so a scanned book is not reread every time.
- Treats a book with no printed headings as one included **Full Book** section.
- Reopens cached OCR text in the Cleaned Text and Chapters workspaces.
- Repairs the empty Library count when a recent book is restored.

## R1.4 runtime repair

- Permanent portable `Books`, `Temp`, and `Voices` path registry
- Non-fatal PDF/EPUB cover preview
- Mixed-version batch queue compatibility
- Accurate Kokoro installation/readiness status
- Generate disabled when the production engine is unavailable
- Verification now exercises real PDF import and first-page preview
- Cleaner footer status without duplicate `Ready` rows

## v0.3.0 improvements

### Studio interface

- Responsive three-panel workspace with resizable horizontal and vertical splitters.
- OLED Black and Dirty White themes.
- Overview, Cleaned Text, Preparation, and Chapters tabs.
- Scrollable production settings with generation controls kept visible.
- Friendly narrator names while retaining the original engine voice IDs.
- Integrated local voice-preview window.
- Integrated pronunciation manager.
- Book metadata and bitrate controls for compressed exports.

### Book preparation

- Paragraph-preserving PDF and EPUB cleanup.
- Repeating margin text and common page-number filtering.
- Safer line-wrap dehyphenation.
- Preparation report with warnings and notices.
- Editable chapter plan without altering the source book.
- Chapter exclusions and custom order are used during generation.
- Chunks never cross chapter boundaries.

### Narration and recovery

- Fingerprint-based chunk reuse using text, engine, voice, speed, pitch, engine package version, engine module, and engine manifest.
- Validation of every reusable WAV section, including stored size, frames, sample rate, channels, and sample width.
- Atomic progress, project, chapter, and manifest writes.
- Crash-safe resume and stale-tail cleanup.
- Pause and stop checks inside narration and merge loops.
- Existing valid sections are retained when compressed export fails.

### Pronunciation

- Automatic migration of the original simple pronunciation dictionary.
- Whole-word, case-sensitive, regular-expression, language, and enabled options.
- Rule preview before saving.
- Atomic local rule storage in `pronunciation.json`.

### Export

- Streaming WAV merge for long books.
- Tagged MP3 export with optional embedded cover.
- M4B chapter timestamps generated from actual WAV durations.
- M4B title, author, narrator, genre, description, date, cover, and chapter metadata.
- Final audio quality report with duration, peak, average level, clipping, and silence checks.
- Preparation, narration plan, chapter, metadata, and quality reports saved with each book.

## Preserved files and folders

The update retains the existing project structure and recognizes:

- `Books`, `Projects`, `Output`, `Models`, `Voices`, `Cache`, `Logs`, and `Temp`
- `config.json` and private `config.local.json`
- `library.json` and private `library.local.json`
- `voices.json` and `pronunciation.json`
- Existing engine, controller, worker, core, and UI module organization

The repair installer does not overwrite `config.local.json`, `library.local.json`, `pronunciation.json`, or `voices.json`.

## Start on Windows

After installing dependencies, double-click:

`LAUNCH_AUDIOBOOK_STUDIO.bat`

Or run the PowerShell launcher:

```powershell
.\launch_audiobook_studio.ps1
```

## Verify

```powershell
.\run_phase3_checks.ps1
```

The full checks validate dependencies, core imports, responsive GUI construction, scanned-PDF OCR, engine manifests, runtime folders, and FFmpeg availability. They do not install the optional Chatterbox module or generate a full book.

## Important use note

Convert only books and documents that you own or have permission to reproduce as audio.

## Engine availability

Kokoro remains the default supported production engine. Chatterbox is an optional, separately installed local voice-cloning engine for authorized reference recordings. Piper and XTTS extension points remain disabled until their incomplete implementations receive full packaging and regression-test support.

## R1.14 structured scanned-page support

Scanned PDFs are processed with coordinate-aware OCR. Timeline and calendar pages are narrated cell by cell, and strong multi-column layouts are ordered without combining unrelated text from the same horizontal row. The OCR cache contains a page-level `layout_report.json` for review.

## R1.14.1 installer reliability

The staged update gate now runs ordinary tests offscreen and runs the Qt worker-dispatch stress test on the real Windows renderer. Native child failures are reported with their exact signed and hexadecimal status instead of an unexplained `-1`.

