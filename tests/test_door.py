
from iot_devices.door import DoorDevice
from ipc.pmtp_client import PTMPClient


def main():
    with PTMPClient(debug=True) as client:
        door = DoorDevice(client, "IoT0")

        print("\n========== DOOR INFORMATION ==========")
        print("Device:", client.get_device_name("IoT0"))
        print("Model:", client.get_device_model("IoT0"))

        print("\n========== INITIAL STATE ==========")
        print(door.get_state())

        print("\n========== UNLOCK DOOR ==========")
        print(door.set_state("unlock"))

        print("\n========== OPEN DOOR ==========")
        print(door.set_state("open"))

        print("\n========== CLOSE DOOR ==========")
        print(door.set_state("close"))

        print("\n========== LOCK DOOR ==========")
        print(door.set_state("lock"))

        print("\n========== FINAL STATE ==========")
        print(door.get_state())


if __name__ == "__main__":
    main()
