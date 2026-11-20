#!/usr/bin/env python3
"""Cybersec Toolkit — Security Operations Command Center."""

import asyncio
import subprocess
import sys
from pathlib import Path

from rich import box
from rich.align import Align
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table
from rich.text import Text

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from mcp_server.tools_db import ToolsDatabase
from mcp_server.security import execute_tool

DB = ToolsDatabase(ROOT)
CONSOLE = Console()
PAGE_SIZE = 12
NON_EXECUTABLE = {"git", "docker", "snap"}
LOOP = asyncio.new_event_loop()
STATUS_CACHE = {}

# Visual identity
CYAN = "#22D3EE"
BLUE = "#38BDF8"
VIOLET = "#A78BFA"
GREEN = "#4ADE80"
AMBER = "#FBBF24"
RED = "#FB7185"
MUTED = "#94A3B8"

MODULE_LABELS = {
    "blockchain": "Blockchain",
    "blueteam": "Blue Team",
    "cloud": "Cloud Security",
    "containers": "Container Security",
    "cracking": "Password Cracking",
    "crypto": "Cryptography",
    "enterprise": "Enterprise Security",
    "forensics": "Digital Forensics",
    "llm": "LLM Security",
    "misc": "Miscellaneous",
    "mobile": "Mobile Security",
    "networking": "Networking",
    "pwn": "PWN & Exploitation",
    "recon": "Reconnaissance",
    "reversing": "Reverse Engineering",
    "stego": "Steganography",
    "web": "Web Security",
    "wireless": "Wireless Security",
}

MODULE_COLORS = {
    "blockchain": "#A78BFA",
    "blueteam": "#4ADE80",
    "cloud": "#38BDF8",
    "containers": "#22D3EE",
    "cracking": "#FB7185",
    "crypto": "#A78BFA",
    "enterprise": "#38BDF8",
    "forensics": "#FBBF24",
    "llm": "#C084FC",
    "misc": "#94A3B8",
    "mobile": "#F472B6",
    "networking": "#22D3EE",
    "pwn": "#FB7185",
    "recon": "#4ADE80",
    "reversing": "#A78BFA",
    "stego": "#FBBF24",
    "web": "#38BDF8",
    "wireless": "#22D3EE",
}


def version():
    try:
        return (ROOT / "VERSION").read_text().strip()
    except OSError:
        return "1.5.0"


def refresh_inventory():
    STATUS_CACHE.clear()
    with CONSOLE.status(
        "[bold cyan]Scanning tool inventory...[/]",
        spinner="dots",
    ):
        DB.reload_versions(ttl=0)
        for tool in DB.list_tools():
            STATUS_CACHE[tool["name"]] = DB.check_installed(
                tool["name"]
            )
    return len(STATUS_CACHE)


def get_status(tool):
    name = tool["name"]
    if name not in STATUS_CACHE:
        STATUS_CACHE[name] = DB.check_installed(name)
    return STATUS_CACHE[name]


def pause():
    CONSOLE.input("\n[dim]Press Enter to continue...[/]")


def frame(section="OVERVIEW", subtitle="SECURITY OPERATIONS CENTER"):
    CONSOLE.clear()

    heading = Text()
    heading.append("CYBER", style=f"bold {CYAN}")
    heading.append("SEC", style="bold white")
    heading.append("  /  TOOLKIT", style=f"bold {BLUE}")

    sub = Text(subtitle, style=f"bold {MUTED}")

    content = Table.grid(expand=True)
    content.add_column(ratio=1)
    content.add_row(heading)
    content.add_row(sub)

    CONSOLE.print(Panel(
        content,
        border_style=CYAN,
        box=box.DOUBLE,
        padding=(0, 1),
    ))

    CONSOLE.print(
        Text.assemble(
            ("  / ", MUTED),
            (section.upper(), f"bold {VIOLET}"),
            ("   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━", f"{CYAN}"),
        )
    )


def inventory_stats():
    total = DB.total_tools
    installed = sum(
        1 for status in STATUS_CACHE.values()
        if status["installed"]
    )
    return total, installed, len(DB.modules)


def stat_card(label, value, accent, detail):
    content = Text()
    content.append(str(value), style=f"bold {accent}")
    content.append(f"\n{label.upper()}", style="bold white")
    content.append(f"\n{detail}", style=f"dim {MUTED}")

    return Panel(
        Align.center(content),
        border_style=accent,
        box=box.ROUNDED,
        padding=(0, 1),
    )


