# Audiobook Studio v0.3.0 R1.4

## Permanent runtime repair

R1.4 repairs the two failures captured in `Logs/audiobook.log` and adds regression protection so they cannot silently return.

### Book import and cover preview

- Adds `Books`, `Temp`, and `Voices` to the canonical `AppPaths` registry.
- Creates every runtime directory from the same portable project root.
- Makes cover extraction non-critical: a missing or damaged cover cannot abort PDF/EPUB import.
- Exercises actual PDF import and first-page preview during the Windows verification check.

### Batch queue compatibility

- Replaces the raw queue list with a list-compatible `JobCollection`.
- Supports both historical `batch.jobs()` calls and current `batch.jobs` list access.
- Includes a complete current `ui/batch_queue.py` replacement to converge mixed installations.

### Narration engine readiness

- Replaces the misleading `Engine not loaded` text with an installed/available status.
- Explains that Kokoro loads on first preview or narration rather than at application startup.
- Disables Generate and voice preview when the production engine is unavailable.
- Verifies the actual Kokoro, PyTorch, librosa, and audio dependencies.
- Preserves an existing PyTorch installation; the dependency helper installs a CPU-compatible build only when PyTorch is absent.

### Interface cleanup

- Removes duplicate `Ready` messages from the footer.
- Reserves the footer for active book, section progress, and engine state.
- Adds full-path tooltips to book and output labels.
- Keeps specific import errors inside the expected book workflow rather than displaying a generic unhandled-exception popup.

## Protected data

The R1.4 update does not replace personal books, models, voices, projects, output, cache, logs, temporary files, pronunciation rules, or local configuration/library files.
