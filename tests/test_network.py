
import os
import socket
import time
import uuid

HOST = "127.0.0.1"
PORT = 39001
USERNAME = os.getenv("NOVA_PT_USERNAME", "hu.nova.smarthome")
PASSWORD = os.getenv("NOVA_PT_PASSWORD")

if not PASSWORD:
    raise SystemExit("Hianyzo NOVA_PT_PASSWORD kornyezeti valtozo.")


class PTMPClient:
    def __init__(self):
        self.sock = None
        self.buffer = b""
        self.call_id = 0

    def connect(self):
        self.sock = socket.create_connection((HOST, PORT), timeout=5)
        self.sock.settimeout(5)

        timestamp = time.strftime("%Y%m%d%H%M%S")
        app_id = str(uuid.uuid4())

        negotiation = (
            f"PTMP\0"
            f"1\0"
            f"{app_id}\0"
            f"1\0"
            f"1\0"
            f"1\0"
            f"1\0"
            f"{timestamp}\0"
            f"60\0"
            f":PTVER8.0.0.0000\0\0"
        )

        self.send(0, negotiation)
        message_type, _ = self.receive()

        if message_type != 1:
            raise RuntimeError("PTMP negotiation failed")

        self.send(2, f"{USERNAME}\0")
        message_type, _ = self.receive()

        if message_type != 3:
            raise RuntimeError("Authentication challenge failed")

        self.send(4, f"{USERNAME}\0{PASSWORD}\0\0\0")
        message_type, payload = self.receive()

        if message_type != 5 or payload.rstrip(b"\0") != b"true":
            raise RuntimeError("Authentication rejected")

        print("[OK] NOVA authenticated")

    def send(self, message_type, payload):
        encoded_type = str(message_type).encode() + b"\0"
        encoded_payload = payload.encode("utf-8")
        length = str(len(encoded_type + encoded_payload)).encode() + b"\0"
        self.sock.sendall(length + encoded_type + encoded_payload)

    def receive(self):
        while True:
            first_null = self.buffer.find(b"\0")

            if first_null != -1:
                length = int(self.buffer[:first_null])
                frame_end = first_null + 1 + length

                if len(self.buffer) >= frame_end:
                    frame = self.buffer[first_null + 1:frame_end]
                    self.buffer = self.buffer[frame_end:]

                    type_end = frame.find(b"\0")

                    if type_end == -1:
                        raise ValueError("Invalid PTMP frame")

                    message_type = int(frame[:type_end])
                    payload = frame[type_end + 1:]

                    return message_type, payload

            chunk = self.sock.recv(4096)

            if not chunk:
                raise ConnectionError("Packet Tracer disconnected")

            self.buffer += chunk

    def call(self, name, arguments=None):
        self.call_id += 1
        arguments = arguments or []

        payload = f"{self.call_id}\0{name}\0"

        for argument_type, value in arguments:
            payload += f"{argument_type}\0{value}\0"

        payload += " 0 \0"

        print(f"\n[CALL] {name.replace(chr(0), ' / ')}")
        print(f"[ARGS] {arguments}")

        self.send(100, payload)

        while True:
            message_type, response = self.receive()

            if message_type not in (101, 102):
                print(f"[EVENT] {message_type}: {response!r}")
                continue

            fields = response.decode("utf-8", errors="replace").split("\0")

            if fields[0] != str(self.call_id):
                print(f"[OTHER RESPONSE] {fields}")
                continue

            print(f"[TYPE] {message_type}")
            print(f"[FIELDS] {fields}")

            return message_type, fields

    def close(self):
        if self.sock:
            self.sock.close()


def main():
    client = PTMPClient()

    try:
        client.connect()

        tests = [
            ("Device count", "network\0 0 \0getDeviceCount", []),
            ("Device by name", "network\0 0 \0getDevice", [(9, "IoT3")]),
            ("Device at index 0", "network\0 0 \0getDeviceAt", [(4, 0)]),
        ]

        for label, method, arguments in tests:
            print(f"\n========== {label} ==========")

            try:
                client.call(method, arguments)
            except (OSError, ValueError, RuntimeError) as error:
                print(f"[ERROR] {error}")
                break

    finally:
        client.close()


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, RuntimeError) as error:
        print(f"[FATAL] {error}")
