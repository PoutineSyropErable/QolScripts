#!/usr/bin/env python
from typing import List, Dict, Tuple
from numpy.typing import NDArray
import tkinter as tk
from tkinter import messagebox
from tkinter import simpledialog

import subprocess, os, sys, argparse
import numpy as np
import time
import re

import random
from colorsys import hls_to_rgb
import numpy as np

MAIN_MONITOR = "DP-1"


def notify_send(summary: str, body: str = "", urgency: str = "normal", timeout: int = 5000):
    """
    Sends a desktop notification using notify-send.

    Args:
        summary (str): The title of the notification.
        body (str): Optional body text.
        urgency (str): "low", "normal", or "critical".
        timeout (int): Timeout in milliseconds.
    """
    subprocess.run(["notify-send", "--urgency", urgency, "--expire-time", str(timeout), summary, body])


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
    def __init__(self, name: str, position: Tuple[int, int], resolution: Tuple[int, int], refresh_rate: float):
        """
        :param name: str, monitor identifier
        :param position: tuple (x, y) in pixels
        :param resolution: tuple (width, height) in pixels
        """
        self.name = name
        self.position: NDArray[np.float64] = np.array(list(position))  # (x, y)
        self.resolution = resolution  # (width, height)
        self.color = self._random_light_color()
        self.canvas_id = None  # stores the canvas rectangle ID
        self.refresh_rate = refresh_rate
        self.text_id = None  # stores the canvas text ID

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
        return (
            f"Monitor(name={self.name}, position={self.position}, resolution={self.resolution}, "
            f"refresh_rate={self.refresh_rate}, color={self.color})"
        )


def create_monitors() -> List[Monitor]:
    best_modes = get_best_monitor_modes()
    monitors = []
    x_offset = 0
    for name, (res_str, refresh) in best_modes.items():
        w, h = map(int, res_str.split("x"))
        monitors.append(Monitor(name, (x_offset, 0), (w, h), refresh))
        x_offset += w

    # Move "DP-2" to the front if it exists
    for i, mon in enumerate(monitors):
        if mon.name == "DP-2":
            dp2 = monitors.pop(i)
            monitors.insert(0, dp2)
            break
    return monitors


def calculate_canvas_position(window_width, window_height, canvas_width, canvas_height):
    # center the canvas inside the window

    print(f"window_height = {window_height}")
    print(f"window_width = {window_width}\n")
    pos_x = max(0, (window_width - canvas_width) / 2)
    pos_y = max(0, (window_height - canvas_height) / 2)
    return pos_x, pos_y


align_horizontal = True
align_vertical = True


def toggle_horizontal(event=None):
    global align_horizontal
    align_horizontal = not align_horizontal
    print(f"Horizontal alignment: {align_horizontal}")


def toggle_vertical(event=None):
    global align_vertical
    align_vertical = not align_vertical
    print(f"Vertical alignment: {align_vertical}")


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

    return offset_x


