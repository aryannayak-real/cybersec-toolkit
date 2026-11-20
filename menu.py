#!/usr/bin/env python3
"""Interactive menu for every tool in Cybersec Toolkit."""

import asyncio
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from mcp_server.tools_db import ToolsDatabase
from mcp_server.security import execute_tool

DB = ToolsDatabase(ROOT)
PAGE_SIZE = 20
NON_EXECUTABLE = {"git", "docker", "snap"}
LOOP = asyncio.new_event_loop()


def pause():
    input("\nPress Enter to continue...")


def status(tool):
    result = DB.check_installed(tool["name"])
    return "INSTALLED" if result["installed"] else "NOT INSTALLED"


def show_tool(tool):
    name = tool["name"]
    method = tool["method"]
    result = DB.check_installed(name)

    print("\n" + "=" * 48)
    print("TOOL:", name)
    print("MODULE:", tool["module"])
    print("METHOD:", method)
    print("STATUS:", "INSTALLED" if result["installed"] else "NOT INSTALLED")
    print("DETAILS:", result["details"])
    print("INFO:", tool.get("url", "Not available"))
    print("=" * 48)

    if not result["installed"]:
        choice = input("[I] Install  [B] Back: ").strip().lower()
        if choice == "i":
            print("\nStarting installer...\n")
            subprocess.run(
                ["bash", str(ROOT / "install.sh"), "--tool", name],
                cwd=ROOT
            )
            DB.reload_versions(ttl=0)
            pause()
        return

    if method in NON_EXECUTABLE:
        print("This is a managed tool, not a directly executable CLI.")
        pause()
        return

    choice = input("[R] Run  [B] Back: ").strip().lower()
    if choice != "r":
        return

    args = input("Arguments (leave blank for none): ").strip()
    timeout_text = input("Timeout in seconds [120]: ").strip()

    try:
        timeout = int(timeout_text) if timeout_text else 120
        timeout = max(1, min(timeout, 300))
    except ValueError:
        print("Invalid timeout.")
        pause()
        return

    print("\nExecuting through the toolkit's security checks...\n")

    try:
        result = LOOP.run_until_complete(
            execute_tool(name, args, DB, timeout=timeout)
        )
        print("Exit code:", result.get("exit_code", -1))
        if result.get("stdout"):
            print("\n--- OUTPUT ---\n", result["stdout"])
        if result.get("stderr"):
            print("\n--- ERRORS / POLICY ---\n", result["stderr"])
    except Exception as exc:
        print("Execution error:", exc)

    pause()


def browse_tools(tools, heading):
    page = 0
    tools = sorted(tools, key=lambda item: item["name"].lower())

    while True:
        total = len(tools)
        pages = max(1, (total + PAGE_SIZE - 1) // PAGE_SIZE)
        page = min(page, pages - 1)
        start = page * PAGE_SIZE
        current = tools[start:start + PAGE_SIZE]

        print("\n" + "=" * 55)
        print(heading)
        print(f"Tools: {total} | Page {page + 1}/{pages}")
        print("=" * 55)

        for index, tool in enumerate(current, 1):
            installed = status(tool)
            print(f"{index:2}. {tool['name']:<27} [{installed}]")

        print("\n[N] Next  [P] Previous  [B] Back")
        choice = input("Select a number or command: ").strip().lower()

        if choice == "b":
            return
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
                show_tool(current[number - 1])
        except ValueError:
            print("Invalid selection.")
            pause()


def browse_modules():
    modules = DB.modules

    while True:
        print("\n========== MODULES ==========")
        for i, module in enumerate(modules, 1):
            count = len(DB.list_tools(module=module))
            print(f"{i:2}. {module:<22} ({count} tools)")
        print("B. Back")

        choice = input("\nChoose module: ").strip().lower()
        if choice == "b":
            return

        try:
            index = int(choice) - 1
            module = modules[index]
            browse_tools(DB.list_tools(module=module), module.upper())
        except (ValueError, IndexError):
            print("Invalid selection.")


def search_tools():
    query = input("\nSearch all tools: ").strip().lower()
    if not query:
        return

    matches = [
        tool for tool in DB.list_tools()
        if query in tool["name"].lower()
        or query in tool["module"].lower()
        or query in tool["method"].lower()
    ]

    if matches:
        browse_tools(matches, f"SEARCH RESULTS: {query}")
    else:
        print("No matching tools found.")
        pause()


def main():
    print("\nCybersec Toolkit Interactive Menu")
    print(f"Loaded {DB.total_tools} registered tools.")

    while True:
        print("\n" + "=" * 42)
        print("          CYBERSEC TOOLKIT")
        print("=" * 42)
        print("1. Browse all modules")
        print("2. Search all tools")
        print("3. Show all registered tools")
        print("4. Exit")
        print("=" * 42)

        choice = input("Select an option: ").strip()

        if choice == "1":
            browse_modules()
        elif choice == "2":
            search_tools()
        elif choice == "3":
            browse_tools(DB.list_tools(), "ALL REGISTERED TOOLS")
        elif choice == "4":
            break
        else:
            print("Invalid selection.")

    LOOP.close()
    print("Cybersec Toolkit closed.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nExiting...")
        LOOP.close()
