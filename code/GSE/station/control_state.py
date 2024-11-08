from PyQt5.QtCore import *

class ControlState(QObject):
    CONTROLS = ['logging', 'heater', 'valve_arm', 'fill_valve', 'abort_valve', 'igniter_arm', 'igniter']
    PROTECTED_CONTROLS = ['fill_valve', 'abort_valve', 'igniter_arm', 'igniter']

    state_changed = pyqtSignal(dict)
    
    def __init__(self):
        super().__init__()
        self.controls = {k: False for k in ControlState.CONTROLS}

    def update(self, target, value):
        self.controls[target] = value
        self.state_changed.emit({'state': self.controls})
    
    def get(self, target):
        return self.controls[target]
    
    def get_all(self):
        return self.controls
    
    def update_all(self, data):
        self.controls = data