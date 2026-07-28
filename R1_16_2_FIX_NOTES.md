# Audiobook Studio v0.3.0 R1.16.2

R1.16.2 contains the CompactPathField startup correction from R1.16.1
and permanently repairs its exact GUI smoke test.

The previous smoke script was executed from the Scripts directory, so
Python placed that directory—not the Audiobook Studio project root—at
the beginning of sys.path. Imports such as `ui.settings` therefore
failed even though the live source was valid.

The repaired smoke script resolves its own location, inserts the parent
project directory into sys.path, changes to that directory, and then
constructs the real SettingsPanel using the verified PySide6 runtime.
