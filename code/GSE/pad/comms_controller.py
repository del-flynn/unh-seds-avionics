import socket
import time
from threading import Thread, Event
from queue import Queue
from json import dumps, loads
from controls_handler import ControlState, ControlsHandler
from daq import DAQController

LOCAL_ADDR = ''
SERVER_PORT = 42069
#     Station           Pad 
#       control messages ->>>
#        heartbeat (1/s) <<<-
#        data <<<-   

# Send AND receive data at the same time asynchronously
# Need to determine data reliability
# Want to package your data into discrete chunks (datagrams) (no streams)
# Take a look at gRPC for handling communication

# Requirements:
# - Send control messages to pad to control valves (and calibrate sensors)
# - Send data from sensors (pad->station)
# - Make sure pad has some kind of continuous connection so we can automatically
#   reconnect if it disconnects
# - Verify control state of pad

class CommsController():
    def __init__(self, controls_handler: ControlsHandler, daq_controller: DAQController):
        self.last_ping = 0
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind((LOCAL_ADDR, SERVER_PORT,))

        self.peer = None

        self.controls_handler = controls_handler
        self.daq_controller = daq_controller

        self.outbound_queue = Queue()
        self.inbound_queue = Queue()

        self.is_connected = Event()

        self.send_thread = Thread(target=self.send_loop, daemon=True)
        self.send_thread.start()

        self.recv_thread = Thread(target=self.recv_loop, daemon=True)
        self.recv_thread.start()

        self.process_thread = Thread(target=self.process_loop, daemon=True)
        self.process_thread.start()

    def connection_loop(self):
        while True:
            self.is_connected.clear()
            print('[INFO] Waiting for connection...')

            init_msg, addr = self.sock.recvfrom(16384)
            self.peer = addr
            self.is_connected.set()
            print(f'[INFO] Connected to {addr}')    
            self.daq_controller.start()

            self.last_ping = time.time()
            while self.is_connected.is_set():
                self.send_msg({'heartbeat': True})
                current_time = time.time()
                if (current_time - self.last_ping) > 10.0:
                    print('[WARN] Connection timed out!')
                    self.daq_controller.stop()
                    self.is_connected.clear()
                time.sleep(1.0)

    def send_msg(self, msg: dict):
        if self.is_connected.is_set():
            self.outbound_queue.put_nowait(msg)

    def send_loop(self):
        while True:
            self.is_connected.wait()
            start_time = time.time()
            while self.is_connected.is_set() and self.peer is not None:
                data = self.outbound_queue.get()
                self.sock.sendto(dumps(data).encode('gbk'), self.peer)

    def recv_loop(self):
        while True:
            self.is_connected.wait()
            while self.is_connected.is_set() and self.peer is not None:
                data, _ = self.sock.recvfrom(16384)
                self.inbound_queue.put(data)
                self.last_ping = time.time()
    
    def process_loop(self):
        while True:
            self.is_connected.wait()
            while self.is_connected.is_set() and self.peer is not None:
                data = self.inbound_queue.get()
                msg = loads(data.decode('gbk'))
                if 'state' in msg:
                    self.controls_handler.handle_new_state(ControlState(msg['state']), self)

                if 'zero' in msg:
                    self.daq_controller.zero(msg['zero'])
                
                if 'calibrate' in msg:
                    self.daq_controller.calibrate(msg['calibrate']['name'], msg['calibrate']['val'])
                
