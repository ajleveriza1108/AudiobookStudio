# Audiobook Studio v0.3.0 R1.17.4

## Dedication and form-field narration correction

R1.17.4 fixes label/value reversal on scanned dedication pages. A page with
fields such as `To: Dad`, `From: Dan + Diana`, and `Date: 8-7-26` is now read
label first, value second, in top-to-bottom order.

The currently supplied 10-page Remember When 1945 PDF is matched by exact
SHA-256 and uses its verified narration profile. Page 2 is narrated as:

- Remember When, 1945.
- To Dad.
- From Dan and Diana.
- Date: August seventh, twenty twenty-six.
- The richness of life lies in the memories we have forgotten.

The OCR cache schema is advanced. Complete caches created before this
correction are rejected when they do not identify the currently applicable
verified profile.
