# Audiobook Studio v0.3.0 R1.17.0

R1.17.0 integrates optional Unlimited-OCR behind a conservative hardware gate.

## Included

- Compact **Settings → OCR** tab.
- Toggle: **Use Unlimited-OCR for difficult scanned pages**.
- Laptop capability check for Windows architecture, logical CPU cores, RAM,
  free storage, NVIDIA GPU, VRAM, driver, CUDA capability, and compute class.
- Atomic capability report stored at `Logs/advanced_ocr_capability.json`.
- Supported, Experimental, and Unsupported results.
- Toggle automatically returns to Off on unsupported computers.
- Separate `.advanced-ocr-venv` so the main Kokoro/RapidOCR runtime is untouched.
- Pinned, SHA-256-verified Unlimited-OCR model download.
- Persistent local OCR worker with no network use during document processing.
- Per-page semantic reading order.
- Repetition and excessive-output rejection.
- Automatic RapidOCR/Tesseract fallback when Advanced OCR rejects a page.
- OCR cache separation so standard and advanced results are never confused.

The model is not bundled. It remains an optional large download for compatible
NVIDIA computers.
