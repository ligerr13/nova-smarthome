
from abc import ABC, abstractmethod
from ipc.pmtp_client import PTMPClient

class BaseIoTDevice(ABC):
    MODEL = None

    def __init__(self, client: PTMPClient, device_id: str):
        self.client = client
        self.device_id = device_id

    def get_state(self):
        return self.client.get_device_property(self.device_id, "state")

    @abstractmethod
    def set_state(self, state: str) -> dict:
        pass

    def get_info(self) -> dict:
        return {
            "id": self.device_id,
            "model": self.MODEL,
            "state": self.get_state(),
        }
