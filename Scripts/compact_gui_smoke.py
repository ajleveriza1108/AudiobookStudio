from __future__ import annotations

import os
import sys
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("QT_OPENGL", "software")

# When Python executes Scripts\compact_gui_smoke.py, sys.path[0] is the
# Scripts folder rather than the application root. Add the root explicitly
# so imports such as "ui.settings" work regardless of the caller's directory.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
project_root_text = str(PROJECT_ROOT)
if project_root_text not in sys.path:
    sys.path.insert(0, project_root_text)
os.chdir(PROJECT_ROOT)


def fail(message: str) -> None:
    print(f"Compact GUI smoke test: FAIL - {message}", file=sys.stderr, flush=True)
    raise SystemExit(1)


def main() -> int:
    try:
        from PySide6.QtWidgets import QApplication
        from ui.compact_widgets import CompactPathField
        from ui.settings import SettingsPanel
    except Exception as exc:
        fail(f"imports failed: {exc}")

    app = QApplication.instance() or QApplication([])

    try:
        field = CompactPathField("No book selected")
        if not field.isReadOnly():
            fail("CompactPathField is not read-only")
        field.setValue(r"D:\Books\Example Book.pdf")
        if field.text() != r"D:\Books\Example Book.pdf":
            fail("setValue did not update text")
        if field.toolTip() != field.text():
            fail("tooltip did not retain the complete value")
        field.selectAll()
        if field.selectedText() != field.text():
            fail("read-only text cannot be selected/copied")

        panel = SettingsPanel()
        panel.resize(360, 620)
        panel.show()
        app.processEvents()
        if panel.book.label.text() != "No book selected":
            fail("book path field did not initialize")
        if panel.output.label is None:
            fail("output path field did not initialize")
        panel.close()
        panel.deleteLater()
        field.deleteLater()
        app.processEvents()
    except Exception as exc:
        fail(f"widget construction failed: {exc}")

    print("Compact GUI startup smoke test: PASS", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
