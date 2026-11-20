
from iot_devices.base import BaseIoTDevice


class WindowDevice(BaseIoTDevice):
    MODEL = "Window"
    PROJECT = "Window (JavaScript)"

    STATES = {
        "open": 1,
        "close": 0,
        "opened": 1,
        "closed": 0,
        "1": 1,
        "0": 0,
    }

    def set_state(self, state: str) -> dict:
        normalized = str(state).strip().lower()

        if normalized not in self.STATES:
            raise ValueError(f"Unsupported window state: {state}")

        target = self.STATES[normalized]

        result = self.client.run_device_code(
            self.device_id,
            self.PROJECT,
            f"setState({target});",
        )

        actual = self.get_state()
        success = actual == str(target)

        return {
            "success": success,
            "device_id": self.device_id,
            "model": self.MODEL,
            "requested_state": normalized,
            "state": actual,
            "ipc_result": result,
            "error": None if success else "Window state verification failed",
        }
