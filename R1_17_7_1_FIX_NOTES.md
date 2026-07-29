# Audiobook Studio v0.3.0 R1.17.7.1

## Exact selected PDF + RTX 2050 cumulative merge

This release fixes the failed R1.17.7 installation over R1.17.5.4.

The prior package installed R1.17.7 source over the GPU build, then ran stale
R1.17.5.4 tests against a mixed live project. The test suite scanned the
machine-specific `.gpu-venv`, expected the previous version number, and treated
the GPU launcher as an error. Installation rolled back correctly.

R1.17.7.1 is a true cumulative merge:

- exact selected-PDF SHA-256 binding from R1.17.7;
- source-specific OCR cache and output folder;
- removal of the hardcoded Remember When narration profile;
- persistent ebook removal and startup-history reconciliation;
- automatic RTX 2050 GPU launcher and protected CPU fallback from R1.17.5.4;
- merged GPU and removal-persistence configuration defaults;
- runtime-aware tests that never scan `.venv`, `.gpu-venv`, or
  `.advanced-ocr-venv`;
- installed-source verification in an isolated copy built from the manifest,
  rather than inside the live project.

User books, PDFs, audio, projects, models, voices, local configuration, CPU
runtime, GPU runtime, and Advanced OCR runtime are preserved.
