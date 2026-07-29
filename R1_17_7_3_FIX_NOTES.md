# Audiobook Studio R1.17.7.3

## Sports-card live OCR repair

R1.17.7.2 correctly refused to narrate page 9 when live RapidOCR returned a
different region shape than the test fixture. The most important variation was
a single region containing both the card label and value, such as:

`World Series Champion Detroit Tigers`

R1.17.7.3 now:

- separates inline sports labels from their OCR-recognized values at Winner or Champion;
- reconstructs labels whose final Winner/Champion keyword was returned as a separate region;
- locates all card anchors before assigning values, preventing the next label from being attached to the previous value;
- keeps the structured safety gate active;
- derives every value from the selected PDF OCR rather than a hardcoded transcript;
- bumps OCR cache/layout schemas to 9/7 so the affected PDF is processed again.
