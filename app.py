from __future__ import annotations

import faulthandler
import json
import os
import sys
import traceback
from datetime import datetime
from pathlib import Path

# Stable Windows QWidget rendering. The application uses a complete custom
# stylesheet, so the cross-platform Fusion style is more predictable than a
# native theme plug-in. These settings must be applied before importing Qt.
os.environ.setdefault("CUDA_MODULE_LOADING", "LAZY")
os.environ.setdefault("QT_STYLE_OVERRIDE", "Fusion")
os.environ.setdefault("QT_OPENGL", "software")
os.environ.setdefault("QT_QUICK_BACKEND", "software")
os.environ.setdefault("QSG_RHI_BACKEND", "software")
os.environ.setdefault("QT_WIDGETS_RHI", "0")

if os.name == "nt":
    windows_fonts = Path(os.environ.get("WINDIR", r"C:\Windows")) / "Fonts"
    if windows_fonts.is_dir():
        os.environ.setdefault("QT_QPA_FONTDIR", str(windows_fonts))

os.environ.setdefault(
    "PYTORCH_CUDA_ALLOC_CONF",
    "max_split_size_mb:128,expandable_segments:True",
)

from core.paths import PATHS  # noqa: E402

PATHS.ensure_runtime_directories()
os.chdir(PATHS.project_root)

_CRASH_STREAM = None
_STAGE_FILE = PATHS.logs / "startup_stage.json"
_PROBE_MARKER = PATHS.logs / "gui_probe_complete.json"
_CLEAN_SHUTDOWN_FLAG = PATHS.logs / "clean_shutdown.flag"

try:
    _PREVIOUS_SESSION_CLEAN = _CLEAN_SHUTDOWN_FLAG.is_file()
    if _CLEAN_SHUTDOWN_FLAG.exists():
        _CLEAN_SHUTDOWN_FLAG.unlink()
except Exception:
    _PREVIOUS_SESSION_CLEAN = False


def _write_startup_stage(stage: str, detail: str = "") -> None:
    try:
        temporary = _STAGE_FILE.with_suffix(".json.tmp")
        temporary.write_text(
            json.dumps(
                {
                    "timestamp": datetime.now().isoformat(timespec="seconds"),
                    "stage": stage,
                    "detail": detail,
                    "python": sys.executable,
                },
                indent=2,
                ensure_ascii=False,
            )
            + "\n",
            encoding="utf-8",
        )
        os.replace(temporary, _STAGE_FILE)
    except Exception:
        pass


def _enable_native_crash_log() -> None:
    global _CRASH_STREAM
    try:
        crash_path = PATHS.logs / "native_crash.log"
        _CRASH_STREAM = crash_path.open("a", encoding="utf-8", buffering=1)
        _CRASH_STREAM.write(
            f"\n[{datetime.now().isoformat(timespec='seconds')}] Audiobook Studio startup\n"
        )
        faulthandler.enable(file=_CRASH_STREAM, all_threads=True)
    except Exception:
        _CRASH_STREAM = None


_enable_native_crash_log()
_write_startup_stage("python-started")

from PySide6.QtCore import QTimer, Qt  # noqa: E402
from PySide6.QtWidgets import QApplication, QMessageBox  # noqa: E402

from core.cache import CacheManager  # noqa: E402
from core.config import Config  # noqa: E402
from core.library import Library  # noqa: E402
from core.logger import Logger  # noqa: E402
from ui.main_window import MainWindow  # noqa: E402
from ui.theme_manager import ThemeManager  # noqa: E402


