import socket
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from connection_state import ConnectionStatus
from logwindow_widget import LogWindow
from time import sleep, time
from json import dumps, loads
import queue

class ConnectionWatchdog(QThread):
    conn_timeout = pyqtSignal()

    def __init__(self):
        super(ConnectionWatchdog, self).__init__()
        self.deadline = time()

    def run(self):
        while True:
            if time() > self.deadline:
                self.conn_timeout.emit()

    def update_time(self):
        self.deadline = time() + 5.0

class ConnectionThread(QThread):
    conn_status_changed = pyqtSignal(ConnectionStatus)
    log_warn = pyqtSignal(str)
    log_info = pyqtSignal(str)
    peer_changed = pyqtSignal(str)

    def __init__(self, parent, sock, log_window: LogWindow):
        super(ConnectionThread, self).__init__(parent)
        self.connection_status = ConnectionStatus.Disconnected
        self.peer = ''

        self.parent = parent
        self.sock = sock

        self.log_warn.connect(log_window.appendWarn)
        self.log_info.connect(log_window.appendInfo)
        self.conn_status_changed.connect(parent.update_connection_status)

    def run(self):
        while True:
            self.conn_status_changed.emit(ConnectionStatus.Reconnecting)

            try:
                self.peer = socket.gethostbyname(CommsController.REMOTE_NAME)
            except socket.gaierror:
                self.conn_status_changed.emit(ConnectionStatus.Disconnected)
                self.log_warn.emit('DAQ not found on network!')
                sleep(5)
                continue

            # if not failed:
            #     try:
            #         self.sock.connect((self.peer, CommsController.REMOTE_PORT))
            #     except OSError as msg:
            #         self.connection_status = ConnectionStatus.Disconnected
            #         self.conn_status_changed.emit(ConnectionStatus.Disconnected)
            #         self.log_warn.emit(f'Could not connect to DAQ: {msg}')
            #         connected = False
            #         sleep(5)
                

            for _ in range(5):
                if self.parent.connection_status == ConnectionStatus.Reconnecting:
                    self.sock.sendto(dumps({'connect': True}).encode('gbk'), (self.peer, CommsController.REMOTE_PORT))
                    sleep(1)

            if self.parent.connection_status == ConnectionStatus.Connected:
                self.log_info.emit('Connected!')
                self.conn_status_changed.emit(ConnectionStatus.Connected)
                self.peer_changed.emit(self.peer)
            else:
                self.log_warn.emit('Failed to connect!')

            while self.parent.connection_status == ConnectionStatus.Connected:
                try:
                    self.sock.sendto(dumps({'heartbeat': True}).encode('gbk'), (self.peer, CommsController.REMOTE_PORT))
                    sleep(1)
                except Exception as e:
                    self.log_warn.emit(f'BALLS: {e}')
                    break
            sleep(5)

    def on_msg_recv(self, msg):
        if self.parent.connection_status == ConnectionStatus.Reconnecting:
            self.conn_status_changed.emit(ConnectionStatus.Connected)

    def conn_interrupted(self):
        self.connection_status = ConnectionStatus.Disconnected

class SendThread(ConnectionThread):
    def __init__(self, parent, sock, log_window: LogWindow):
        super().__init__(parent, sock, log_window)
        self.send_queue = queue.Queue()
        self.num_failed = 0
        self.peer = ''

    def queue_msg(self, msg: dict):
        if self.parent.connection_status == ConnectionStatus.Connected and self.peer != '':
            self.send_queue.put_nowait(msg)
        else:
            self.log_warn.emit('Error sending message: Not connected to DAQ!')

    def run(self):
        while True:
            try:
                msg = self.send_queue.get()
                if self.parent.connection_status == ConnectionStatus.Connected:
                    self.sock.sendto(dumps(msg).encode('gbk'), (self.peer, CommsController.REMOTE_PORT))
                else:
                    self.log_warn.emit(f'Discarding message: {dumps(e)}')
            except Exception as e:
                self.log_warn.emit(f'Error sending message: {e}')
                self.num_failed += 1
                if self.num_failed >= 5:
                    self.conn_status_changed.emit(ConnectionStatus.Disconnected)

    def update_peer(self, peer):
        self.peer = peer

class RecvThread(ConnectionThread):
    msg_received = pyqtSignal(dict)

    def run(self):
        while True:
            try:
                data, _ = self.sock.recvfrom(16384)
                # print('got message')
                self.msg_received.emit(loads(data.decode('gbk')))
            except Exception as e:
                self.log_warn.emit(f'Error receiving message: {e}')

class CommsController(QObject):
    REMOTE_NAME = 'gse-daq.local'
    # REMOTE_NAME = '127.0.0.1'
    REMOTE_PORT = 42069
    LOCAL_PORT = 42070

    status_changed = pyqtSignal(ConnectionStatus)
    
    def __init__(self, log_window: LogWindow):
        super().__init__()
        self.connection_status = ConnectionStatus.Disconnected

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(('0.0.0.0', CommsController.LOCAL_PORT))

        self.log_window = log_window

        self.watchdog = ConnectionWatchdog()

        self.connection_thread = ConnectionThread(self, self.sock, log_window)
        self.watchdog.conn_timeout.connect(self.connection_thread.conn_interrupted)
        
        self.send_thread = SendThread(self, self.sock, log_window)

        self.recv_thread = RecvThread(self, self.sock, log_window)
        self.recv_thread.msg_received.connect(self.handle_msg)
        self.recv_thread.msg_received.connect(self.connection_thread.on_msg_recv)

        self.connection_thread.peer_changed.connect(self.send_thread.update_peer)
        self.connection_thread.start()
        self.send_thread.start()
        self.recv_thread.start()
        
        self.listeners = {}
        
    def update_connection_status(self, status: ConnectionStatus):
        self.connection_status = status
        self.status_changed.emit(self.connection_status)
    
    def send_msg(self, msg: dict):
        self.send_thread.queue_msg(msg)

    def register(self, target: str, name: str):
        self.listeners[name] = target

    def handle_msg(self, msg: dict):
        if 'data' in msg:
            for target in self.listeners:
                if target in msg['data']:
                    self.listeners[target].handle_data(msg['data'][target])
        elif 'info' in msg:
            self.log_window.appendInfo(msg['info'])
        elif 'warn' in msg:
            self.log_window.appendWarn(msg['warn'])
    