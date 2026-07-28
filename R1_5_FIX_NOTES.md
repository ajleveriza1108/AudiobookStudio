# Audiobook Studio v0.3.0 R1.5

## Scanned PDF and chapterless-book repair

R1.5 permanently distinguishes a normal text PDF from a scanned image-only PDF. A scanned book is no longer treated as an empty book and is no longer blocked by the **No Chapters Included** message.

### Offline OCR

- Adds local RapidOCR + ONNX Runtime support for scanned and mixed PDFs.
- Reads image-only pages without sending the book to a cloud service.
- Preserves selectable embedded text on mixed PDFs and OCRs only pages that need it.
- Caches recognized text under `Cache/OCR` using a source fingerprint.
- Reuses cached OCR text immediately when the same book is reopened.
- Reports page-by-page OCR status during generation.
- Keeps the original PDF unchanged.
- Supports a local Tesseract installation as a fallback OCR backend.

### Books without chapters

- A book with no printed chapter headings becomes one included **Full Book** section.
- Scanned books show this Full Book section before OCR so Generate remains usable.
- If OCR later recognizes chapter headings, generation uses those headings automatically.
- M4B and separate chapter export no longer require the source to contain a table of contents.

### Interface and library repairs

- Replaces the misleading empty chapter table with a scanned-PDF explanation.
- Shows whether OCR is ready and which local backend will be used.
- Keeps the header status as `Ready` instead of replacing it with a long filename.
- Restores/reopens a recent book into the Library automatically, fixing the `0 Books` state.
- Uses clearer `No Sections Included` wording for deliberately excluded content.

### Verification

The Windows verification now creates a real image-only PDF, confirms that it is detected as scanned, runs offline OCR, checks the Full Book fallback, validates OCR caching, and reloads the cached narration text.