def dashboard():
    frame("OVERVIEW")

    total, installed, modules = inventory_stats()
    missing = total - installed
    percentage = (installed / total * 100) if total else 0

    stats = Table.grid(expand=True, padding=(0, 1))
    stats.add_column(ratio=1)
    stats.add_column(ratio=1)

    stats.add_row(
        stat_card("Registered tools", total, CYAN, "TOOL DATABASE"),
        stat_card("Installed", installed, GREEN, "READY TO USE"),
    )
    stats.add_row(
        stat_card("Categories", modules, VIOLET, "MODULES"),
        stat_card("Not installed", missing, AMBER, "AVAILABLE TO INSTALL"),
    )

    CONSOLE.print(stats)

    progress = int(percentage / 5)
    bar = Text()
    bar.append("  INVENTORY READINESS  ", style=f"bold {MUTED}")
    bar.append("█" * progress, style=GREEN)
    bar.append("░" * (20 - progress), style="bright_black")
    bar.append(f"  {percentage:.1f}%", style=f"bold {CYAN}")
    CONSOLE.print(bar)

    CONSOLE.print("\n[bold white]  COMMAND CENTER[/bold white]")

    menu = Table(
        box=box.ROUNDED,
        expand=True,
        show_header=False,
        border_style="bright_black",
        padding=(0, 1),
    )
    menu.add_column(width=5, justify="center")
    menu.add_column(ratio=1)
    menu.add_column(style=f"dim {MUTED}")

    menu.add_row(
        Text("01", style=f"bold {CYAN}"),
        Text("Search tools", style="bold white"),
        "FIND",
    )
    menu.add_row(
        Text("02", style=f"bold {VIOLET}"),
        Text("Category explorer", style="bold white"),
        "18 MODULES",
    )
    menu.add_row(
        Text("03", style=f"bold {BLUE}"),
        Text("All tools", style="bold white"),
        "EXPLORE",
    )
    menu.add_row(
        Text("04", style=f"bold {GREEN}"),
        Text("Installed tools", style="bold white"),
        "READY",
    )
    menu.add_row(
        Text("05", style=f"bold {AMBER}"),
        Text("Refresh inventory", style="bold white"),
        "RESCAN",
    )
    menu.add_row(
        Text(" Q", style=f"bold {RED}"),
        Text("Exit command center", style="bold white"),
        "QUIT",
    )

    CONSOLE.print(menu)

    footer = Text()
    footer.append("  ● ", style=GREEN)
    footer.append("DATABASE LOADED", style=f"bold {GREEN}")
    footer.append("    ◆ ", style=CYAN)
    footer.append("POLICY CONTROLLED", style=f"bold {CYAN}")
    CONSOLE.print(footer)
    CONSOLE.print(
        f"  [dim]CYBERSEC TOOLKIT v{version()}  ·  "
        f"{CONSOLE.width} columns[/dim]"
    )


