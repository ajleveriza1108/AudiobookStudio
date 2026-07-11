from PySide6.QtWidgets import (
    QGroupBox,
    QVBoxLayout,
    QCheckBox,
)


class SettingsExport(QGroupBox):

    def __init__(self):

        super().__init__("Export")

        layout = QVBoxLayout(self)

        layout.setContentsMargins(
            12,
            16,
            12,
            12
        )

        self.export_wav = QCheckBox(

            "Export WAV"

        )

        self.export_mp3 = QCheckBox(

            "Export MP3"

        )

        self.export_m4b = QCheckBox(

            "Export M4B"

        )

        self.overwrite = QCheckBox(

            "Overwrite Existing Chunks"

        )

        self.delete_chunks = QCheckBox(

            "Delete Chunks After Merge"

        )

        self.export_wav.setChecked(

            True

        )

        layout.addWidget(

            self.export_wav

        )

        layout.addWidget(

            self.export_mp3

        )

        layout.addWidget(

            self.export_m4b

        )

        layout.addWidget(

            self.overwrite

        )

        layout.addWidget(

            self.delete_chunks

        )

        layout.addStretch()

    def options(self):

        return {

            "wav": self.export_wav.isChecked(),

            "mp3": self.export_mp3.isChecked(),

            "m4b": self.export_m4b.isChecked(),

            "overwrite": self.overwrite.isChecked(),

            "delete_chunks": self.delete_chunks.isChecked(),

        }