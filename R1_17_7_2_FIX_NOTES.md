# Audiobook Studio v0.3.0 R1.17.7.2

## Structured page narration repair

This update keeps the exact selected-PDF binding, persistent ebook removal,
and automatic RTX 2050 support from R1.17.7.1.

It adds geometry-based narration layouts for:

- cover pages with decorative product images;
- To / From / Date dedication forms;
- month timelines;
- World News and National News sections;
- label/value fact cards;
- cost-of-living item/price tables;
- three-column birth notices;
- sports label/value cards;
- music and movie lists.

Running publisher footers are removed. Structured pages are no longer allowed
to fall back to flattened row-order OCR. OCR cache schema 8 and layout schema 6
force a fresh read of the selected PDF. Existing books, source PDFs, projects,
models, GPU runtime, CPU runtime, output, and reference audio are preserved.
