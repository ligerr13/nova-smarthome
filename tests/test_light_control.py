
import os
import socket
import time
import uuid

HOST = "127.0.0.1"
PORT = 39001

USERNAME = os.getenv("NOVA_PT_USERNAME", "hu.nova.smarthome")
PASSWORD = os.getenv("NOVA_PT_PASSWORD")

if not PASSWORD:
    raise SystemExit("Missing NOVA_PT_PASSWORD environment variable")


class PTMPClient:
    def __init__(self):
        self.sock = None
        self.buffer = b""
        self.call_id = 0

    def send(self, message_type, payload):
        body = f"{message_type}\0".encode("utf-8") + payload.encode("utf-8")
        frame = f"{len(body)}\0".encode("utf-8") + body
        self.sock.sendall(frame)

    def receive(self):
        while True:
            separator = self.buffer.find(b"\0")

            if separator >= 0:
                length = int(self.buffer[:separator])
                end = separator + 1 + length

                if len(self.buffer) >= end:
                    frame = self.buffer[separator + 1:end]
                    self.buffer = self.buffer[end:]

                    type_end = frame.find(b"\0")

                    if type_end < 0:
                        raise ValueError("Invalid PTMP frame")

                    message_type = int(frame[:type_end])
                    payload = frame[type_end + 1:]

                    return message_type, payload

            chunk = self.sock.recv(4096)

            if not chunk:
                raise ConnectionError("Packet Tracer disconnected")

            self.buffer += chunk

    def connect(self):
        self.sock = socket.create_connection((HOST, PORT), timeout=5)
        self.sock.settimeout(5)

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

        self.send(0, negotiation)
        message_type, _ = self.receive()

        if message_type != 1:
            raise RuntimeError("Negotiation failed")

        self.send(2, f"{USERNAME}\0")
        message_type, _ = self.receive()

        if message_type != 3:
            raise RuntimeError("Authentication challenge failed")

        self.send(4, f"{USERNAME}\0{PASSWORD}\0\0\0")
        message_type, payload = self.receive()

        if message_type != 5 or payload.rstrip(b"\0") != b"true":
            raise RuntimeError("Authentication rejected")

        print("[OK] NOVA authenticated successfully")

    def call(self, steps):
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

        description = " -> ".join(
            f"{method}({', '.join(str(v) for _, v in args)})"
            for method, args in steps
        )

        print(f"\n[CALL] {description}")

        self.send(100, payload)

        while True:
            message_type, response = self.receive()

            if message_type not in (101, 102):
                print(f"[EVENT] {message_type}: {response!r}")
                continue

            result = response.decode("utf-8", errors="replace").split("\0")

            if result[0] != str(call_id):
                print(f"[OTHER RESPONSE] {result}")
                continue

            print(f"[TYPE] {message_type}")
            print(f"[FIELDS] {result}")

            return message_type, result

    def close(self):
        if self.sock:
            self.sock.close()


def get_light_state(client):
    message_type, fields = client.call([
        ("network", []),
        ("getDevice", [(9, "IoT3")]),
        ("getCustomVarStr", [(9, "state")])
    ])

    if message_type != 102 or len(fields) < 3:
        raise RuntimeError("Failed to read light state")

    return fields[2]


def main():
    client = PTMPClient()

    try:
        client.connect()

        print("\n========== INITIAL STATE ==========")
        initial_state = get_light_state(client)
        print(f"[STATE] IoT3 = {initial_state}")

        print("\n========== TURN LIGHT ON ==========")

        message_type, fields = client.call([
            ("network", []),
            ("getDevice", [(9, "IoT3")]),
            ("runCodeInProject", [
                (8, "Light (JavaScript)"),
                (8, "setState(2);")
            ])
        ])

        if message_type != 102:
            raise RuntimeError("Light control IPC call failed")

        print("\n========== VERIFY STATE ==========")
        time.sleep(1)

        new_state = get_light_state(client)
        print(f"[STATE] IoT3 = {new_state}")

        if new_state == "2":
            print("\n[SUCCESS] IoT3 light is ON!")
        else:
            print("\n[WARNING] Light state did not change")

    finally:
        client.close()


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, RuntimeError) as error:
        print(f"[ERROR] {error}")
