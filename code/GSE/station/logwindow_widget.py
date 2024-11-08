from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from datetime import datetime

class LogWindow(QPlainTextEdit):
    def __init__(self):
        super().__init__()
        self.setReadOnly(True)
        self.setStyleSheet('border: 1px solid white; padding: 20px; font-size: 20px; line-height: 28px')

    def appendText(self, text):
        self.verticalScrollBar().setValue(self.verticalScrollBar().maximum())
        self.appendHtml(text)
        QCoreApplication.processEvents()

    def appendWarn(self, text):
        self.appendText(f'<p style="color: orange">[{datetime.now().strftime("%H:%M:%S")}] [WARN] {text:s}</p>')

    def appendInfo(self, text):
        self.appendText(f'<p style="color: white">[{datetime.now().strftime("%H:%M:%S")}] [INFO] {text:s}</p>')

    def appendSuccess(self, text):
        self.appendText(f'<p style="color: lightgreen">[{datetime.now().strftime("%H:%M:%S")}] [SUCCESS] {text:s}</p>')