from __future__ import annotations

import os
import sys
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("QT_OPENGL", "software")
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
os.chdir(PROJECT_ROOT)


def main() -> int:
    try:
        from PySide6.QtWidgets import QApplication
        from ui.settings_advanced_ocr import SettingsAdvancedOCR
    except Exception as error:
        print(f"Advanced OCR GUI smoke test: FAIL - imports failed: {error}")
        return 2
    app = QApplication.instance() or QApplication([])
    widget = SettingsAdvancedOCR()
    assert widget.enabled.text().startswith("Use Unlimited-OCR")
    assert widget.check_button.text() == "Check Laptop"
    assert widget.install_button.text() == "Install Module"
    widget.close()
    app.processEvents()
    print("Advanced OCR GUI smoke test: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
