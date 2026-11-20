
from agent.smarthome_agent import SmartHomeAgent


def main():
    agent = SmartHomeAgent()

    print("\n========== NOVA SMART HOME ==========")
    print("AI Device Control - Cisco Packet Tracer")
    print("Kilépés: exit\n")

    while True:
        try:
            message = input("Te: ").strip()

            if message.lower() in ("exit", "quit", "kilepes", "kilépés"):
                break

            if not message:
                continue

            result = agent.process(message)

            print(f"\nNOVA: {result.get('message', '')}")

            if not result.get("success"):
                print(f"Részletek: {result.get('details')}")

            print()

        except KeyboardInterrupt:
            print("\nKilépés.")
            break


if __name__ == "__main__":
    main()
