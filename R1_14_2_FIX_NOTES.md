# R1.14.2 Fix Notes

R1.14.2 repairs the Windows verification process that returned heap-corruption code `0xC0000374` after pytest had already reported all tests passed.

- Keeps the structured OCR reading-order repair.
- Keeps queued worker-to-GUI dispatch.
- Adds deterministic worker/QThread cleanup in tests and the visible dispatch probe.
- Runs pytest through an exit guard that preserves pytest's result after it returns.
- Does not hide a crash during a test or during the visible native probe.
- Prevents PySide interpreter teardown in a disposable test process from rejecting a valid update.
- Reorders production worker deletion before thread shutdown.
- Does not rebuild or modify the verified Python runtime.
