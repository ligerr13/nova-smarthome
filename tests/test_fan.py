
from iot_devices.fan import FanDevice
from ipc.pmtp_client import PTMPClient


def main():
    with PTMPClient(debug=True) as client:
        fan = FanDevice(client, "IoT1")

        print("Device:", client.get_device_name("IoT1"))
        print("Model:", client.get_device_model("IoT1"))
        print("Initial state:", fan.get_state())

        for state in ("low", "high", "off"):
            print(f"\nSetting fan to: {state}")
            print(fan.set_state(state))

        print("\nFinal state:", fan.get_state())


if __name__ == "__main__":
    main()
