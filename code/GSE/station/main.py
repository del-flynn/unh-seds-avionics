from PyQt5.QtWidgets import *
from main_widget import MainWidget
import sys
import signal

def main():
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    app = QApplication(sys.argv)
    main_widget = MainWidget()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()