from PySide6.QtWidgets import QMessageBox

from core.version import APP_NAME, AUTHOR, VERSION


def show_about(parent):
    QMessageBox.about(
        parent,
        APP_NAME,
        f"""
<h2>{APP_NAME}</h2>
<p><b>Offline book-to-audiobook production workspace</b></p>
<ul>
<li>PDF and EPUB preparation review</li>
<li>Editable chapter plan and safe pronunciation rules</li>
<li>Kokoro local narration with verified resume</li>
<li>WAV, tagged MP3, and chapter-aware M4B export</li>
<li>Audio quality and preparation reports</li>
<li>Batch queue, live progress, OLED Black, and Dirty White themes</li>
</ul>
<p>Version {VERSION}<br>Project owner: {AUTHOR}</p>
""",
    )
