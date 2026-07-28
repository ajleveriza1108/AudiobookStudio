from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtCore import QObject, QTimer


@dataclass(frozen=True)
class LayoutMode:
    name: str
    compact_header: bool
    very_compact_header: bool
    sidebar_width: int
    settings_width: int
    workspace_height: int


class ResponsiveController(QObject):
    """Adaptive panel manager that avoids impossible minimum widths.

    Wide screens can show all panels. Compact screens use narrower panels.
    Focus mode shows the reading workspace plus one side panel at a time, so
    controls never overlap or become cropped at common Windows scaling levels.
    """

    WIDE = LayoutMode("wide", False, False, 225, 330, 180)
    COMPACT = LayoutMode("compact", True, False, 180, 290, 150)
    FOCUS = LayoutMode("focus", True, True, 210, 285, 125)

    def __init__(self, window):
        super().__init__(window)
        self.window = window
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.setInterval(80)
        self._timer.timeout.connect(self.apply)
        self._mode_name = ""
        self._user_library = True
        self._user_settings = True
        self._user_activity = True
        self._focus_panel = "settings"

    def schedule(self) -> None:
        self._timer.start()

    def mode_for_width(self, width: int) -> LayoutMode:
        if width >= 1360:
            return self.WIDE
        if width >= 1040:
            return self.COMPACT
        return self.FOCUS

    def _is_focus(self) -> bool:
        widget = self.window.centralWidget()
        return bool(widget and self.mode_for_width(widget.width()).name == "focus")

    def set_library_visible(self, visible: bool) -> None:
        self._user_library = bool(visible)
        if self._is_focus():
            if visible:
                self._focus_panel = "library"
            elif self._focus_panel == "library":
                self._focus_panel = "none"
        self.apply(force=True)

    def set_settings_visible(self, visible: bool) -> None:
        self._user_settings = bool(visible)
        if self._is_focus():
            if visible:
                self._focus_panel = "settings"
            elif self._focus_panel == "settings":
                self._focus_panel = "none"
        self.apply(force=True)

    def set_activity_visible(self, visible: bool) -> None:
        self._user_activity = bool(visible)
        self.apply(force=True)

    def _effective_side_panels(self, mode: LayoutMode) -> tuple[bool, bool]:
        if mode.name != "focus":
            return self._user_library, self._user_settings

        # One side panel at a time in focus mode. Clicking Library or Settings
        # switches panels instead of squeezing the preview between both.
        if self._focus_panel == "library" and self._user_library:
            return True, False
        if self._focus_panel == "settings" and self._user_settings:
            return False, True
        return False, False

    def apply(self, force: bool = False) -> None:
        central = self.window.centralWidget()
        if central is None:
            return
        width = max(1, central.width())
        height = max(1, central.height())
        mode = self.mode_for_width(width)
        changed = mode.name != self._mode_name
        self._mode_name = mode.name

        library_visible, settings_visible = self._effective_side_panels(mode)
        activity_visible = self._user_activity and height >= 610

        self.window.central.sidebar.setVisible(library_visible)
        self.window.central.settings.setVisible(settings_visible)
        self.window.workspace.setVisible(activity_visible)
        self.window.header.set_compact(mode.compact_header, mode.very_compact_header)
        self.window.header.set_panel_states(
            library=library_visible,
            settings=settings_visible,
            activity=activity_visible,
        )
        menu = getattr(self.window, "main_menu", None)
        if menu is not None:
            for action, value in (
                (menu.show_library, library_visible),
                (menu.show_settings, settings_visible),
                (menu.show_activity, activity_visible),
            ):
                action.blockSignals(True)
                action.setChecked(bool(value))
                action.blockSignals(False)

        main = self.window.central.main_layout
        available = max(500, width - 24)
        sidebar_width = mode.sidebar_width if library_visible else 0
        settings_width = mode.settings_width if settings_visible else 0
        preview_width = max(360, available - sidebar_width - settings_width - 10)

        if force or changed:
            main.setSizes([sidebar_width, preview_width, settings_width])
            if activity_visible:
                central_height = max(350, height - mode.workspace_height - 100)
                self.window.content_splitter.setSizes([central_height, mode.workspace_height])
            else:
                self.window.content_splitter.setSizes([height, 0])

        compact = mode.name != "wide"
        self.window.central.preview.set_compact(compact)
        self.window.central.settings.set_compact(compact)
        self.window.central.sidebar.set_compact(compact)
        self.window.footer.set_compact(mode.name == "focus")

    def restore_user_preferences(self, config) -> None:
        self._user_library = bool(config.get("panel_library_visible", True))
        self._user_settings = bool(config.get("panel_settings_visible", True))
        self._user_activity = bool(config.get("panel_activity_visible", True))
        self._focus_panel = str(config.get("focus_side_panel", "settings") or "settings")
        if self._focus_panel not in {"library", "settings", "none"}:
            self._focus_panel = "settings"

    def preferences(self) -> dict:
        return {
            "panel_library_visible": self._user_library,
            "panel_settings_visible": self._user_settings,
            "panel_activity_visible": self._user_activity,
            "focus_side_panel": self._focus_panel,
        }
