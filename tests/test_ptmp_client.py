from ipc.pmtp_client import PTMPClient, PTMPError

def main():
    try:
        with PTMPClient() as client:
            print("[OK] Connected to Packet Tracer")

            count = client.get_device_count()
            print(f"[OK] Device count: {count}")

            name = client.get_device_name("IoT3")
            print(f"[OK] Device name: {name}")

            model = client.get_device_model("IoT3")
            print(f"[OK] Device model: {model}")

            state = client.get_device_property("IoT3", "state")
            print(f"[OK] Light state: {state}")

            print("\n[SUCCESS] All PTMP tests passed")

    except (PTMPError, OSError, ValueError) as error:
        print(f"[ERROR] {error}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
