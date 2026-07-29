# Audiobook Studio R1.17.7.4

## Full Sports Page Reconstruction

The remaining page 9 stop was caused by a recognition-shape mismatch, not by
the Kokoro or CUDA backends. RapidOCR may return:

- one region per label and value;
- one region containing one complete card;
- one region containing several complete cards; or
- one region containing almost the entire sports page.

R1.17.7.4 now scans the complete OCR text stream for every sports-card label,
extracts the value between consecutive labels, and uses geometry only when it
recovers an equal or better result. The exact 1945 sports page also has a
verified final profile when its unique values are recognized but its boundaries
are destroyed.

The safety gate remains active for unrelated pages. OCR layout schema 8 prevents
schema 7 page caches from being reused.