def draw_instructions(canvas, x=10, y=10):
    instructions = ["ESC to stop", "Mouse to drag", "H to toggle horizontal align", "V to toggle vertical align"]
    for i, line in enumerate(instructions):
        canvas.create_text(
            x, y + i * 20, text=line, fill="black", anchor="nw", font=("Arial", 12, "bold")  # north-west anchor, so x,y is top-left of text
        )


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
    print(f"\nvirtual_width = {virtual_width}")
    print(f"virtual_height = {virtual_height}\n")

    root = tk.Tk()
    root.title("Monitor Layout")

    def quit_program(event=None):
        root.destroy()

    root.bind("<Escape>", quit_program)
    root.bind("h", toggle_horizontal)
    root.bind("v", toggle_vertical)

    drag_data = {"x": 0, "y": 0, "item": None, "monitor": None}

    def get_rectangle_corners(canvas, rect_id) -> np.ndarray:
        """
        Given a Tkinter canvas and a rectangle canvas ID,
        return the positions of the four corners as a 4x2 numpy array.

        The order of corners returned is:
        top-left, top-right, bottom-right, bottom-left
        """
        coords = canvas.coords(rect_id)  # [x1, y1, x2, y2]
        if len(coords) != 4:
            # Item does not exist or coords are invalid
            raise ValueError(f"Invalid rectangle coords for item {rect_id}: {coords}")
        x1, y1, x2, y2 = coords
        corners = np.array(
            [
                [x1, y1],  # top-left
                [x2, y1],  # top-right
                [x2, y2],  # bottom-right
                [x1, y2],  # bottom-left
            ]
        )
        return corners

    def on_ready():
        window_width = root.winfo_width()
        window_height = root.winfo_height()
        notify_send("Canvas", f"window_width = {window_width}, window_height = {window_height}")

        scale_x = window_width / virtual_width
        scale_y = window_height / virtual_height
        scale = min(scale_x, scale_y)
        print(f"scale = {scale}")
        # Calculate canvas position (top-left) to center the scaled virtual canvas in window
        center_canvas_width = virtual_width * scale
        center_canvas_height = virtual_height * scale
        notify_send("Canvas", f"center_canvas_width = {center_canvas_width}, center_canvas_height = {center_canvas_height}")
        canvas_pos_x, canvas_pos_y = calculate_canvas_position(window_width, window_height, center_canvas_width, center_canvas_height)
        print(f"canvas_pos_x = {canvas_pos_x}")
        print(f"canvas_pos_y = {canvas_pos_y}")
        canvas.create_rectangle(
            canvas_pos_x,
            canvas_pos_y,
            canvas_pos_x + center_canvas_width,
            canvas_pos_y + center_canvas_height,
            fill="black",
            outline="black",
            width=2,
        )

        canvas.create_rectangle(
            canvas_pos_x,
            canvas_pos_y,
            canvas_pos_x + 10,
            canvas_pos_y + 20,
            fill="red",
            outline="green",
            width=2,
        )

        monitor_offset_x = calculate_monitor_offset(monitors)
        min_y = min(mon.position[1] for mon in monitors)
        max_y = max(mon.position[1] + mon.resolution[1] for mon in monitors)

        monitor_total_height = max_y - min_y
        print(f"monitor_total_height = {monitor_total_height}")

        monitor_offset_y = (virtual_height - monitor_total_height) / 2 - max_height

        print("monitor_offset_x, y = ", monitor_offset_x, monitor_offset_y)

        scaled_xs = []
        scaled_ys = []
        all_mon_rects = {}
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

            rect = canvas.create_rectangle(
                scaled_x,
                scaled_y,
                scaled_x + scaled_w,
                scaled_y + scaled_h,
                fill=mon.color,
                outline="white",
                width=2,
            )
            all_mon_rects[mon] = rect
            scaled_xs.append(scaled_x)
            scaled_xs.append(scaled_x + scaled_w)

            scaled_ys.append(scaled_y)
            scaled_ys.append(scaled_y + scaled_h)

            text = canvas.create_text(
                scaled_x + scaled_w / 2,
                scaled_y + scaled_h / 2,
                text=mon.name,
                fill="black",
                font=("Arial", max(8, int(14 * scale)), "bold"),
            )
            mon.canvas_id = rect
            mon.text_id = text

        left_corner = np.array([min(scaled_xs), min(scaled_ys)])
        right_bottom_corner = np.array([max(scaled_xs), max(scaled_ys)])
        scaled_size = right_bottom_corner - left_corner

        bounding_rect_id = None
        bounding_rect_id = canvas.create_rectangle(
            left_corner[0], left_corner[1], right_bottom_corner[0], right_bottom_corner[1], outline="blue", fill="", width=2
        )

        def update_bounding_box():
            scaled_xs = []
            scaled_ys = []
            for mon in monitors:
                coords = canvas.coords(mon.canvas_id)
                x1, y1, x2, y2 = coords
                scaled_xs.extend([x1, x2])
                scaled_ys.extend([y1, y2])

            left_corner = np.array([min(scaled_xs), min(scaled_ys)])
            right_bottom_corner = np.array([max(scaled_xs), max(scaled_ys)])

            canvas.coords(bounding_rect_id, left_corner[0], left_corner[1], right_bottom_corner[0], right_bottom_corner[1])

        def on_start_drag(event):
            widget = event.widget
            item = widget.find_closest(event.x, event.y)[0]
            for mon in monitors:
                if mon.canvas_id == item:
                    drag_data["item"] = item
                    drag_data["monitor"] = mon
                    drag_data["x"] = event.x
                    drag_data["y"] = event.y
                    break

        def on_drag(event):
            if drag_data["item"] is not None:
                dx = event.x - drag_data["x"]
                dy = event.y - drag_data["y"]
                drag_data["x"] = event.x
                drag_data["y"] = event.y

                canvas.move(drag_data["monitor"].canvas_id, dx, dy)
                canvas.move(drag_data["monitor"].text_id, dx, dy)

        def get_key_points(rect_coords: List[float]) -> np.ndarray:
            """
            Given [x1, y1, x2, y2], returns key points:
            - corners: TL, TR, BR, BL
            - edge midpoints: top, right, bottom, left
            - center
            Returns an (9, 2) array of points.
            """
            x1, y1, x2, y2 = rect_coords
            cx = (x1 + x2) / 2
            cy = (y1 + y2) / 2
            return np.array(
                [
                    [x1, y1],  # top-left
                    [x2, y1],  # top-right
                    [x2, y2],  # bottom-right
                    [x1, y2],  # bottom-left
                    [cx, y1],  # top edge midpoint
                    [x2, cy],  # right edge midpoint
                    [cx, y2],  # bottom edge midpoint
                    [x1, cy],  # left edge midpoint
                    [cx, cy],  # center
                ]
            )

        def get_other_monitors_keypoints_tensor(canvas, all_mon_rects, exclude_monitor) -> np.ndarray:
            """
            Returns a rank-3 tensor of shape (N, 9, 2), containing key points
            from all monitors except the dragged one.

            Each monitor contributes:
            - 4 corners
            - 4 edge midpoints
            - 1 center
            """
            other_points = []
            for mon, rect_id in all_mon_rects.items():
                if mon == exclude_monitor:
                    continue
                coords = canvas.coords(rect_id)  # [x1, y1, x2, y2]
                other_points.append(get_key_points(coords))  # shape (9, 2)
            return np.array(other_points)  # shape (N, 9, 2)

        def find_closest_alignment(dragged_keypoints: np.ndarray, others_tensor: np.ndarray) -> tuple:
            """
            Find the pair of points (from dragged and others) with the smallest Euclidean distance.

            Args:
                dragged_keypoints: (9, 2)
                others_tensor: (N, 9, 2)

            Returns:
                delta (np.ndarray): vector to move dragged monitor (2,)
                dragged_idx, monitor_idx, other_idx (ints): for debugging/inspection
            """
            # Compute all distances: shape (9, N, 9)
            min_dist = float("inf")
            best_delta = np.array([0.0, 0.0])
            best_info = (-1, -1, -1, min_dist)  # drag_idx, monitor_idx, point_idx, dist

            for i, drag_pt in enumerate(dragged_keypoints):  # (9,)
                for j, mon_keypoints in enumerate(others_tensor):  # (N, 9, 2)
                    for k, other_pt in enumerate(mon_keypoints):  # (9,)
                        dist = np.linalg.norm(drag_pt - other_pt)
                        if dist < min_dist:
                            min_dist = dist
                            best_delta = other_pt - drag_pt
                            best_info = (i, j, k, dist)

            return best_delta, best_info

        def on_end_drag(event):
            if drag_data["monitor"] is not None:
                mon = drag_data["monitor"]

                # 1. Get dragged monitor's 9 key points
                dragged_keypoints = get_key_points(canvas.coords(mon.canvas_id))  # shape (9, 2)

                # 2. Get (N, 9, 2) keypoints of all *other* monitors
                others_tensor = get_other_monitors_keypoints_tensor(canvas, all_mon_rects, mon)

                # 3. Find best alignment and delta
                delta, (drag_idx, mon_idx, point_idx, dist) = find_closest_alignment(dragged_keypoints, others_tensor)
                print(f"Snapping dragged point {drag_idx} to monitor {mon_idx}'s point {point_idx} (dist = {dist:.2f})")
                print(f"Delta = {delta}")

                # 4. Move the dragged canvas rectangle and its text label
                align_mask = np.array([align_horizontal, align_vertical])
                delta *= align_mask
                canvas.move(mon.canvas_id, delta[0], delta[1])
                canvas.move(mon.text_id, delta[0], delta[1])

                # 5. Update monitor position logically (from new canvas position)
                x1, y1, x2, y2 = canvas.coords(mon.canvas_id)
                new_adj_x = (x1 - canvas_pos_x) / scale
                new_adj_y = (y1 - canvas_pos_y) / scale
                new_x = new_adj_x - max_width - monitor_offset_x
                new_y = new_adj_y - max_height - monitor_offset_y

                mon.position = np.array([round(new_x), round(new_y)])
                print(f"Updated position of {mon.name}: {mon.position}")

            drag_data["item"] = None
            drag_data["monitor"] = None
            update_bounding_box()

        canvas.bind("<ButtonPress-1>", on_start_drag)
        canvas.bind("<B1-Motion>", on_drag)
        canvas.bind("<ButtonRelease-1>", on_end_drag)

    canvas = tk.Canvas(root, bg="white")
    canvas.pack(fill="both", expand=True)
    root.after(500, on_ready)
    draw_instructions(canvas)
    root.mainloop()


