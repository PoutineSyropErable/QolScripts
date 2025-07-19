#!/usr/bin/env python
import tkinter as tk
from tkinter import messagebox
from tkinter import simpledialog

import subprocess, os, sys, argparse
import numpy as np
import time
import re

import random
from colorsys import hls_to_rgb


def list_available_monitor_names():
    # Use xrandr to get connected screens
    xrandr_output = subprocess.check_output(["xrandr"]).decode("utf-8")

    # Extract screen names
    screen_names = []
    lines = xrandr_output.splitlines()
    for line in lines:
        if " connected" in line:
            screen_name = line.split()[0]
            screen_names.append(screen_name)

    return screen_names


def get_best_monitor_modes():
    xrandr_output = subprocess.check_output(["xrandr"]).decode("utf-8")
    lines = xrandr_output.splitlines()

    monitor_modes = {}
    current_monitor = None

    for line in lines:
        if " connected" in line:
            current_monitor = line.split()[0]
            monitor_modes[current_monitor] = []
        elif current_monitor and re.match(r"\s+\d+x\d+", line):
            parts = line.strip().split()
            resolution = parts[0]
            refresh_rates = [float(re.sub(r"[+*]", "", r)) for r in parts[1:] if re.match(r"\d+(\.\d+)?([+*]?)", r)]
            for rate in refresh_rates:
                monitor_modes[current_monitor].append((resolution, rate))

    best_modes = {}
    for monitor, modes in monitor_modes.items():
        if not modes:
            best_modes[monitor] = None
            continue

        def res_area(res):  # resolution area = width × height
            w, h = map(int, res.split("x"))
            return w * h

        # Group refresh rates by resolution
        res_to_rates = {}
        for res, rate in modes:
            res_to_rates.setdefault(res, []).append(rate)

        # Pick the resolution with max area
        best_res = max(res_to_rates.keys(), key=res_area)
        best_rate = max(res_to_rates[best_res])

        best_modes[monitor] = (best_res, round(best_rate))

    return best_modes


class Monitor:
    def __init__(self, name, position, resolution):
        """
        :param name: str, monitor identifier
        :param position: tuple (x, y) in pixels
        :param resolution: tuple (width, height) in pixels
        """
        self.name = name
        self.position = position  # (x, y)
        self.resolution = resolution  # (width, height)
        self.color = self._random_light_color()

    def _random_light_color(self):
        """
        Generate a random light color using HLS:
        - Hue: random 0-1
        - Lightness: high (0.75 - 0.9)
        - Saturation: medium (0.4 - 0.7)
        Returns hex string color like "#aabbcc"
        """
        h = random.random()
        l = random.uniform(0.75, 0.9)
        s = random.uniform(0.4, 0.7)
        r, g, b = hls_to_rgb(h, l, s)
        return f"#{int(r*255):02x}{int(g*255):02x}{int(b*255):02x}"

    def __repr__(self):
        return f"Monitor(name={self.name}, position={self.position}, " f"resolution={self.resolution}, color={self.color})"


def create_monitors():
    best_modes = get_best_monitor_modes()
    monitors = []
    x_offset = 0
    for name, (res_str, refresh) in best_modes.items():
        w, h = map(int, res_str.split("x"))
        monitors.append(Monitor(name, (x_offset, 0), (w, h)))
        x_offset += w
    return monitors


def calculate_canvas_position(window_width, window_height, canvas_width, canvas_height):
    # center the canvas inside the window

    print(f"window_height = {window_height}")
    print(f"canvas_height = {canvas_height}")
    pos_x = max(0, (window_width - canvas_width) / 2)
    pos_y = max(0, (window_height - canvas_height) / 2)
    return pos_x, pos_y


