#!/usr/bin/env python3
"""
Mouse Mover Macro
------------------
Moves the mouse cursor down by an adjustable amount, with named presets
you can save and reload later.

Setup (one time):
    pip install pyautogui

Usage:
    python mouse_mover.py                 # interactive menu
    python mouse_mover.py move 250        # move down 250 px immediately
    python mouse_mover.py save work 250   # save a preset called "work" = 250 px
    python mouse_mover.py load work       # move down using the "work" preset
    python mouse_mover.py list            # list saved presets
    python mouse_mover.py delete work     # delete a preset

Presets are stored in mouse_presets.json next to this script.
"""

import json
import sys
import time
from pathlib import Path

try:
    import pyautogui
except ImportError:
    print("Missing dependency. Install it with:\n    pip install pyautogui")
    sys.exit(1)

PRESETS_FILE = Path(__file__).with_name("mouse_presets.json")
DEFAULT_DELAY = 0.3  # short pause before moving, so you can release keys/focus a window


def load_presets():
    if PRESETS_FILE.exists():
        try:
            return json.loads(PRESETS_FILE.read_text())
        except json.JSONDecodeError:
            print("Warning: presets file was corrupted, starting fresh.")
            return {}
    return {}


def save_presets(presets):
    PRESETS_FILE.write_text(json.dumps(presets, indent=2))


def move_down(amount, delay=DEFAULT_DELAY, duration=0.2):
    """Move the mouse cursor down by `amount` pixels from its current position."""
    x, y = pyautogui.position()
    if delay:
        time.sleep(delay)
    pyautogui.moveTo(x, y + amount, duration=duration)
    print(f"Moved mouse down {amount}px (from y={y} to y={y + amount}).")


def cmd_move(args):
    if not args:
        print("Usage: move <pixels>")
        return
    move_down(int(args[0]))


def cmd_save(args):
    if len(args) < 2:
        print("Usage: save <name> <pixels>")
        return
    name, amount = args[0], int(args[1])
    presets = load_presets()
    presets[name] = amount
    save_presets(presets)
    print(f"Saved preset '{name}' = {amount}px.")


def cmd_load(args):
    if not args:
        print("Usage: load <name>")
        return
    name = args[0]
    presets = load_presets()
    if name not in presets:
        print(f"No preset named '{name}'. Use 'list' to see saved presets.")
        return
    move_down(presets[name])


def cmd_list(args):
    presets = load_presets()
    if not presets:
        print("No presets saved yet.")
        return
    print("Saved presets:")
    for name, amount in presets.items():
        print(f"  {name}: {amount}px")


def cmd_delete(args):
    if not args:
        print("Usage: delete <name>")
        return
    name = args[0]
    presets = load_presets()
    if name in presets:
        del presets[name]
        save_presets(presets)
        print(f"Deleted preset '{name}'.")
    else:
        print(f"No preset named '{name}'.")


def interactive_menu():
    while True:
        presets = load_presets()
        print("\n=== Mouse Mover ===")
        print("1. Move down by custom amount")
        print("2. Load a saved preset")
        print("3. Save a new preset")
        print("4. Delete a preset")
        print("5. List presets")
        print("6. Quit")
        choice = input("Choose an option (1-6): ").strip()

        if choice == "1":
            try:
                amount = int(input("Move down by how many pixels? ").strip())
                move_down(amount)
            except ValueError:
                print("Please enter a whole number.")

        elif choice == "2":
            if not presets:
                print("No presets saved yet.")
                continue
            print("Presets:", ", ".join(f"{n} ({a}px)" for n, a in presets.items()))
            name = input("Which preset? ").strip()
            if name in presets:
                move_down(presets[name])
            else:
                print("Preset not found.")

        elif choice == "3":
            name = input("Name for this preset: ").strip()
            try:
                amount = int(input("Amount in pixels: ").strip())
                presets[name] = amount
                save_presets(presets)
                print(f"Saved '{name}' = {amount}px.")
            except ValueError:
                print("Please enter a whole number.")

        elif choice == "4":
            if not presets:
                print("No presets saved yet.")
                continue
            name = input("Preset to delete: ").strip()
            if name in presets:
                del presets[name]
                save_presets(presets)
                print(f"Deleted '{name}'.")
            else:
                print("Preset not found.")

        elif choice == "5":
            if not presets:
                print("No presets saved yet.")
            else:
                for n, a in presets.items():
                    print(f"  {n}: {a}px")

        elif choice == "6":
            print("Bye!")
            break

        else:
            print("Invalid choice, try again.")


def main():
    args = sys.argv[1:]
    if not args:
        interactive_menu()
        return

    command, rest = args[0].lower(), args[1:]
    commands = {
        "move": cmd_move,
        "save": cmd_save,
        "load": cmd_load,
        "list": cmd_list,
        "delete": cmd_delete,
    }
    if command in commands:
        commands[command](rest)
    else:
        print(f"Unknown command '{command}'.")
        print("Available commands: move, save, load, list, delete (or run with no args for a menu).")


if __name__ == "__main__":
    main()