def show_tool(tool):
    name = tool["name"]
    method = tool["method"]
    status = get_status(tool)
    module = tool.get("module", "Unknown")

    accent = MODULE_COLORS.get(module, CYAN)
    frame("TOOL INTELLIGENCE", "TOOL PROFILE / DETAILS")

    status_text = (
        Text("● INSTALLED", style=f"bold {GREEN}")
        if status["installed"]
        else Text("● NOT INSTALLED", style=f"bold {AMBER}")
    )

    details = Table.grid(expand=True, padding=(0, 1))
    details.add_column(width=13, style=f"dim {MUTED}")
    details.add_column(ratio=1)

    details.add_row("TOOL", Text(name, style=f"bold {CYAN}"))
    details.add_row("CATEGORY", Text(
        MODULE_LABELS.get(module, module), style=f"bold {accent}"
    ))
    details.add_row("METHOD", Text(method, style="bold white"))
    details.add_row("STATUS", status_text)
    details.add_row("INSTALL INFO", Text(
        status.get("details", ""), style=MUTED
    ))

    description = str(tool.get("description", "") or "")
    if description:
        details.add_row("DESCRIPTION", Text(description, style="white"))

    url = str(tool.get("url", "") or "")
    if url:
        details.add_row("REFERENCE", Text(url, style=BLUE))

    CONSOLE.print(Panel(
        details,
        title=f"[bold {accent}] {name} [/]",
        subtitle="[dim]TOOL PROFILE[/]",
        border_style=accent,
        box=box.DOUBLE,
        padding=(1, 1),
    ))

    if not status["installed"]:
        choice = Prompt.ask(
            f"[{CYAN}]I[/{CYAN}] Install    "
            f"[{MUTED}]B[/{MUTED}] Back",
            default="b",
        ).lower()

        if choice == "i":
            CONSOLE.print(
                f"\n[bold {AMBER}]INSTALLING {name.upper()}[/]\n"
            )
            subprocess.run(
                ["bash", str(ROOT / "install.sh"), "--tool", name],
                cwd=ROOT,
            )
            refresh_inventory()
            pause()
        return

    if method in NON_EXECUTABLE:
        CONSOLE.print(
            f"\n[bold {AMBER}]MANAGED TOOL[/]"
            "\n[dim]This tool is not directly executable here.[/]"
        )
        pause()
        return

    choice = Prompt.ask(
        f"[{GREEN}]R[/{GREEN}] Run tool    "
        f"[{MUTED}]B[/{MUTED}] Back",
        default="b",
    ).lower()

    if choice != "r":
        return

    args = Prompt.ask(f"[{CYAN}]Arguments[/]", default="")
    timeout_text = Prompt.ask(
        f"[{CYAN}]Timeout in seconds[/]", default="120"
    )

    try:
        timeout = max(1, min(int(timeout_text), 300))
    except ValueError:
        CONSOLE.print(f"[bold {RED}]Invalid timeout.[/]")
        pause()
        return

    CONSOLE.print(
        f"\n[bold {CYAN}]EXECUTION / SECURITY POLICY[/]\n"
    )

    try:
        with CONSOLE.status(
            "[bold cyan]Validating and executing tool...[/]",
            spinner="dots",
        ):
            result = LOOP.run_until_complete(
                execute_tool(name, args, DB, timeout=timeout)
            )

        exit_code = result.get("exit_code", -1)
        success = exit_code == 0

        CONSOLE.print(Panel(
            Text(
                f"EXIT CODE: {exit_code}\n"
                f"STATUS: {'SUCCESS' if success else 'FAILED / BLOCKED'}",
                style=f"bold {GREEN if success else RED}",
            ),
            title="[bold]EXECUTION RESULT[/]",
            border_style=GREEN if success else RED,
            box=box.ROUNDED,
        ))

        if result.get("stdout"):
            CONSOLE.print(Panel(
                Text(result["stdout"]),
                title=f"[bold {GREEN}]OUTPUT[/]",
                border_style=GREEN,
                box=box.ROUNDED,
            ))

        if result.get("stderr"):
            CONSOLE.print(Panel(
                Text(result["stderr"]),
                title=f"[bold {RED}]ERROR / POLICY[/]",
                border_style=RED,
                box=box.ROUNDED,
            ))

    except Exception as exc:
        CONSOLE.print(
            f"\n[bold {RED}]EXECUTION ERROR[/]\n{exc}"
        )

    pause()


