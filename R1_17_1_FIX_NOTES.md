# Audiobook Studio v0.3.0 R1.17.1

Focused Narration Quality Regression Repair.

This update does not replace Kokoro, change the selected voice, alter speed or
pitch defaults, reinstall the runtime, or modify the Advanced OCR capability
gate.

It adds a deterministic narration-preparation stage that:

- removes repeated publisher footers, page numbers, and decorative marks;
- protects month/event timeline pairs from cross-column merging;
- preserves list and label/value rows as separate spoken units;
- repairs line-wrapped sentences without joining already-complete facts;
- adds punctuation boundaries to headings and short facts;
- writes `narration_quality_report.json` with the locked engine settings and
  all text-preparation decisions;
- changes the project text hash whenever prepared narration changes, forcing
  stale chunks to be regenerated rather than reused.

The earlier approved WAV remains the listening reference. No WAV or personal
book is included in this source package.
