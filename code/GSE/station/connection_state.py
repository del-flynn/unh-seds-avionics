from enum import Enum

class ConnectionStatus(Enum):
    Connected = 1
    Reconnecting = 2
    Disconnected = 3