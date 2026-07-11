# Audiobook Studio -- Project Handoff

## Project

Audiobook Studio converts PDF/EPUB books into audiobooks.

## Locked Tech Stack

-   Python 3.12
-   PySide6
-   Kokoro TTS
-   FastAPI
-   FFmpeg
-   Windows 11
-   NVIDIA RTX 2050

## Development Rules

1.  Always provide COMPLETE FILE REPLACEMENTS.
2.  Never provide snippets.
3.  Never remove features unless requested.
4.  Preserve the architecture.
5.  Build incrementally.
6.  Uploaded files are the source of truth.
7.  If another file is required, ask only for that filename.

## Current Priorities

1.  Fix startup/runtime errors.
2.  Restore GUI.
3.  Make maximized GUI identical to windowed.
4.  Restore audiobook generation.
5.  Resume generation:
    -   Skip valid WAV chunks.
    -   Regenerate missing/corrupt chunks.
    -   Save progress.json.
    -   Resume after crash.
6.  Merge chunks automatically.
7.  Restore live logs, progress, statistics and queue.

## Resume Design

Chunk format: - chunk_00001.wav - chunk_00002.wav - ...

Algorithm: - Scan chunk\_\*.wav. - Validate WAVs. - Delete only corrupt
chunks. - Skip valid chunks. - Resume from first missing chunk. - Save
progress.json. - Merge automatically after completion.

## Important UI Files

-   window_controller.py
-   settings_book.py
-   settings_output.py
-   batch_queue.py
-   live_statistics.py
-   logger.py

Never assume: - ui.logs - ui.statistics - ui.queue - ui.controller

Use: - ui.logger - ui.live_statistics - ui.batch_queue -
ui.window_controller

## Added Core Modules

-   core/cache.py
-   core/memory.py
-   core/logger.py
-   core/output_manager.py
-   core/audio_validator.py
-   core/chunk_validator.py
-   core/progress.py
-   core/resume.py

## Workflow

For every uploaded file: - Analyze current implementation. - Return
COMPLETE replacement. - Preserve architecture. - Never invent APIs.

## Final Goal

Deliver a stable Audiobook Studio with: - Resume after crash - Automatic
merge - MP3/M4B export - Queue support - Live statistics - Modern
responsive GUI - Stable Kokoro integration