def calculate_monitor_offset(monitors):
    """
    Calculate horizontal offset to center the monitors in the virtual canvas,
    so that the middle monitor (or middle point between two center monitors)
    is aligned with the horizontal center of the virtual canvas.

    Returns (offset_x, offset_y) which can be added to each monitor's position.
    """
    n = len(monitors)
    if n == 0:
        return 0, 0

    # Sort monitors by their x position
    monitors_sorted = sorted(monitors, key=lambda m: m.position[0])

    # Compute total width
    total_width = sum(mon.resolution[0] for mon in monitors)

    # Find middle monitor(s)
    if n % 2 == 1:
        # Odd: center the middle monitor's center
        mid_index = n // 2
        mid_mon = monitors_sorted[mid_index]
        mid_center_x = mid_mon.position[0] + mid_mon.resolution[0] / 2
        center_x = total_width / 2
        offset_x = center_x - mid_center_x
    else:
        # Even: center the midpoint between two middle monitors
        mid_index1 = n // 2 - 1
        mid_index2 = n // 2
        mon1 = monitors_sorted[mid_index1]
        mon2 = monitors_sorted[mid_index2]
        mid_center_x = (mon1.position[0] + mon1.resolution[0] + mon2.position[0]) / 2
        center_x = total_width / 2
        offset_x = center_x - mid_center_x

    # Vertical offset: keep as 0 for now (no vertical shift)
    offset_y = 0

    return offset_x, offset_y


def draw_monitors(monitors):
    # Calculate layout bounds
    widths = [mon.position[0] + mon.resolution[0] for mon in monitors]
    heights = [mon.position[1] + mon.resolution[1] for mon in monitors]

    sum_width = sum(mon.resolution[0] for mon in monitors)
    sum_height = sum(mon.resolution[1] for mon in monitors)
    max_width = max(mon.resolution[0] for mon in monitors)
    max_height = max(mon.resolution[1] for mon in monitors)

    # Virtual canvas size with margin for one extra monitor left/right/top/bottom
    virtual_width = sum_width + 2 * max_width
    virtual_height = sum_height + 2 * max_height

    root = tk.Tk()
    root.title("Monitor Layout")
    root.update_idletasks()  # Ensure geometry is calculated
    window_width = root.winfo_width()
    window_height = root.winfo_height()

    print(f"window_width = {window_width}")
    print(f"window_height = {window_height}")

    canvas = tk.Canvas(root, width=window_width, height=window_height, bg="white")
    # Create canvas inside window
    canvas.pack()
    # Calculate uniform scale factor to fit virtual canvas into window canvas
    scale_x = window_width / virtual_width
    scale_y = window_height / virtual_height
    scale = min(scale_x, scale_y)
    print(f"scale = {scale}")

    # Calculate canvas position (top-left) to center the scaled virtual canvas in window
    canvas_pos_x, canvas_pos_y = calculate_canvas_position(window_width, window_height, virtual_width * scale, virtual_height * scale)

    # Calculate horizontal monitor offset for centering middle monitor(s)
    monitor_offset_x, monitor_offset_y = calculate_monitor_offset(monitors)
    print(f"canvas_pos_x = {canvas_pos_x}")
    print(f"canvas_pos_y = {canvas_pos_y}")

    canvas.create_rectangle(
        canvas_pos_x,
        canvas_pos_y,
        canvas_pos_x + window_width * scale,
        canvas_pos_y + window_height * scale,
        fill="black",
        outline="black",
        width=2,
    )
    root.mainloop()
    return

    # Draw monitors scaled, offset by margin + monitor offset + centered in window
    for mon in monitors:
        x, y = mon.position
        w, h = mon.resolution

        # Adjust position with margin and centering offsets
        adj_x = x + max_width + monitor_offset_x
        adj_y = y + max_height + monitor_offset_y

        # Scale and offset to fit and center in canvas
        scaled_x = scale * adj_x + canvas_pos_x
        scaled_y = scale * adj_y + canvas_pos_y
        scaled_w = scale * w
        scaled_h = scale * h

        canvas.create_rectangle(
            scaled_x,
            scaled_y,
            scaled_x + scaled_w,
            scaled_y + scaled_h,
            fill=mon.color,
            outline="white",
            width=2,
        )
        canvas.create_text(
            scaled_x + scaled_w / 2,
            scaled_y + scaled_h / 2,
            text=mon.name,
            fill="black",
            font=("Arial", max(8, int(14 * scale)), "bold"),
        )

    root.mainloop()


if __name__ == "__main__":
    print("\n\n====Start of program=====\n\n")
    monitors = create_monitors()
    for m in monitors:
        print(m)
    draw_monitors(monitors)
