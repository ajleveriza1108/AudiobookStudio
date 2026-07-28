# Optional third-party engines

## Chatterbox TTS

Audiobook Studio can optionally install `chatterbox-tts` into a separate `.voice-venv` for local voice cloning from user-authorized reference recordings.

- Project: Resemble AI Chatterbox
- License: MIT
- Package pinned by R1.16 installer: `chatterbox-tts==0.1.7`
- Model files and Python packages are downloaded only when the user runs the optional installer or first uses a selected model.
- Audiobook Studio does not distribute celebrity recordings or third-party voice samples.

Users are responsible for obtaining permission to use each reference recording and generated voice profile.
