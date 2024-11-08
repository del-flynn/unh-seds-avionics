from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5 import QtCore
from connection_state import ConnectionStatus

class StatusWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.status = ConnectionStatus.Disconnected
        layout = QHBoxLayout()
        label = QLabel('STATUS:')
        label.setFont(QFont('Arial', 30))

        self.status_label = QLabel('DISCONNECTED')
        self.status_label.setFont(QFont('Arial', 30))
        self.update_status(self.status)

        self.save_button = QPushButton("Save Data")
        self.save_button.setFont(QFont('Arial', 20))
        self.save_button.setCursor(QCursor(QtCore.Qt.PointingHandCursor))
        self.save_button.setStyleSheet('border: 2px solid white; border-radius: 5px; padding: 5px; background: #dddddd; color: #000000')

        layout.addStretch()
        layout.addWidget(label)
        layout.addWidget(self.status_label)
        layout.addStretch()
        layout.addWidget(self.save_button)
        self.setLayout(layout)

    def update_status(self, status: ConnectionStatus):
        self.status = status
        if self.status == ConnectionStatus.Connected:
            self.status_label.setStyleSheet('color: lightgreen')
            self.status_label.setText('CONNECTED')
        elif self.status == ConnectionStatus.Reconnecting:
            self.status_label.setStyleSheet('color: orange')
            self.status_label.setText('RECONNECTING')
        else:
            self.status_label.setStyleSheet('color: red')
            self.status_label.setText('DISCONNECTED')

        
        