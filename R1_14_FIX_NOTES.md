# Audiobook Studio v0.3.0 R1.14

## Structured OCR Reading-Order Repair

R1.14 repairs scanned pages that contain timelines, multiple independent columns, or other spatial layouts. Earlier releases retained the OCR words but discarded their coordinates, so unrelated cells on the same horizontal row could be narrated as one sentence.

### Permanent repairs

- Retains RapidOCR and Tesseract bounding boxes, confidence scores, and page coordinates.
- Detects month-based timeline and calendar layouts.
- Associates each description with its nearest month heading and narrates cells in calendar order.
- Detects strong multi-column gutters and orders columns independently.
- Ignores decorative connector lines and narrow OCR artifacts.
- Writes `layout_report.json` to the OCR cache and copies it to the audiobook project as `OCR Reading Order Report.json`.
- Invalidates all pre-R1.14 OCR caches because they may contain flattened reading order.
- Stores page-level layout mode, confidence, warnings, regions, and reading order.
- Adds preparation notices for timeline and multi-column OCR pages.
- Preserves the R1.13 queued main-thread GUI callback repair.

### Important regeneration behavior

The first generation after R1.14 automatically reruns OCR for scanned PDFs. Existing incorrectly ordered cache text is not reused. Changed narration text also invalidates stale audio chunks through the existing resume fingerprints.
