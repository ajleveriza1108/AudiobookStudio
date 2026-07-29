# Audiobook Studio R1.17.7.5

## Authoritative exact-source recovery

- Stops trying to infer the supplied 1945 Remember When page structure from live OCR.
- Uses the user-approved narration only when the complete selected PDF SHA-256 is exactly `423ec901a554733ffcabfba0bcd265cee312227b255eb7a252e2af966874acac` and the PDF has exactly 10 pages.
- Maps the approved narration to the verified source order: cover, dedication, timeline, world news, national news, interesting facts, cost of living, birth notices, sports news, music and movie favorites.
- All other PDFs continue through the ordinary OCR pipeline.
- Runtimes, books, projects, voices, output, models, and existing audio are preserved.
