import RPi.GPIO as GPIO

class ControlState():
    CONTROLS = ['logging', 'heater', 'valve_arm', 'fill_valve', 'abort_valve', 'igniter_arm', 'igniter']
    
    def __init__(self, controls=None):
        if controls is not None:
            self.update_all(controls)
        else:
            self.controls = {k: False for k in ControlState.CONTROLS}

    def update(self, target, value):
        self.controls[target] = value
    
    def get(self, target):
        return self.controls[target]
    
    def get_all(self):
        return self.controls
    
    def update_all(self, data):
        self.controls = {k: data[k] if k in data else False for k in ControlState.CONTROLS}
    
    def xor(self, data):
        state = {}
        for k in ControlState.CONTROLS:
            state[k] = self.controls[k] or data.get(k) and not (self.controls[k] and data.get(k))
        return state

class ControlsHandler():
    HEATER_PIN = 18
    FILL_PIN = 24
    ABORT_PIN = 25
    IGNITER_PIN = 23

    def __init__(self, daq_controller):
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(ControlsHandler.HEATER_PIN, GPIO.OUT)
        GPIO.setup(ControlsHandler.FILL_PIN, GPIO.OUT)
        GPIO.setup(ControlsHandler.ABORT_PIN, GPIO.OUT)
        GPIO.setup(ControlsHandler.IGNITER_PIN, GPIO.OUT)

        GPIO.output(ControlsHandler.HEATER_PIN, GPIO.LOW)
        GPIO.output(ControlsHandler.FILL_PIN, GPIO.LOW)
        GPIO.output(ControlsHandler.ABORT_PIN, GPIO.LOW)
        GPIO.output(ControlsHandler.IGNITER_PIN, GPIO.LOW)

        self.daq = daq_controller

        self.current_state = ControlState()

    def handle_new_state(self, state: ControlState, responder):
        changes = self.current_state.xor(state)
        if changes['logging']:
            self.current_state.update('logging', state.get('logging'))
            if state.get('logging'):
                self.daq.start_logging()
                responder.send_msg({'info': 'Logging activated'})
            else:
                self.daq.stop_logging()
                responder.send_msg({'info': 'Logging deactivated'})
        
        if changes['heater']:
            self.current_state.update('heater', state.get('heater'))
            if state.get('heater'):
                GPIO.output(ControlsHandler.HEATER_PIN, GPIO.HIGH if state['heater'] else GPIO.LOW)
                responder.send_msg({'info': 'Heater activated'})
            else:
                GPIO.output(ControlsHandler.HEATER_PIN, GPIO.LOW)
                responder.send_msg({'info': 'Heater deactivated'})

        if changes['valve_arm']:
            self.current_state.update('valve_arm', state.get('valve_arm'))
            if not state.get('valve_arm'):
                responder.send_msg({'info': 'Valves disarmed'})
                self.current_state.update('fill_valve', False)
                GPIO.output(ControlsHandler.FILL_PIN, GPIO.LOW)

                self.current_state.update('abort_valve', False)
                GPIO.output(ControlsHandler.ABORT_PIN, GPIO.LOW)

                self.current_state.update('abort_valve', False)
                GPIO.output(ControlsHandler.HEATER_PIN, GPIO.HIGH)
                
                self.current_state.update('igniter_arm', False)
                self.current_state.update('igniter', False)
                GPIO.output(ControlsHandler.IGNITER_PIN, GPIO.LOW)
            else:
                responder.send_msg({'info': 'Valves armed'})

        if changes['fill_valve']:
            if state.get('fill_valve') and self.current_state.get('valve_arm'):
                self.current_state.update('fill_valve', True)
                GPIO.output(ControlsHandler.FILL_PIN, GPIO.HIGH)
                responder.send_msg({'info': 'Fill valve opened'})
            else:
                self.current_state.update('fill_valve', False)
                GPIO.output(ControlsHandler.FILL_PIN, GPIO.LOW)
                responder.send_msg({'info': 'Fill valve closed'})

        if changes['abort_valve']:
            if state.get('abort_valve') and self.current_state.get('valve_arm'):
                self.current_state.update('abort_valve', True)
                GPIO.output(ControlsHandler.ABORT_PIN, GPIO.HIGH)
                responder.send_msg({'info': 'Abort valve opened'})
            else:
                self.current_state.update('abort_valve', False)
                GPIO.output(ControlsHandler.ABORT_PIN, GPIO.LOW)
                responder.send_msg({'info': 'Abort valve closed'})

        if changes['igniter_arm']:
            self.current_state.update('igniter_arm', state.get('igniter_arm'))
            if not state.get('igniter_arm'):
                responder.send_msg({'info': 'Igniter disarmed'})
                self.current_state.update('igniter_arm', False)
                self.current_state.update('igniter', False)
                GPIO.output(ControlsHandler.IGNITER_PIN, GPIO.LOW)
            else:
                responder.send_msg({'info': 'Igniter armed'})

        if changes['igniter']:
            if state.get('igniter') and self.current_state.get('igniter_arm'):
                self.current_state.update('igniter', True)
                GPIO.output(ControlsHandler.IGNITER_PIN, GPIO.HIGH)
                responder.send_msg({'info': 'Igniter activated'})
            else:
                self.current_state.update('igniter', False)
                GPIO.output(ControlsHandler.IGNITER_PIN, GPIO.LOW)
                responder.send_msg({'info': 'Igniter deactivated'})

        