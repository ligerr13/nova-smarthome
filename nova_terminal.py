
import os
import time
from datetime import datetime

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt
from rich.text import Text
from rich.align import Align
from rich import box

from agent.smarthome_agent import SmartHomeAgent


console = Console()
agent = SmartHomeAgent()


def header():
    console.clear()

    logo = Text()
    logo.append("N O V A\n", style="bold bright_cyan")
    logo.append(
        "NEURAL OPERATED VIRTUAL ASSISTANT\n",
        style="bold white"
    )
    logo.append(
        "SMART HOME AI CONTROL SYSTEM",
        style="dim cyan"
    )

    console.print(
        Panel(
            Align.center(logo),
            border_style="bright_cyan",
            padding=(1, 2),
            title="[bold cyan]SYSTEM ONLINE[/]",
            subtitle="[dim]Qwen3.5:4B | Ollama | Cisco Packet Tracer[/]",
        )
    )


def system_info():
    table = Table(
        box=box.ROUNDED,
        border_style="bright_blue",
        expand=True,
        show_header=False,
    )

    table.add_column("Property", style="dim")
    table.add_column("Value", style="bold white")

    table.add_row("AI MODEL", os.getenv("NOVA_MODEL", "qwen3.5:4b"))
    table.add_row("AI ENGINE", "Ollama")
    table.add_row("SIMULATION", "Cisco Packet Tracer")
    table.add_row("COMMUNICATION", "PTMP / IPC")
    table.add_row("STATUS", "[green]READY[/]")

    console.print(table)


def show_devices():
    console.print("\n[bold cyan]DEVICE DISCOVERY[/]")

    try:
        result = agent.tools.list_devices()

        if not result.get("success"):
            console.print(
                Panel(
                    str(result.get("error", "Unknown error")),
                    title="[red]CONNECTION ERROR[/]",
                    border_style="red",
                )
            )
            return

        devices = result.get("devices", [])

        table = Table(
            box=box.SIMPLE_HEAVY,
            expand=True,
            header_style="bold bright_cyan",
        )

        table.add_column("DEVICE ID")
        table.add_column("MODEL")
        table.add_column("STATUS")
        table.add_column("CONTROL")

        for device in devices:
            controllable = device.get("controllable", False)

            table.add_row(
                str(device.get("id", "-")),
                str(device.get("model", "-")),
                str(device.get("state", "-")),
                "[green]ENABLED[/]" if controllable else "[dim]READ ONLY[/]",
            )

        console.print(table)

    except Exception as error:
        console.print(f"[red]Device discovery failed: {error}[/]")


def show_decision(result):
    actions = result.get("actions", [])

    if not actions:
        return

    table = Table(
        box=box.MINIMAL,
        show_header=True,
        header_style="bold magenta",
        expand=True,
    )

    table.add_column("DEVICE")
    table.add_column("ACTION")
    table.add_column("RESULT")

    results = result.get("results", [])

    for index, action in enumerate(actions):
        execution = results[index] if index < len(results) else {}
        success = execution.get("success", False)

        table.add_row(
            str(action.get("device_id", "-")),
            str(action.get("state", "-")),
            "[green]SUCCESS[/]" if success else "[red]FAILED[/]",
        )

    console.print(
        Panel(
            table,
            title="[bold magenta]AI EXECUTION PLAN[/]",
            border_style="magenta",
        )
    )


def show_response(result, elapsed):
    success = result.get("success", False)
    message = result.get("message", "Nincs válasz.")

    if success:
        console.print(
            Panel(
                f"[bold green]{message}[/]\n"
                f"[dim]Processing time: {elapsed:.2f}s[/]",
                title="[bold green]NOVA RESPONSE[/]",
                border_style="green",
            )
        )
    else:
        details = result.get("details")
        content = f"[bold red]{message}[/]"

        if details:
            content += f"\n[dim]{details}[/]"

        console.print(
            Panel(
                content,
                title="[bold red]NOVA ERROR[/]",
                border_style="red",
            )
        )


def main():
    header()
    system_info()
    show_devices()

    console.print(
        "\n[dim]Commands: devices | clear | exit[/]\n"
    )

    while True:
        try:
            message = Prompt.ask(
                "[bold bright_cyan]YOU[/]"
            ).strip()

            if not message:
                continue

            if message.lower() in ("exit", "quit", "kilepes"):
                console.print(
                    "\n[cyan]NOVA shutting down. Goodbye![/]"
                )
                break

            if message.lower() == "clear":
                header()
                system_info()
                continue

            if message.lower() == "devices":
                show_devices()
                continue

            start = time.perf_counter()

            with console.status(
                "[bold cyan]NOVA is processing your request...",
                spinner="dots",
            ):
                result = agent.process(message)

            elapsed = time.perf_counter() - start

            console.print(
                f"\n[dim]{datetime.now():%H:%M:%S} | "
                f"AI processing completed[/]"
            )

            show_decision(result)
            show_response(result, elapsed)

        except KeyboardInterrupt:
            console.print("\n[yellow]Interrupted.[/]")
            break

        except Exception as error:
            console.print(
                Panel(
                    str(error),
                    title="[red]SYSTEM ERROR[/]",
                    border_style="red",
                )
            )


if __name__ == "__main__":
    main()
