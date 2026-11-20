
from iot_devices import DEVICE_HANDLERS
from ipc.pmtp_client import PTMPClient, PTMPError


class DeviceTools:
    def __init__(self, client=None):
        self.client = client if client is not None else PTMPClient()

    def _execute(self, callback):
        if self.client.connected:
            return callback()

        with self.client:
            return callback()

    def _get_handler(self, device_id):
        model = self.client.get_device_model(device_id)
        handler_class = DEVICE_HANDLERS.get(model)

        if handler_class is None:
            raise ValueError(f"Unsupported device model: {model}")

        return handler_class(self.client, device_id)

    def _discover(self):
        devices = []
        count = self.client.get_device_count()

        for index in range(count):
            try:
                device_id = self.client.get_device_name_at(index)
                model = self.client.get_device_model_at(index)

                if not device_id:
                    continue

                handler_class = DEVICE_HANDLERS.get(model)
                state = None

                if handler_class is not None:
                    try:
                        handler = handler_class(self.client, device_id)
                        state = handler.get_state()
                    except (PTMPError, OSError, ValueError):
                        pass
                else:
                    try:
                        state = self.client.get_device_property(device_id, "state")
                    except (PTMPError, OSError, ValueError):
                        pass

                devices.append({
                    "id": device_id,
                    "name": device_id,
                    "model": model,
                    "type": str(model).lower().replace(" ", "_"),
                    "state": state,
                    "available": True,
                    "controllable": handler_class is not None,
                    "actions": (
                        list(handler_class.STATES.keys())
                        if hasattr(handler_class, "STATES")
                        else list(handler_class.COMMANDS.keys())
                        if hasattr(handler_class, "COMMANDS")
                        else []
                    ),
                })

            except (PTMPError, OSError, ValueError) as error:
                devices.append({
                    "id": None,
                    "index": index,
                    "available": False,
                    "controllable": False,
                    "error": str(error),
                })

        return devices

    def list_devices(self) -> dict:
        try:
            devices = self._execute(self._discover)

            return {
                "success": True,
                "count": len(devices),
                "devices": devices,
            }

        except (PTMPError, OSError, ValueError) as error:
            return {
                "success": False,
                "count": 0,
                "devices": [],
                "error": str(error),
            }

    def get_device_state(self, device_id: str) -> dict:
        try:
            def operation():
                handler = self._get_handler(device_id)

                return {
                    "success": True,
                    "device_id": device_id,
                    "model": handler.MODEL,
                    "state": handler.get_state(),
                }

            return self._execute(operation)

        except (PTMPError, OSError, ValueError) as error:
            return {
                "success": False,
                "device_id": device_id,
                "error": str(error),
            }

    def set_device_state(self, device_id: str, state: str) -> dict:
        try:
            def operation():
                handler = self._get_handler(device_id)
                return handler.set_state(state)

            return self._execute(operation)

        except (PTMPError, OSError, ValueError) as error:
            return {
                "success": False,
                "device_id": device_id,
                "requested_state": state,
                "error": str(error),
            }
