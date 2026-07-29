# Audiobook Studio v0.3.0 R1.17.2

Cumulative Stable Narration Repair and Installer Preflight Correction.

R1.17.2 contains the complete R1.17.1 narration-quality work:

- removes repeated footers, page numbers, and decorative OCR noise;
- protects timeline month/event pairs;
- repairs sentence fragments without merging separate facts;
- preserves list and label/value rows;
- records locked narrator settings and narration-preparation decisions;
- forces regeneration when prepared narration changes.

The R1.17.1 live project was not changed because its installer stopped
during preflight. The preflight package imported
`core.narration_plan`, which depends on `core.chunker`, but the update
payload did not include `core/chunker.py`.

R1.17.2 includes every dependency required by the isolated source
preflight and adds a regression test that verifies the payload can
import and exercise the chunker before touching the live project.
