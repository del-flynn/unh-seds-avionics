from PyQt5.QtWidgets import *
from control_state import ControlState
from controls_widget import ControlsWidget
from graph_widget import GraphWidget
from status_widget import StatusWidget
from comms_controller import CommsController
from statevisualizer_widget import StateVisualizer
from logwindow_widget import LogWindow
from datetime import datetime

class MainWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.control_state = ControlState()
        self.controls_widget = ControlsWidget(self.control_state)
        self.status_widget = StatusWidget()
        self.status_widget.save_button.clicked.connect(self.save_data)

        self.lc_graph = GraphWidget('Load Cell', 'loadcell', 'lbf')
        self.pt_graph = GraphWidget('Pressure Tap', 'pressuretap', 'psi')

        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setLineWidth(3)

        graph_layout = QVBoxLayout()
        graph_layout.addWidget(self.lc_graph)
        graph_layout.addWidget(line)
        graph_layout.addWidget(self.pt_graph)

        self.state_visualizer = StateVisualizer()
        self.log_window = LogWindow()
        self.lc_graph.log_info.connect(self.log_window.appendInfo)
        self.pt_graph.log_info.connect(self.log_window.appendInfo)

        state_logging_layout = QVBoxLayout()
        state_logging_layout.addWidget(self.state_visualizer)
        state_logging_layout.addWidget(self.log_window)

        layout = QGridLayout()
        layout.addWidget(self.controls_widget, 0, 0)
        layout.addLayout(graph_layout, 0, 2)
        layout.addLayout(state_logging_layout, 0, 1)
        layout.addWidget(self.status_widget, 1, 0, 1, 3)
        self.setLayout(layout)

        self.comms_controller = CommsController(self.log_window)
        self.comms_controller.status_changed.connect(self.status_widget.update_status)
        self.comms_controller.status_changed.connect(self.controls_widget.update_all_status)

        self.comms_controller.register(self.lc_graph, 'loadcell')
        self.comms_controller.register(self.pt_graph, 'pressuretap')
        self.control_state.state_changed.connect(self.comms_controller.send_msg)
        self.lc_graph.zero_sig.connect(self.comms_controller.send_msg)
        self.lc_graph.cal_sig.connect(self.comms_controller.send_msg)
        self.pt_graph.zero_sig.connect(self.comms_controller.send_msg)
        self.pt_graph.cal_sig.connect(self.comms_controller.send_msg)
        
        self.setGeometry(100, 100, 2000, 1000)
        self.setStyleSheet('background-color: black; color: white')
        self.setWindowTitle("GSE Control")
        self.show()

    def save_data(self):
        pt_data = self.pt_graph.get_data()
        lc_data = self.lc_graph.get_data()
        
        if pt_data is not None and len(pt_data) == 2 and pt_data[0] is not None and pt_data[1] is not None:
            pt_filename = datetime.now().strftime("%d%m%Y-%H%M%S-pt.csv")
            with open(pt_filename, 'w') as file:
                file.write('time, pressure')
                file.writelines(f'\n{t}, {v}' for t, v in zip(pt_data[0], pt_data[1]))
        else:
            self.log_window.appendWarn('Pressure tap data is blank!')

        if lc_data is not None and len(lc_data) == 2 and lc_data[0] is not None and lc_data[1] is not None:
            lc_filename = datetime.now().strftime("%d%m%Y-%H%M%S-lc.csv")
            with open(lc_filename, 'w') as file:
                file.write('time, force')
                file.writelines(f'\n{t}, {v}' for t, v in zip(lc_data[0], lc_data[1]))
        else:
            self.log_window.appendWarn('Load cell data is blank!')

        self.log_window.appendInfo('Data saved locally!')