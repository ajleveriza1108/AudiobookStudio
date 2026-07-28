# Audiobook Studio v0.3.0 R1.16

## Compact responsive studio

- Reworked the header, library, preview, settings, workspace, chapter editor, batch queue, and footer for common Windows display sizes and scaling levels.
- Added Wide, Compact, and Focus layouts. Focus mode shows one side panel at a time instead of squeezing or cropping the reading workspace.
- Added Library, Settings, and Activity panel buttons plus keyboard shortcuts.
- Converted long paths to single-line selectable fields with full-path tooltips.
- Moved export metadata and advanced controls into collapsible sections.
- Wrapped crowded chapter and queue actions into two-row button grids.
- Reduced excess padding while preserving readable text and click targets.
- Retained OLED Black and Dirty White themes.

## Voice Studio

- Added authorized local voice profiles under `Voices/Cloned`.
- Copies the selected reference recording into the portable project and records the user's permission confirmation.
- Added Nano, Turbo, and Multilingual V3 model choices.
- Added an optional isolated `.voice-venv` installer so the verified Kokoro/OCR runtime is never modified.
- Added a persistent local Chatterbox worker and engine adapter.
- No celebrity recordings or voice samples are included.

## Preserved behavior

PDF/EPUB importing, structured OCR, corrected narration profiles, Kokoro narration, projects, resume, pronunciation rules, queues, and WAV/MP3/M4B exports remain in place.
