
import os
import socket
import time
import uuid


class PTMPError(Exception):
    pass


class PTMPClient:
    def __init__(self, host=None, port=None, username=None, password=None, timeout=10, debug=False):
        self.host = host or os.getenv("NOVA_PT_HOST", "127.0.0.1")
        self.port = int(port if port is not None else os.getenv("NOVA_PT_PORT", "39000"))
        self.username = username or os.getenv("NOVA_PT_USERNAME", "hu.nova.smarthome")
        self.password = password if password is not None else os.getenv("NOVA_PT_PASSWORD")
        self.timeout = timeout
        self.debug = debug
        self.sock = None
        self.buffer = b""
        self.call_id = 0

    @property
    def connected(self):
        return self.sock is not None

    def _log(self, message):
        if self.debug:
            print(f"[PTMP] {message}", flush=True)

    def _send(self, message_type, payload):
        if self.sock is None:
            raise PTMPError("Not connected to Packet Tracer")

        body = f"{message_type}\0".encode("utf-8") + payload.encode("utf-8")
        frame = f"{len(body)}\0".encode("utf-8") + body
        self.sock.sendall(frame)

    def _receive(self):
        if self.sock is None:
            raise PTMPError("Not connected to Packet Tracer")

        while True:
            separator = self.buffer.find(b"\0")

            if separator >= 0:
                try:
                    length = int(self.buffer[:separator])
                except ValueError as error:
                    raise PTMPError("Invalid PTMP frame length") from error

                end = separator + 1 + length

                if len(self.buffer) >= end:
                    frame = self.buffer[separator + 1:end]
                    self.buffer = self.buffer[end:]

                    type_end = frame.find(b"\0")

                    if type_end < 0:
                        raise PTMPError("Invalid PTMP message")

                    message_type = int(frame[:type_end])
                    payload = frame[type_end + 1:]

                    self._log(f"Received message type {message_type}")
                    return message_type, payload

            try:
                chunk = self.sock.recv(4096)
            except socket.timeout as error:
                raise PTMPError("Timed out while waiting for Packet Tracer response") from error

            if not chunk:
                raise PTMPError("Packet Tracer disconnected")

            self.buffer += chunk

    def connect(self):
        if self.connected:
            return

        if not self.password:
            raise PTMPError("Missing NOVA_PT_PASSWORD environment variable")

        self.buffer = b""
        self.call_id = 0

        try:
            self._log(f"Connecting to {self.host}:{self.port}")

            self.sock = socket.create_connection((self.host, self.port), timeout=self.timeout)
            self.sock.settimeout(self.timeout)

            timestamp = time.strftime("%Y%m%d%H%M%S")
            session_id = str(uuid.uuid4())

            negotiation = (
                f"PTMP\0"
                f"1\0"
                f"{session_id}\0"
                f"1\0"
                f"1\0"
                f"1\0"
                f"1\0"
                f"{timestamp}\0"
                f"60\0"
                f":PTVER8.0.0.0000\0\0"
            )

            self._send(0, negotiation)
            message_type, _ = self._receive()

            if message_type != 1:
                raise PTMPError(f"PTMP negotiation failed: {message_type}")

            self._send(2, f"{self.username}\0")
            message_type, _ = self._receive()

            if message_type != 3:
                raise PTMPError(f"Authentication challenge failed: {message_type}")

            self._send(4, f"{self.username}\0{self.password}\0\0\0")
            message_type, payload = self._receive()

            if message_type != 5 or payload.rstrip(b"\0") != b"true":
                raise PTMPError("Packet Tracer authentication rejected")

            self._log("Authentication successful")

        except (OSError, ValueError, PTMPError):
            self.close()
            raise

    def call(self, steps):
        if not self.connected:
            raise PTMPError("Not connected to Packet Tracer")

        if not steps:
            raise ValueError("At least one IPC call step is required")

        self.call_id += 1
        call_id = self.call_id
        fields = [str(call_id)]

        for method, arguments in steps:
            fields.append(method)

            for argument_type, value in arguments:
                fields.append(str(argument_type))
                fields.append(str(value))

            fields.append("0")

        payload = "\0".join(fields) + "\0"
        self._send(100, payload)

        while True:
            message_type, response = self._receive()

            if message_type not in (101, 102):
                continue

            result = response.decode("utf-8", errors="replace").split("\0")

            if not result or result[0] != str(call_id):
                continue

            if message_type == 101:
                error_class = result[1] if len(result) > 1 else "IPC"
                error_message = result[2] if len(result) > 2 else "Unknown IPC error"
                raise PTMPError(f"{error_class}: {error_message}")

            return result[2] if len(result) > 2 else None

    def get_device_count(self):
        return int(self.call([
            ("network", []),
            ("getDeviceCount", [])
        ]))

    def get_device_at_property(self, index, method, arguments=None):
        return self.call([
            ("network", []),
            ("getDeviceAt", [(4, index)]),
            (method, arguments or [])
        ])

    def get_device_name_at(self, index):
        return self.get_device_at_property(index, "getName")

    def get_device_model_at(self, index):
        return self.get_device_at_property(index, "getModel")

    def get_device_property(self, device_name, property_name):
        return self.call([
            ("network", []),
            ("getDevice", [(9, device_name)]),
            ("getCustomVarStr", [(9, property_name)])
        ])

    def get_device_name(self, device_name):
        return self.call([
            ("network", []),
            ("getDevice", [(9, device_name)]),
            ("getName", [])
        ])

    def get_device_model(self, device_name):
        return self.call([
            ("network", []),
            ("getDevice", [(9, device_name)]),
            ("getModel", [])
        ])

    def run_device_code(self, device_name, project_name, code):
        return self.call([
            ("network", []),
            ("getDevice", [(9, device_name)]),
            ("runCodeInProject", [
                (8, project_name),
                (8, code)
            ])
        ])

    def close(self):
        if self.sock is not None:
            try:
                self.sock.close()
            finally:
                self.sock = None
                self.buffer = b""

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()
