
from iot_devices.base import BaseIoTDevice


class DoorDevice(BaseIoTDevice):
    MODEL = "Door"
    PROJECT = "Door (JavaScript)"

    COMMANDS = {
        "open": ("openDoor();", "door", "1"),
        "close": ("closeDoor();", "door", "0"),
        "lock": ("setLockState(1);", "lock", "1"),
        "unlock": ("setLockState(0);", "lock", "0"),
    }

    def get_state(self) -> dict:
        door = self.client.get_device_property(self.device_id, "door state")
        lock = self.client.get_device_property(self.device_id, "lock state")

        return {
            "door": door,
            "lock": lock,
            "is_open": door == "1",
            "is_locked": lock == "1",
        }

    def set_state(self, state: str) -> dict:
        normalized = str(state).strip().lower()

        if normalized not in self.COMMANDS:
            raise ValueError(f"Unsupported door action: {state}")

        code, field, target = self.COMMANDS[normalized]

        result = self.client.run_device_code(
            self.device_id,
            self.PROJECT,
            code,
        )

        actual = self.get_state()
        success = actual[field] == target

        return {
            "success": success,
            "device_id": self.device_id,
            "model": self.MODEL,
            "requested_state": normalized,
            "state": actual,
            "ipc_result": result,
            "error": None if success else "Door state verification failed",
        }