def browse_tools(tools, heading):
    tools = sorted(tools, key=lambda t: t["name"].lower())
    page = 0

    while True:
        total = len(tools)
        pages = max(1, (total + PAGE_SIZE - 1) // PAGE_SIZE)
        page = min(page, pages - 1)
        current = tools[page * PAGE_SIZE:(page + 1) * PAGE_SIZE]

        frame(heading, "TOOL INVENTORY / SELECT TO INSPECT")

        CONSOLE.print(
            f"  [bold {CYAN}]{total} TOOLS[/]  "
            f"[dim]· Page {page + 1}/{pages}[/]\n"
        )

        table = Table(
            box=box.ROUNDED,
            expand=True,
            header_style=f"bold {CYAN}",
            border_style="bright_black",
            padding=(0, 1),
        )
        table.add_column("#", width=3, justify="right")
        table.add_column("TOOL", ratio=1, overflow="ellipsis")
        table.add_column("STATUS", width=10)

        for index, tool in enumerate(current, 1):
            installed = get_status(tool)["installed"]
            table.add_row(
                Text(f"{index:02}", style=f"dim {MUTED}"),
                Text(tool["name"], style="bold white"),
                Text(
                    "● READY" if installed else "○ MISSING",
                    style=f"bold {GREEN}" if installed else MUTED,
                ),
            )

        CONSOLE.print(table)
        CONSOLE.print(
            f"\n  [{CYAN}]N[/{CYAN}] Next   "
            f"[{CYAN}]P[/{CYAN}] Previous   "
            f"[{MUTED}]B[/{MUTED}] Back   "
            f"[{RED}]Q[/{RED}] Quit"
        )

        choice = Prompt.ask(
            f"[bold {CYAN}]SELECT[/]"
        ).strip().lower()

        if choice in ("b", "q"):
            return choice == "q"

        if choice == "n":
            if page + 1 < pages:
                page += 1
            continue

        if choice == "p":
            page = max(0, page - 1)
            continue

        try:
            number = int(choice)
            if 1 <= number <= len(current):
                if show_tool(current[number - 1]):
                    return True
            else:
                CONSOLE.print(f"[bold {RED}]Invalid selection.[/]")
                pause()
        except ValueError:
            CONSOLE.print(f"[bold {RED}]Invalid selection.[/]")
            pause()


def browse_modules():
    modules = []

    for module in DB.modules:
        tools = DB.list_tools(module=module)
        installed = sum(
            1 for tool in tools if get_status(tool)["installed"]
        )
        modules.append((module, tools, installed))

    modules.sort(
        key=lambda item: (
            -len(item[1]),
            MODULE_LABELS.get(item[0], item[0]).lower(),
        )
    )

    while True:
        frame("CATEGORY EXPLORER", "DISCOVER / 18 SECURITY DOMAINS")

        CONSOLE.print(
            f"  [bold {CYAN}]{DB.total_tools}[/] TOOLS   "
            f"[bold {VIOLET}]{len(modules)}[/] CATEGORIES\n"
        )

        grid = Table.grid(expand=True, padding=(0, 1))
        grid.add_column(ratio=1)
        grid.add_column(ratio=1)

        cards = []

        for index, (module, tools, installed) in enumerate(modules, 1):
            accent = MODULE_COLORS.get(module, CYAN)
            label = MODULE_LABELS.get(
                module, module.replace("_", " ").title()
            )

            card = Text()
            card.append(f"{index:02}  ", style=f"bold {accent}")
            card.append(label, style="bold white")
            card.append(
                f"\n    {len(tools)} tools",
                style=f"dim {MUTED}",
            )
            card.append("  ·  ", style="dim")
            card.append(f"{installed} ready", style=f"bold {GREEN}")

            cards.append(card)

        for index in range(0, len(cards), 2):
            left = cards[index]
            right = cards[index + 1] if index + 1 < len(cards) else Text()
            grid.add_row(left, right)

        CONSOLE.print(Panel(
            grid,
            title=f"[bold {CYAN}] MODULE DIRECTORY [/]",
            border_style=CYAN,
            box=box.ROUNDED,
            padding=(1, 1),
        ))

        CONSOLE.print(
            f"  [{CYAN}]NUMBER[/{CYAN}] Open category    "
            f"[{MUTED}]B[/{MUTED}] Back"
        )

        choice = Prompt.ask(
            f"[bold {CYAN}]CATEGORY[/]"
        ).strip().lower()

        if choice == "b":
            return

        try:
            index = int(choice) - 1
            if 0 <= index < len(modules):
                module, tools, _ = modules[index]
                label = MODULE_LABELS.get(module, module.upper())

                if browse_tools(tools, label.upper()):
                    return
            else:
                CONSOLE.print(f"[bold {RED}]Invalid category.[/]")
                pause()
        except ValueError:
            CONSOLE.print(
                f"[bold {RED}]Enter a category number or B.[/]"
            )
            pause()


def search_tools():
    while True:
        frame("TOOL SEARCH", "DISCOVER / FIND A SECURITY TOOL")

        CONSOLE.print(
            f"  [dim]Search across {DB.total_tools} registered tools[/]\n"
        )

        query = Prompt.ask(
            f"[bold {CYAN}]SEARCH[/] (B to return)"
        ).strip().lower()

        if query in ("b", "back", ""):
            return

        matches = [
            tool for tool in DB.list_tools()
            if query in tool["name"].lower()
            or query in tool["module"].lower()
            or query in tool["method"].lower()
            or query in str(tool.get("description", "")).lower()
        ]

        if matches:
            CONSOLE.print(
                f"\n[bold {GREEN}]{len(matches)} MATCHES FOUND[/]\n"
            )
            if browse_tools(matches, f"SEARCH / {query.upper()}"):
                return
        else:
            CONSOLE.print(
                f"\n[bold {AMBER}]NO MATCHES FOUND[/]"
                "\n[dim]Try another tool name or category.[/]"
            )
            pause()


def main():
    refresh_inventory()

    while True:
        dashboard()

        choice = Prompt.ask(
            f"[bold {CYAN}]COMMAND[/]",
            choices=["1", "2", "3", "4", "5", "q"],
            default="1",
        ).lower()

        if choice == "q":
            break
        elif choice == "1":
            search_tools()
        elif choice in ("2", "3"):
            browse_modules()
        elif choice == "4":
            installed = [
                tool for tool in DB.list_tools()
                if get_status(tool)["installed"]
            ]
            if browse_tools(installed, "INSTALLED TOOLS"):
                break
        elif choice == "5":
            frame("INVENTORY REFRESH", "DATABASE / RESCAN")
            refresh_inventory()
            CONSOLE.print(
                f"\n[bold {GREEN}]INVENTORY UPDATED[/]"
                f"\n[dim]{len(STATUS_CACHE)} tools checked.[/]"
            )
            pause()

    CONSOLE.print(
        f"\n[bold {CYAN}]CYBERSEC TOOLKIT CLOSED[/]"
    )


if __name__ == "__main__":
    try:
        main()
    except (KeyboardInterrupt, EOFError):
        CONSOLE.print(f"\n[dim]Session closed.[/]")
    finally:
        LOOP.close()
