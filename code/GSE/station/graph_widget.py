from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5 import QtCore
import numpy as np
import pyqtgraph as pg

class GraphWidget(QWidget):
    zero_sig = QtCore.pyqtSignal(dict)
    cal_sig = QtCore.pyqtSignal(dict)
    log_info = QtCore.pyqtSignal(str)
    
    def __init__(self, title, slug, unit):
        super().__init__()
        layout = QVBoxLayout()

        self.plot_widget = pg.PlotWidget()
        self.data_line = None
        self.xdata = None
        self.ydata = None

        label = QLabel(f'{title:s} ({unit:s})')
        label.setFont(QFont('Arial', 24))
        label.setStyleSheet('margin-left: 40px')

        self.title = title
        self.slug = slug
        self.unit = unit
        self.indicator_label = QLabel(f'- {unit:s}')
        self.indicator_label.setFont(QFont('Arial', 24))
        self.indicator_label.setStyleSheet('border: 2px solid white; padding: 10px')
        self.indicator_label.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)

        self.zero_button = QPushButton("Zero")
        self.zero_button.clicked.connect(self.zero)
        self.zero_button.setFont(QFont('Arial', 16))
        self.zero_button.setCursor(QCursor(QtCore.Qt.PointingHandCursor))
        self.zero_button.setStyleSheet('border: 2px solid white; border-radius: 5px; padding: 5px; background: #dddddd; color: #000000')

        self.cal_button = QPushButton("Calibrate")
        self.cal_button.clicked.connect(self.calibrate)
        self.cal_button.setFont(QFont('Arial', 16))
        self.cal_button.setCursor(QCursor(QtCore.Qt.PointingHandCursor))
        self.cal_button.setStyleSheet('border: 2px solid white; border-radius: 5px; padding: 5px; background: #dddddd; color: #000000')

        self.clear_button = QPushButton("Clear")
        self.clear_button.clicked.connect(self.clear)
        self.clear_button.setFont(QFont('Arial', 16))
        self.clear_button.setCursor(QCursor(QtCore.Qt.PointingHandCursor))
        self.clear_button.setStyleSheet('border: 2px solid white; border-radius: 5px; padding: 5px; background: #dddddd; color: #000000')

        self.indicator_controls_layout = QVBoxLayout()
        self.indicator_controls_layout.addWidget(self.indicator_label)
        self.indicator_controls_layout.addWidget(self.zero_button)
        self.indicator_controls_layout.addWidget(self.cal_button)
        self.indicator_controls_layout.addWidget(self.clear_button)

        graph_layout = QHBoxLayout()
        graph_layout.addWidget(self.plot_widget)
        graph_layout.addLayout(self.indicator_controls_layout)
        
        graph_label_layout = QVBoxLayout()
        graph_label_layout.addWidget(label)
        graph_label_layout.addLayout(graph_layout)
        self.setLayout(graph_label_layout)
        
    def handle_data(self, data):
        if self.data_line is None:
            self.xdata = data[0]
            self.ydata = data[1]
            self.data_line = self.plot_widget.plot(self.xdata, self.ydata)
        elif len(data) == 2 and len(data[0]) == len(data[1]) and len(data[0]) > 0:
            self.xdata.extend(data[0])
            self.ydata.extend(data[1])
            self.data_line.setData(self.xdata, self.ydata)
        
        self.indicator_label.setText(f'{self.ydata[len(self.ydata) - 1]:.1f} {self.unit:s}')

    def zero(self):
        status = QMessageBox.question(self,f'{self.title} Zeroing', 'Are you sure you want to zero?', QMessageBox.Yes | QMessageBox.No)

        if status == QMessageBox.Yes:
            self.log_info.emit(f'Zeroing instrument {self.title}')
            self.zero_sig.emit({"zero": self.slug})

    def calibrate(self):
        num, ok = QInputDialog.getDouble(self,f'{self.title} Calibration',f'Enter the calibration value in {self.unit}')
            
        if ok and num > 1.0:
            self.log_info.emit(f'Calibrating instrument {self.title}')
            self.cal_sig.emit({"calibrate": {"name": self.slug, "val": num}})

    def clear(self):
        if self.data_line is not None:
            self.data_line.clear()
            self.data_line = None
            self.xdata = []
            self.ydata = []
            self.num_data_points = 0

    def get_data(self):
        return (self.xdata, self.ydata)
