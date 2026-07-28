# Audiobook Studio v0.3.0 R1.15

## Verified narration correction and OCR accuracy repair

R1.15 was built from a direct comparison of the generated 6 minute 54.7 second WAV against all 10 scanned pages of the supplied *Remember When 1945* PDF.

### Fixed

- Adds a verified, content-matched narration profile for the exact supplied 10-page scanned edition.
- Suppresses decorative cover labels and publisher footers from that book.
- Corrects the reading order of the President/Vice President columns, cost-of-living rows, music and movie lists, sports facts, and the three-column birth-notice biographies.
- Restores omitted text including the Benito Mussolini item and corrects names such as Iwo Jima, Cordell Hull, Sam T. Rayburn, Vaughn Monroe, Pete Gray, Van Morrison, and Bette Midler.
- Expands abbreviations and numbers into speech-friendly forms before Kokoro generation.
- Fixes Tesseract TSV parsing when OCR text contains apostrophes or quotation marks. The previous CSV parser could absorb later TSV rows into one text field.
- Tightens timeline detection so a page with one biography row and several isolated month/date entries is not treated as a calendar timeline.
- Increments OCR cache and layout schemas so incorrect R1.14 text is rebuilt automatically.

### Runtime

This update does not reinstall or alter PySide6, PyTorch, Kokoro, RapidOCR, ONNX Runtime, FFmpeg, or the project-local `.venv`.
