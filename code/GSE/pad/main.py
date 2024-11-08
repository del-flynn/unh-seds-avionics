from comms_controller import CommsController
from controls_handler import ControlsHandler
from daq import DAQController

daq_controller = DAQController()
# code monkey deployed
controls_handler = ControlsHandler(daq_controller)

comms_controller = CommsController(controls_handler, daq_controller)
daq_controller.connect_outbound(comms_controller)
comms_controller.connection_loop()