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
from tkinter import ttk, messagebox, simpledialog
from pathlib import Path

try:
    import pyautogui
except ImportError:
    pyautogui = None

PRESETS_FILE = Path(__file__).with_name("jrz_presets.json")
MOVE_DELAY = 0.3     # short pause before moving, so you can release keys/focus a window
MOVE_DURATION = 0.2  # how long the mouse takes to glide to the new spot

# ---------------------------------------------------------------------------
# Design tokens (matches a purple "dashboard kit" look: soft lavender base,
# white rounded cards, purple gradient primary buttons, light pill inputs)
# ---------------------------------------------------------------------------
BASE_BG = "#EEF0FB"
CARD_BG = "#FFFFFF"
PILL_BG = "#F2F1FA"
BORDER = "#E7E5F5"
PURPLE_LIGHT = "#9B6BFF"
PURPLE_DARK = "#5B2FE0"
PURPLE_TEXT = "#5B2FE0"
TEXT_DARK = "#241F35"
TEXT_GRAY = "#8D8AA0"
DANGER_TEXT = "#E0537A"

FONT = "Segoe UI"


# ---------------------------------------------------------------------------
# Small canvas drawing helpers (rounded rectangles + horizontal gradients)
# ---------------------------------------------------------------------------
def round_rect(canvas, x1, y1, x2, y2, radius=18, **kwargs):
    """Draw (and return the id of) a rounded rectangle on a canvas."""
    points = [
        x1 + radius, y1,
        x2 - radius, y1,
        x2, y1,
        x2, y1 + radius,
        x2, y2 - radius,
        x2, y2,
        x2 - radius, y2,
        x1 + radius, y2,
        x1, y2,
        x1, y2 - radius,
        x1, y1 + radius,
        x1, y1,
    ]
    return canvas.create_polygon(points, smooth=True, **kwargs)


def _lerp_color(c1, c2, t):
    c1 = c1.lstrip("#")
    c2 = c2.lstrip("#")
    r1, g1, b1 = int(c1[0:2], 16), int(c1[2:4], 16), int(c1[4:6], 16)
    r2, g2, b2 = int(c2[0:2], 16), int(c2[2:4], 16), int(c2[4:6], 16)
    r = round(r1 + (r2 - r1) * t)
    g = round(g1 + (g2 - g1) * t)
    b = round(b1 + (b2 - b1) * t)
    return f"#{r:02x}{g:02x}{b:02x}"


def gradient_pill(canvas, x1, y1, x2, y2, color1, color2, tags):
    """Draw a horizontally-gradiented pill (rounded ends, gradient fill)."""
    radius = (y2 - y1) / 2
    canvas.create_arc(x1, y1, x1 + 2 * radius, y2, start=90, extent=180,
                       fill=color1, outline=color1, tags=tags)
    canvas.create_arc(x2 - 2 * radius, y1, x2, y2, start=270, extent=180,
                       fill=color2, outline=color2, tags=tags)
    inner_x1, inner_x2 = x1 + radius, x2 - radius
    width = max(int(inner_x2 - inner_x1), 1)
    for i in range(width):
        t = i / max(width - 1, 1)
        color = _lerp_color(color1, color2, t)
        xx = inner_x1 + i
        canvas.create_line(xx, y1, xx, y2, fill=color, tags=tags)


class PillButton:
    """A clickable rounded button drawn on a canvas (primary/secondary/danger)."""

    def __init__(self, canvas, x1, y1, x2, y2, text, command, style="primary", font_size=11):
        self.canvas = canvas
        self.coords = (x1, y1, x2, y2)
        self.command = command
        self.style = style
        self.tag = f"btn_{id(self)}"
        self.text = text
        self.font_size = font_size
        self._draw()
        canvas.tag_bind(self.tag, "<Button-1>", lambda e: self.command())
        canvas.tag_bind(self.tag, "<Enter>", lambda e: self._hover(True))
        canvas.tag_bind(self.tag, "<Leave>", lambda e: self._hover(False))

    def _draw(self, hovered=False):
        self.canvas.delete(self.tag)
        x1, y1, x2, y2 = self.coords
        if self.style == "primary":
            c1, c2 = (PURPLE_DARK, PURPLE_LIGHT) if hovered else (PURPLE_LIGHT, PURPLE_DARK)
            gradient_pill(self.canvas, x1, y1, x2, y2, c1, c2, self.tag)
            text_color = "white"
        elif self.style == "danger":
            fill = "#F7E4EA" if not hovered else "#F3D3DD"
            round_rect(self.canvas, x1, y1, x2, y2, radius=(y2 - y1) / 2,
                       fill=fill, outline=fill, tags=self.tag)
            text_color = DANGER_TEXT
        else:  # secondary
            fill = PILL_BG if not hovered else BORDER
            round_rect(self.canvas, x1, y1, x2, y2, radius=(y2 - y1) / 2,
                       fill=fill, outline=fill, tags=self.tag)
            text_color = PURPLE_TEXT
        self.canvas.create_text(
            (x1 + x2) / 2, (y1 + y2) / 2, text=self.text,
            fill=text_color, font=(FONT, self.font_size, "bold"), tags=self.tag,
        )
        self.canvas.tag_raise(self.tag)

    def _hover(self, on):
        self.canvas.config(cursor="hand2" if on else "")
        self._draw(hovered=on)


