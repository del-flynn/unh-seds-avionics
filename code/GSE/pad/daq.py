import time, random, board, busio, PyNAU7802, smbus2 
from json import dumps, loads
from datetime import datetime
from threading import Thread, Event, Lock
from queue import Queue
import numpy as np

class DAQController():
    def __init__(self):
        self.running = Event()
        self.logging = Event()
        self.measurement_lock = Lock()
        self.process_queue = Queue()

        self.ack_thread = Thread(target=self.collect_data, daemon=True)
        self.proc_thread = Thread(target=self.process_data, daemon=True)

        self.cals = {}

        try:
            with open('cals.json', 'r') as f:
                contents = loads(f.read())

                if 'loadcell' in contents and 'zero' in contents['loadcell'] and 'cal' in contents['loadcell']:
                    self.cals['loadcell'] = contents['loadcell']
                else:
                    self.cals['loadcell'] = {'zero': 1.0, 'cal': 1.0}

                if 'pressuretap' in contents and 'zero' in contents['pressuretap'] and 'cal' in contents['pressuretap']:
                    self.cals['pressuretap'] = contents['pressuretap']
                else:
                    self.cals['pressuretap'] = {'zero': 1400.0, 'cal': 1.0}
        except FileNotFoundError:

            self.cals['loadcell'] = {'zero': 1.0, 'cal': 1.0}
            self.cals['pressuretap'] = {'zero': 1400.0, 'cal': 1.0}
            pass

        with open('cals.json', 'w') as f:
            f.write(dumps(self.cals))

        # Initialize NAU7802 for load cell (I2C bus 1)
        self.bus_lc = smbus2.SMBus(1)  # I2C-1 for load cell
        self.lc = PyNAU7802.NAU7802()

        if not self.lc.begin(self.bus_lc):
            raise RuntimeError("Failed to initialize NAU7802 for load cell!")
            
        # Load cell initialiation
        self.lc.setZeroOffset(self.cals['loadcell']['zero'])
        self.lc.setCalibrationFactor(self.cals['loadcell']['zero'])

        self.bus_pt = smbus2.SMBus(3)  # I2C-3 for pressure tap
        self.pt = PyNAU7802.NAU7802()

        if not self.pt.begin(self.bus_pt):
            raise RuntimeError("Failed to initialize NAU7802 for pressure tap!")

        # Create the scale and initialize it
        self.lc = PyNAU7802.NAU7802()
        if not self.lc.begin(self.bus):
            self.lc = None        

        self.outbound = None
        self.filename = None

    def start(self):
        self.running.set()
    
    def stop(self):
        self.running.clear()

    def start_logging(self):
        self.filename = datetime.now().strftime("data/%d%m%Y-%H%M%S.csv")
        with open(self.filename, 'w') as file:
            file.write('time,loadcell,pressuretap')
        self.logging.set()

    def stop_logging(self):
        self.logging.clear()

    def connect_outbound(self, outbound):
        self.outbound = outbound
        self.ack_thread.start()
        self.proc_thread.start()

    def zero(self, target):
        with self.measurement_lock:
            if target == 'loadcell' and self.lc is not None:
                self.lc.calculateZeroOffset()
                self.cals['loadcell']['zero'] = self.lc.getZeroOffset()
            elif target == 'pressuretap':
                measurements = np.empty(10)
                for i in range(10):
                    measurements[i] = self.get_pressuretap()
                    time.sleep(0.1)
                
                self.cals['pressuretap']['zero'] = np.average(measurements)

            with open('cals.json', 'w') as f:
                f.write(dumps(self.cals))
            
            self.outbound.send_msg({"info": f'Instrument {target} zeroed!'})

    def calibrate(self, target, value):
        with self.measurement_lock:
            if target == 'loadcell' and self.lc is not None:
                self.lc.calculateCalibrationFactor(value)
                self.cals['loadcell']['cal'] = self.lc.getCalibrationFactor()
            elif target == 'pressuretap':
                measurements = np.empty(10)
                for i in range(10):
                    measurements[i] = self.get_pressuretap()
                    time.sleep(0.1)
                
                self.cals['pressuretap']['cal'] = np.average(measurements) / value

            with open('cals.json', 'w') as f:
                f.write(dumps(self.cals))

            self.outbound.send_msg({"info": f'Instrument {target} calibrated!'})

    def collect_data(self):
        resolution = 20.0

        start_time = time.time()
        
        while True:
            self.running.wait()
            while self.running.is_set():
                with self.measurement_lock:
                    t_s = time.time()
                    current_time = time.time() - start_time
                    self.process_queue.put_nowait([round(current_time, 4), self.get_loadcell(), self.get_pressuretap()])
                    time.sleep(max((1.0 / resolution) - (time.time() - t_s), 0.0))

    def process_data(self):
        while True:
            self.running.wait()
            last_ping = time.time()
            time_data = []
            lc_data = []
            pt_data = []
            while self.running.is_set():
                data = self.process_queue.get()
                time_data.append(data[0])
                lc_data.append(data[1])
                pt_data.append(data[2])

                if self.logging.is_set():
                    with open(self.filename, 'a') as file:
                        file.write(f'\n{data[0]},{data[1]},{data[2]}')

                if time.time() - last_ping > 1.0:
                    last_ping = time.time()
                    self.outbound.send_msg({'data': {'loadcell': [time_data, lc_data], 'pressuretap': [time_data, pt_data]}})
                    time_data = []
                    lc_data = []
                    pt_data = []

    def get_loadcell(self):
        with self.measurement_lock:
            return self.lc.getWeight()

    def get_pressuretap(self):
        with self.measurement_lock:
            return round((self.pt.getWeight() - self.cals['pressuretap']['zero']) / self.cals['pressuretap']['cal'], 4)