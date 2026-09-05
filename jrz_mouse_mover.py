#!/usr/bin/env python3
"""
JRZ Mouse Mover
---------------
A small desktop app with a UI: moves your mouse cursor down by an
adjustable "strength" (amount in pixels), with named presets you can
save and reload.

Setup (one time):
    pip install pyautogui

Run:
    python jrz_mouse_mover.py
"""

import json
import time
import tkinter as tk
from tkinter import messagebox, simpledialog
from pathlib import Path

try:
    import pyautogui
except ImportError:
    pyautogui = None

PRESETS_FILE = Path(__file__).with_name("jrz_presets.json")
MOVE_DELAY = 0.3     # short pause before moving, so you can release keys/focus a window
MOVE_DURATION = 0.2  # how long the mouse takes to glide to the new spot


def load_presets():
    if PRESETS_FILE.exists():
        try:
            return json.loads(PRESETS_FILE.read_text())
        except json.JSONDecodeError:
            return {}
    return {}


def save_presets(presets):
    PRESETS_FILE.write_text(json.dumps(presets, indent=2))


class JRZMouseMoverApp:
    def __init__(self, root):
        self.root = root
        self.root.title("JRZ Mouse Mover")
        self.root.geometry("360x420")
        self.root.resizable(False, False)

        self.presets = load_presets()

        # --- Strength section ---
        tk.Label(root, text="JRZ Mouse Mover", font=("Segoe UI", 16, "bold")).pack(pady=(16, 4))
        tk.Label(root, text="Move the cursor down by this much (px):").pack(pady=(8, 2))

        self.strength_var = tk.IntVar(value=100)

        self.strength_scale = tk.Scale(
            root, from_=1, to=1000, orient="horizontal",
            variable=self.strength_var, length=280, showvalue=True
        )
        self.strength_scale.pack(pady=(0, 4))

        entry_frame = tk.Frame(root)
        entry_frame.pack(pady=(0, 12))
        tk.Label(entry_frame, text="Exact value:").pack(side="left", padx=(0, 6))
        self.strength_entry = tk.Entry(entry_frame, width=8, justify="center")
        self.strength_entry.insert(0, "100")
        self.strength_entry.pack(side="left")
        tk.Button(entry_frame, text="Set", command=self.set_strength_from_entry).pack(side="left", padx=6)

        self.strength_var.trace_add("write", self.sync_entry_from_slider)

        tk.Button(
            root, text="Move Mouse Down", font=("Segoe UI", 11, "bold"),
            bg="#2d7cf0", fg="white", height=2, command=self.move_mouse
        ).pack(pady=(4, 16), fill="x", padx=30)

        # --- Presets section ---
        tk.Label(root, text="Presets", font=("Segoe UI", 12, "bold")).pack()

        self.preset_listbox = tk.Listbox(root, height=6)
        self.preset_listbox.pack(pady=(4, 6), padx=30, fill="x")
        self.preset_listbox.bind("<<ListboxSelect>>", self.on_preset_select)
        self.refresh_preset_list()

        preset_btns = tk.Frame(root)
        preset_btns.pack(pady=(0, 10))
        tk.Button(preset_btns, text="Save Current as Preset", command=self.save_preset).grid(row=0, column=0, padx=4)
        tk.Button(preset_btns, text="Load Preset", command=self.load_preset).grid(row=0, column=1, padx=4)
        tk.Button(preset_btns, text="Delete Preset", command=self.delete_preset).grid(row=0, column=2, padx=4)

        self.status_var = tk.StringVar(value="Ready.")
        tk.Label(root, textvariable=self.status_var, fg="#555").pack(pady=(6, 0))

        if pyautogui is None:
            self.status_var.set("Missing dependency: run 'pip install pyautogui'")
            messagebox.showwarning(
                "Missing dependency",
                "pyautogui isn't installed, so moving the mouse won't work yet.\n\n"
                "Run:  pip install pyautogui"
            )

    # --- strength helpers ---
    def sync_entry_from_slider(self, *args):
        self.strength_entry.delete(0, tk.END)
        self.strength_entry.insert(0, str(self.strength_var.get()))

    def set_strength_from_entry(self):
        try:
            value = int(self.strength_entry.get())
            value = max(1, min(value, 5000))
            self.strength_var.set(value)
            self.status_var.set(f"Strength set to {value}px.")
        except ValueError:
            messagebox.showerror("Invalid value", "Please enter a whole number.")

    # --- actions ---
    def move_mouse(self):
        if pyautogui is None:
            messagebox.showerror("Missing dependency", "Install it first with: pip install pyautogui")
            return
        amount = self.strength_var.get()
        self.status_var.set(f"Moving down {amount}px...")
        self.root.update_idletasks()
        time.sleep(MOVE_DELAY)
        x, y = pyautogui.position()
        pyautogui.moveTo(x, y + amount, duration=MOVE_DURATION)
        self.status_var.set(f"Moved down {amount}px.")

    def refresh_preset_list(self):
        self.preset_listbox.delete(0, tk.END)
        for name, amount in self.presets.items():
            self.preset_listbox.insert(tk.END, f"{name}  ({amount}px)")

    def get_selected_preset_name(self):
        selection = self.preset_listbox.curselection()
        if not selection:
            return None
        text = self.preset_listbox.get(selection[0])
        return text.split("  (")[0]

    def on_preset_select(self, event):
        name = self.get_selected_preset_name()
        if name and name in self.presets:
            self.status_var.set(f"Selected preset '{name}' = {self.presets[name]}px.")

    def save_preset(self):
        amount = self.strength_var.get()
        name = simpledialog.askstring("Save Preset", f"Name this preset (strength = {amount}px):")
        if not name:
            return
        self.presets[name] = amount
        save_presets(self.presets)
        self.refresh_preset_list()
        self.status_var.set(f"Saved preset '{name}' = {amount}px.")

    def load_preset(self):
        name = self.get_selected_preset_name()
        if not name:
            messagebox.showinfo("No preset selected", "Click a preset in the list first.")
            return
        amount = self.presets.get(name)
        if amount is None:
            return
        self.strength_var.set(amount)
        self.status_var.set(f"Loaded preset '{name}' = {amount}px.")

    def delete_preset(self):
        name = self.get_selected_preset_name()
        if not name:
            messagebox.showinfo("No preset selected", "Click a preset in the list first.")
            return
        if messagebox.askyesno("Delete preset", f"Delete preset '{name}'?"):
            self.presets.pop(name, None)
            save_presets(self.presets)
            self.refresh_preset_list()
            self.status_var.set(f"Deleted preset '{name}'.")


def main():
    root = tk.Tk()
    app = JRZMouseMoverApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