# ---------------------------------------------------------------------------
# Presets persistence
# ---------------------------------------------------------------------------
def load_presets():
    if PRESETS_FILE.exists():
        try:
            return json.loads(PRESETS_FILE.read_text())
        except json.JSONDecodeError:
            return {}
    return {}


def save_presets(presets):
    PRESETS_FILE.write_text(json.dumps(presets, indent=2))


# ---------------------------------------------------------------------------
# Main app
# ---------------------------------------------------------------------------
class JRZMouseMoverApp:
    WIDTH = 400
    HEIGHT = 740

    def __init__(self, root):
        self.root = root
        self.root.title("JRZ Mouse Mover")
        self.root.geometry(f"{self.WIDTH}x{self.HEIGHT}")
        self.root.resizable(False, False)
        self.root.configure(bg=BASE_BG)

        self.presets = load_presets()
        self.strength_var = tk.IntVar(value=100)
        self.status_var = tk.StringVar(value="Ready.")

        self._setup_ttk_style()

        # Single canvas = the whole "screen" (the base), everything else
        # is drawn or embedded on top of it, dashboard-kit style.
        self.canvas = tk.Canvas(root, width=self.WIDTH, height=self.HEIGHT,
                                 bg=BASE_BG, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)

        self._draw_header()
        self._draw_strength_card()
        self._draw_presets_card()
        self._draw_status_pill()

        self.strength_var.trace_add("write", self._on_strength_changed)
        self.refresh_preset_list()

        if pyautogui is None:
            self.status_var.set("Missing dependency: run 'pip install pyautogui'")
            messagebox.showwarning(
                "Missing dependency",
                "pyautogui isn't installed, so moving the mouse won't work yet.\n\n"
                "Run:  pip install pyautogui"
            )

    # --- one-time ttk styling so native widgets (slider, listbox) match ---
    def _setup_ttk_style(self):
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure(
            "Purple.Horizontal.TScale",
            background=CARD_BG,
            troughcolor=PILL_BG,
            bordercolor=CARD_BG,
            lightcolor=PURPLE_DARK,
            darkcolor=PURPLE_DARK,
        )
        style.map("Purple.Horizontal.TScale", background=[("active", CARD_BG)])

    # --- layout: header ---
    def _draw_header(self):
        c = self.canvas
        c.create_text(28, 30, anchor="nw", text="JRZ Mouse Mover",
                       fill=PURPLE_DARK, font=(FONT, 19, "bold"))
        c.create_text(28, 60, anchor="nw", text="cursor automation, made simple",
                       fill=TEXT_GRAY, font=(FONT, 10))

    # --- layout: strength card ---
    def _draw_strength_card(self):
        c = self.canvas
        x1, y1, x2, y2 = 24, 96, 376, 372
        round_rect(c, x1, y1, x2, y2, radius=22, fill=CARD_BG, outline=CARD_BG)

        c.create_text(x1 + 20, y1 + 24, anchor="w", text="cursor strength",
                       fill=TEXT_DARK, font=(FONT, 12, "bold"))
        self.value_text_id = c.create_text(
            x2 - 20, y1 + 24, anchor="e", text="100 px",
            fill=PURPLE_TEXT, font=(FONT, 14, "bold"),
        )

        # slider
        slider = ttk.Scale(
            c, from_=1, to=1000, orient="horizontal",
            variable=self.strength_var, style="Purple.Horizontal.TScale",
        )
        c.create_window(x1 + 20, y1 + 66, anchor="nw", window=slider,
                         width=x2 - x1 - 40, height=22)
        c.create_text(x1 + 20, y1 + 96, anchor="w", text="1",
                       fill=TEXT_GRAY, font=(FONT, 8))
        c.create_text(x2 - 20, y1 + 96, anchor="e", text="1000",
                       fill=TEXT_GRAY, font=(FONT, 8))

        # "exact value" pill input + Set button
        row_y1, row_y2 = y1 + 118, y1 + 158
        entry_x1, entry_x2 = x1 + 20, x1 + 226
        round_rect(c, entry_x1, row_y1, entry_x2, row_y2,
                   radius=(row_y2 - row_y1) / 2, fill=PILL_BG, outline=PILL_BG)

        self.strength_entry = tk.Entry(
            c, justify="center", relief="flat", bg=PILL_BG, fg=TEXT_DARK,
            font=(FONT, 11), highlightthickness=0, bd=0,
        )
        self.strength_entry.insert(0, str(self.strength_var.get()))
        c.create_window(
            (entry_x1 + entry_x2) / 2, (row_y1 + row_y2) / 2,
            window=self.strength_entry, width=entry_x2 - entry_x1 - 24,
            height=row_y2 - row_y1 - 12,
        )

        PillButton(c, x1 + 236, row_y1, x2 - 20, row_y2, "Set",
                   self.set_strength_from_entry, style="secondary", font_size=10)

        # primary action button
        btn_y1, btn_y2 = row_y2 + 20, row_y2 + 64
        PillButton(c, x1 + 20, btn_y1, x2 - 20, btn_y2, "Move Mouse Down",
                   self.move_mouse, style="primary", font_size=12)

    # --- layout: presets card ---
    def _draw_presets_card(self):
        c = self.canvas
        x1, y1, x2, y2 = 24, 392, 376, 690
        round_rect(c, x1, y1, x2, y2, radius=22, fill=CARD_BG, outline=CARD_BG)

        c.create_text(x1 + 20, y1 + 24, anchor="w", text="presets",
                       fill=TEXT_DARK, font=(FONT, 12, "bold"))

        list_y1, list_y2 = y1 + 48, y1 + 190
        round_rect(c, x1 + 20, list_y1, x2 - 20, list_y2, radius=14,
                   fill=PILL_BG, outline=PILL_BG)

        self.preset_listbox = tk.Listbox(
            c, relief="flat", bd=0, highlightthickness=0, bg=PILL_BG,
            fg=TEXT_DARK, font=(FONT, 10), selectbackground=PURPLE_LIGHT,
            selectforeground="white", activestyle="none",
        )
        self.preset_listbox.bind("<<ListboxSelect>>", self.on_preset_select)
        c.create_window((x1 + x2) / 2, (list_y1 + list_y2) / 2,
                         window=self.preset_listbox, width=x2 - x1 - 48,
                         height=list_y2 - list_y1 - 16)

        btn_y1, btn_y2 = list_y2 + 18, list_y2 + 56
        gap = 8
        btn_w = (x2 - x1 - 40 - 2 * gap) / 3
        bx = x1 + 20
        PillButton(c, bx, btn_y1, bx + btn_w, btn_y2, "Save",
                   self.save_preset, style="primary", font_size=10)
        bx += btn_w + gap
        PillButton(c, bx, btn_y1, bx + btn_w, btn_y2, "Load",
                   self.load_preset, style="secondary", font_size=10)
        bx += btn_w + gap
        PillButton(c, bx, btn_y1, bx + btn_w, btn_y2, "Delete",
                   self.delete_preset, style="danger", font_size=10)

    # --- layout: status pill ---
    def _draw_status_pill(self):
        c = self.canvas
        x1, y1, x2, y2 = 24, 704, 376, 730
        self.status_bg_id = round_rect(c, x1, y1, x2, y2, radius=13,
                                        fill=PILL_BG, outline=PILL_BG)
        self.status_text_id = c.create_text(
            (x1 + x2) / 2, (y1 + y2) / 2, text=self.status_var.get(),
            fill=PURPLE_TEXT, font=(FONT, 9, "bold"),
        )
        self.status_var.trace_add(
            "write",
            lambda *a: self.canvas.itemconfig(self.status_text_id, text=self.status_var.get()),
        )

    # --- strength helpers ---
    def _on_strength_changed(self, *args):
        value = self.strength_var.get()
        self.strength_entry.delete(0, tk.END)
        self.strength_entry.insert(0, str(value))
        self.canvas.itemconfig(self.value_text_id, text=f"{value} px")

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
            self.preset_listbox.insert(tk.END, f"  {name}   ({amount}px)")

    def get_selected_preset_name(self):
        selection = self.preset_listbox.curselection()
        if not selection:
            return None
        text = self.preset_listbox.get(selection[0])
        return text.strip().split("   (")[0]

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