class AudiobookStudio:
    def __init__(self) -> None:
        self.config = Config()
        self.library = Library()
        self.cache = CacheManager(str(PATHS.cache))
        self.logger = Logger(str(PATHS.logs))
        self._document_session_restored = False
        self._probe_mode = os.environ.get("AUDIOBOOK_STUDIO_PROBE", "") == "1"
        self._previous_session_clean = bool(_PREVIOUS_SESSION_CLEAN or self._probe_mode)
        if self._probe_mode:
            try:
                if _PROBE_MARKER.exists():
                    _PROBE_MARKER.unlink()
            except Exception:
                pass

        try:
            QApplication.setAttribute(Qt.ApplicationAttribute.AA_UseSoftwareOpenGL, True)
        except Exception:
            pass
        try:
            QApplication.setHighDpiScaleFactorRoundingPolicy(
                Qt.HighDpiScaleFactorRoundingPolicy.RoundPreferFloor
            )
        except Exception:
            try:
                QApplication.setHighDpiScaleFactorRoundingPolicy(
                    Qt.HighDpiScaleFactorRoundingPolicy.Round
                )
            except Exception:
                pass

        _write_startup_stage("creating-qapplication")
        self.app = QApplication.instance() or QApplication(sys.argv)
        self.app.setApplicationName("Audiobook Studio")
        self.app.setOrganizationName("Audiobook Studio")
        self.app.setStyle("Fusion")
        ThemeManager.apply(self.app, self.config.get("theme", "dark"))

        _write_startup_stage("creating-main-window")
        self.window = MainWindow(config=self.config)
        sys.excepthook = self.handle_unhandled_exception
        self.app.aboutToQuit.connect(self.save_session)
        self.restore_interface_settings()
        _write_startup_stage("main-window-created")

    @property
    def settings(self):
        return self.window.central.settings

    @property
    def sidebar(self):
        return self.window.central.sidebar

    @property
    def preview(self):
        return self.window.central.preview

    @property
    def console(self):
        return self.window.workspace.console

    def _log_error(self, message: str) -> None:
        try:
            self.logger.error(message)
        except Exception:
            print(message, file=sys.stderr)

    def handle_unhandled_exception(self, exception_type, exception_value, exception_traceback) -> None:
        details = "".join(
            traceback.format_exception(exception_type, exception_value, exception_traceback)
        )
        self._log_error(details)
        try:
            QMessageBox.critical(
                self.window,
                "Audiobook Studio Needs Attention",
                "An unexpected problem occurred. Your existing project and completed audio "
                "sections were not intentionally removed.\n\n"
                f"Support details were written to: {PATHS.logs}",
            )
        except Exception:
            print(details, file=sys.stderr)

    def restore_interface_settings(self) -> None:
        """Restore lightweight controls before showing the window.

        Book parsing and cover rendering are deliberately deferred until after
        the Windows backing store has completed its first real paint.
        """
        try:
            width = max(900, int(self.config.get("window_width", 1366)))
            height = max(620, int(self.config.get("window_height", 768)))
            screen = self.app.primaryScreen().availableGeometry()
            self.window.resize(min(width, screen.width()), min(height, screen.height()))

            self.settings.set_engine(str(self.config.get("engine", "kokoro")))
            self.settings.set_voice(str(self.config.get("voice", "af_heart")))
            self.settings.speech.set_speed(float(self.config.get("speed", 1.0)))
            self.settings.speech.set_pitch(float(self.config.get("pitch", 0.0)))
            self.settings.export_wav.setChecked(bool(self.config.get("export_wav", True)))
            self.settings.export_mp3.setChecked(bool(self.config.get("export_mp3", False)))
            self.settings.export_m4b.setChecked(bool(self.config.get("export_m4b", False)))
            self.settings.overwrite.setChecked(bool(self.config.get("overwrite", False)))
            self.settings.delete_chunks.setChecked(bool(self.config.get("delete_chunks", False)))
            self.settings.export.bitrate.setCurrentText(str(self.config.get("bitrate", "192k")))

            self.window.content_splitter.setSizes(
                self.config.get("vertical_splitter_sizes", [650, 220])
            )
            self.window.central.main_layout.setSizes(
                self.config.get("horizontal_splitter_sizes", [220, 700, 320])
            )
            self.window.responsive.restore_user_preferences(self.config)
            self.window.responsive.apply(force=True)
        except Exception as error:
            self._log_error(f"Could not restore interface settings: {error}")

    def _complete_gui_probe(self) -> None:
        """Prove that the visible GUI survived after the last book restored."""
        try:
            _PROBE_MARKER.write_text(
                json.dumps(
                    {
                        "timestamp": datetime.now().isoformat(timespec="seconds"),
                        "stage": "post-restore-visible-dwell-complete",
                        "python": sys.executable,
                    },
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )
        except Exception as error:
            self._log_error(f"Could not write GUI probe marker: {error}")
        self.app.quit()

    def _schedule_probe_completion(self) -> None:
        if not self._probe_mode:
            return
        value = os.environ.get("AUDIOBOOK_STUDIO_AUTO_EXIT_MS", "8000").strip()
        try:
            delay = max(3000, int(value))
        except ValueError:
            delay = 8000
        _write_startup_stage("probe-post-restore-dwell", str(delay))
        QTimer.singleShot(delay, self._complete_gui_probe)

    def restore_document_session(self) -> None:
        if self._document_session_restored:
            return
        self._document_session_restored = True
        _write_startup_stage("restoring-document-session")
        try:
            if self.config.get("remember_last_book", True):
                for book in reversed(self.config.recent_books()):
                    if Path(book).is_file():
                        self.sidebar.add_book(book)

                last_book = str(self.config.get("last_book", "") or "")
                if (
                    last_book
                    and not self.config.is_book_removed(last_book)
                    and Path(last_book).is_file()
                ):
                    if self._previous_session_clean:
                        _write_startup_stage("restoring-last-book", last_book)
                        self.window.controller.books.selected(last_book)
                    else:
                        self.window.log(
                            "Safe start: the previous session did not close cleanly. "
                            "The last book was kept in Library but was not opened automatically."
                        )
                        self.window.status_bar.set_message(
                            "Recovered safely • select the previous book from Library"
                        )
                        _write_startup_stage("safe-start-skipped-last-book", last_book)
            _write_startup_stage("ready")
        except Exception as error:
            self._log_error(f"Could not restore the previous book session: {error}")
            _write_startup_stage("ready-with-session-warning", str(error))
        finally:
            # Unlike R1.10, the probe remains visible only after the potentially
            # slow scanned-PDF restore has returned and all queued paints can run.
            self._schedule_probe_completion()

    def save_session(self) -> None:
        if self._probe_mode:
            return
        try:
            current_book = self.sidebar.current_book() or ""
            values = {
                "window_width": self.window.width(),
                "window_height": self.window.height(),
                "window_maximized": self.window.isMaximized(),
                "vertical_splitter_sizes": self.window.content_splitter.sizes(),
                "horizontal_splitter_sizes": self.window.central.main_layout.sizes(),
                "theme": self.window.header.current_theme(),
                "engine": self.settings.current_engine(),
                "voice": self.settings.current_voice(),
                "speed": self.settings.current_speed(),
                "pitch": self.settings.current_pitch(),
                "output_folder": str(self.window.output_folder),
                "export_wav": self.settings.export_wav.isChecked(),
                "export_mp3": self.settings.export_mp3.isChecked(),
                "export_m4b": self.settings.export_m4b.isChecked(),
                "overwrite": self.settings.overwrite.isChecked(),
                "delete_chunks": self.settings.delete_chunks.isChecked(),
                "bitrate": self.settings.export.bitrate.currentText(),
            }
            values["last_book"] = str(current_book) if current_book else ""
            values.update(self.window.responsive.preferences())
            self.config.update(values)
        except Exception as error:
            self._log_error(f"Could not save session: {error}")
        finally:
            try:
                _CLEAN_SHUTDOWN_FLAG.write_text(
                    datetime.now().isoformat(timespec="seconds") + "\n",
                    encoding="utf-8",
                )
            except Exception:
                pass

    def run(self) -> int:
        _write_startup_stage("showing-window")
        if self.config.get("window_maximized", False):
            self.window.showMaximized()
        else:
            self.window.show()
        _write_startup_stage("window-shown")

        # Defer book restoration until the first native Windows paint has
        # finished. This prevents cover scaling/layout changes from re-entering
        # QBackingStore::endPaint during initial exposure.
        QTimer.singleShot(500, self.restore_document_session)

        auto_exit = os.environ.get("AUDIOBOOK_STUDIO_AUTO_EXIT_MS", "").strip()
        if auto_exit and not self._probe_mode:
            try:
                QTimer.singleShot(max(250, int(auto_exit)), self.app.quit)
            except ValueError:
                pass

        code = int(self.app.exec())
        _write_startup_stage("event-loop-exited", str(code))
        return code


def main() -> int:
    studio = AudiobookStudio()
    return studio.run()


if __name__ == "__main__":
    raise SystemExit(main())
