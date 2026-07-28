# Audiobook Studio v0.3.0 R1.3

This repair fixes a PowerShell output-capture defect in the verification and launcher scripts.

## Fixed

- Python verification output is shown live instead of being captured into `$Code`.
- The numeric native-process exit code is stored separately through `$LASTEXITCODE`.
- The launcher uses the same safe pattern, so normal application output cannot be mistaken for an exit code.
- Python runs unbuffered (`-u`) so diagnostics appear immediately.
- Added regression tests for both scripts.

No book, model, project, voice, output, cache, log, or private JSON data is replaced.
