from __future__ import annotations


class ConsoleLogger:
    def __init__(self, console):
        self.console = console

    def write(self, message):
        text = str(message)
        if hasattr(self.console, "appendPlainText"):
            self.console.appendPlainText(text)
        else:
            self.console.append(text)

        bar = self.console.verticalScrollBar()
        bar.setValue(bar.maximum())

    def log(self, message):
        self.write(message)

    __call__ = write
