# R1.14.3 Fix Notes

R1.14.3 completes the R1.14 structured OCR update by repairing the visible GUI-thread preflight cleanup.

The R1.14.2 probe correctly completed 4,000 queued progress updates, then called `thread.quit()` after `ThreadManager` had already handled `thread.finished` and deleted the underlying QThread C++ object. PySide therefore raised `RuntimeError: Internal C++ object ... already deleted`.

R1.14.3 checks `shiboken6.isValid()` before every post-event-loop QThread operation. It treats an already deleted QThread as successful normal cleanup, not as a failed probe. It does not alter the working runtime, OCR engine, TTS engine, books, projects, or output.