def generate_hypr_monitor_config(monitors: List[Monitor]) -> str:
    """
    Generate Hyprland monitor config lines from a list of Monitor objects.
    Output lines like:
    monitor=DP-1,2560x1440@60,0x0,1
    """
    lines = []
    for mon in monitors:
        name = mon.name
        width, height = mon.resolution
        x, y = map(int, mon.position)
        refresh = int(round(mon.refresh_rate))

        # Format as required by Hyprland
        lines.append(f"monitor={name},{width}x{height}@{refresh},{x}x{y},1")
    return "\n".join(lines)


if __name__ == "__main__":
    print("\n\n====Start of program=====\n\n")
    monitors: List[Monitor] = create_monitors()
    draw_monitors(monitors)
    positions: dict[str, np.ndarray] = {}
    all_pos = []
    for m in monitors:
        positions[m.name] = m.position
        print(positions[m.name])
        all_pos.append(positions[m.name])

    # all_pos = np.array(all_pos)
    # print(f"all_pos = \n{all_pos}\n")
    # col_min: np.ndarray = np.min(all_pos, axis=0)
    # col_max: np.ndarray = np.max(all_pos, axis=0)
    # print(f"col_min = {col_min}")
    # print(f"col_max = {col_max}")

    assert MAIN_MONITOR in positions, "The main monitor should be in the positions"
    dp1_pos = positions[MAIN_MONITOR].copy()
    positions_tuple: Dict[str, Tuple[int, int]] = {}
    for m in monitors:
        # m.position = m.position - col_min
        m.position -= dp1_pos
        positions_tuple[m.name] = tuple(m.position.tolist())

    print("======")
    print(f"positions = \n{positions_tuple}\n")
    meta_code = generate_hypr_monitor_config(monitors)
    print("\n")
    print(meta_code)
