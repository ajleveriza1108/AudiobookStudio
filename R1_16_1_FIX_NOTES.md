# Audiobook Studio v0.3.0 R1.16.1

## Compact path-field startup repair

R1.16 introduced `CompactPathField` as a `QLineEdit`, but called
`setTextInteractionFlags()`, which is a `QLabel`/text-document API and is not
available on `QLineEdit`. The program therefore stopped while constructing the
Book settings panel.

R1.16.1 removes the invalid call, retains read-only selection/copy behavior,
adds an exact offscreen settings-panel startup smoke test, and updates the
launcher message. No AI, OCR, voice, model, project, book, or output data is
changed.
