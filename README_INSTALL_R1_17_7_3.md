# Install Audiobook Studio R1.17.7.3

1. Close Audiobook Studio.
2. Extract the complete update ZIP.
3. Run `INSTALL_R1_17_7_3_SPORTS_FIX.bat`.
4. Wait for all ten installer stages to pass.
5. Open Audiobook Studio, select `1945 Remember When.pdf` again, and generate.

The installer preserves `.venv`, `.gpu-venv`, voices, books, projects, output,
and completed narration sections. It creates a transactional source backup and
invalidates only stale OCR/layout caches.
