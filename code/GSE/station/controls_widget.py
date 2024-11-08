from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from control_state import ControlState
from connection_state import ConnectionStatus

class ControlsWidget(QWidget):
    def __init__(self, control_state):
        super().__init__()

        self.control_state = control_state
        self.control_widgets = {k: QPushButton(k.replace('_', ' ').title().replace('Arm', 'ARM'), self) for k in ControlState.CONTROLS}
        
        vbox = QVBoxLayout()
        label = QLabel("CONTROLS")
        label.setFont(QFont('Arial', 30))
        label.resize(200, 50)
        label.setAlignment(Qt.AlignCenter)
        label.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        vbox.addWidget(label)
        for name, button in self.control_widgets.items():
            button.resize(200, 200)
            button.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
            button.setObjectName(name)
            button.setFont(QFont('Arial', 24))
    
            # setting calling method by button
            button.clicked.connect(self.controlUpdate)
            if name in ControlState.PROTECTED_CONTROLS:
                button.setDisabled(True)
            self.update_button_status(name, False) 
    
            # setting default color of button to light-grey
            vbox.addWidget(button)

        self.setLayout(vbox)
    
    def controlUpdate(self):
        target = self.sender().objectName()
        new_status = not self.control_state.get(target)

        if target == 'valve_arm':
            to_enable = ['fill_valve', 'abort_valve', 'igniter_arm']
            to_disable = ['fill_valve', 'abort_valve', 'igniter_arm', 'igniter']
            if new_status:
                for dep in to_enable:
                    self.control_widgets[dep].setEnabled(True)
                    self.update_button_status(dep, False)
            else:
                for dep in to_disable:
                    self.control_widgets[dep].setDisabled(True)
                    self.update_button_status(dep, False)
        elif target == 'igniter_arm':
            self.control_widgets['igniter'].setEnabled(new_status)
            self.update_button_status('igniter', False)
        
        self.update_button_status(target, new_status)
    
    def update_button_status(self, target, status):
        self.control_state.update(target, status)
        button = self.control_widgets[target]
        if button.isEnabled():
            if status:
                button.setStyleSheet("background-color : green; color: black")
            else: 
                button.setStyleSheet("background-color : red; color: black")
        else:
            button.setStyleSheet("background-color : lightgrey; color: black")

    def update_all_status(self, status: ConnectionStatus):
        pass