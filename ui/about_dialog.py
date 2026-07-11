from PySide6.QtWidgets import QMessageBox


def show_about(parent):

    QMessageBox.about(

        parent,

        "Audiobook Studio",

        """
<h2>Audiobook Studio</h2>

Professional AI Audiobook Generator

• PDF
• EPUB
• Kokoro
• Resume Support
• Batch Queue
• MP3
• M4B

Version 1.0
"""
    )