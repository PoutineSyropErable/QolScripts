from numpy.typing import NDArray
import tkinter as tk
from tkinter import messagebox
from tkinter import simpledialog
from typing import List, Tuple, Dict, Literal

import subprocess, os, sys, argparse

import numpy as np
import time
import re

import random
from colorsys import hls_to_rgb
import numpy as np

MAIN_MONITOR = "DP-1"
WAYLAND_WINDOW_CREATION_TIME = 500
from hyprland_sig import env


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
    def __init__(
        self, name: str, position: Tuple[int, int], resolution: Tuple[int, int], refresh_rate: float, transform: int = 0, scale: float = 1.0
    ):
        """
        :param name: str, monitor identifier
        :param position: tuple (x, y) in pixels
        :param resolution: tuple (width, height) in pixels
        :param transform: 0=normal, 1=90°, 2=180°, 3=270°
        :param scale: scaling factor (e.g., 1.0 = 100%, 1.5 = 150%)
        """
        self.name = name
        self.position: NDArray[np.float64] = np.array(list(position))  # (x, y)
        self.color = self._random_light_color()
        self.canvas_id = None
        self.refresh_rate = refresh_rate
        self.text_id = None
        self.scale = scale

        self.first_transform = transform
        self.transform = transform  # rotation
        self._base_resolution = resolution  # store the "natural" resolution
        self.resolution = self._apply_transform_resolution()
        assert transform in [0, 1, 2, 3]

    def _apply_transform_resolution(self) -> Tuple[int, int]:
        """Return resolution depending on rotation: swap width/height if rotated 90° or 270°."""
        w, h = self._base_resolution
        if self.transform % 2 == 1:  # 90° or 270°
            return (h, w)
        return (w, h)

    def get_effective_resolution(self) -> Tuple[int, int]:
        """Get the effective resolution after applying scale."""
        w, h = self.resolution
        return (int(w / self.scale), int(h / self.scale))

    def get_rotation(self) -> int:
        """Return rotation in degrees corresponding to transform."""
        rotation_dict = {0: 0, 1: 90, 2: 180, 3: 270}
        return rotation_dict[self.transform]

    def set_rotation(self, rotation_degree: Literal[0, 90, 180, 270]):
        assert rotation_degree in [0, 90, 180, 270]
        self.transform = rotation_degree // 90
        self.resolution = self._apply_transform_resolution()  # update resolution

    def rotate_clockwise(self):
        self.transform = (self.transform + 1) % 4
        self.resolution = self._apply_transform_resolution()

    def rotate_anticlockwise(self):
        self.transform = (self.transform - 1) % 4
        self.resolution = self._apply_transform_resolution()

    def set_scale(self, scale: float):
        """Set scale factor (e.g., 1.0 = 100%, 1.5 = 150%)."""
        assert scale > 0, "Scale must be positive"
        self.scale = scale

    def get_scale(self) -> float:
        return self.scale

    # --- Corner and center offsets ---

    def top_left_offset(self) -> NDArray[np.float64]:
        """Vector from position to top-left corner (always 0,0)."""
        return np.array([0.0, 0.0])

    def top_right_offset(self) -> NDArray[np.float64]:
        """Vector from position to top-right corner."""
        w, h = self.resolution
        return np.array([w, 0.0])

    def bottom_left_offset(self) -> NDArray[np.float64]:
        """Vector from position to bottom-left corner."""
        w, h = self.resolution
        return np.array([0.0, h])

    def bottom_right_offset(self) -> NDArray[np.float64]:
        """Vector from position to bottom-right corner."""
        w, h = self.resolution
        return np.array([w, h])

    def center_offset(self) -> NDArray[np.float64]:
        """Vector from position to center of the monitor."""
        w, h = self.resolution
        return np.array([w / 2, h / 2])

    def _random_light_color(self):
        h = random.random()
        l = random.uniform(0.75, 0.9)
        s = random.uniform(0.4, 0.7)
        r, g, b = hls_to_rgb(h, l, s)
        return f"#{int(r*255):02x}{int(g*255):02x}{int(b*255):02x}"

    def __repr__(self):
        return (
            f"Monitor(name={self.name}, position={self.position}, resolution={self.resolution}, "
            f"refresh_rate={self.refresh_rate}, scale={self.scale}, transform={self.get_rotation()}°)"
        )


def create_monitors() -> List[Monitor]:
    best_modes = get_best_monitor_modes()

    print(f"best_modes = {best_modes}")
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
    instructions = [
        "ESC to stop",
        "Mouse to drag",
        "H to toggle horizontal align",
        "V to toggle vertical align",
        "R to rotate clockwise",
        "Shift+R to rotate counter-clockwise",
        "S to change scale",
        "+/- to adjust scale",
    ]
    for i, line in enumerate(instructions):
        canvas.create_text(x, y + i * 20, text=line, fill="black", anchor="nw", font=("Arial", 10, "bold"))


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
    root.title("Monitor Layout - Scale and Rotation Support")

    def quit_program(event=None):
        print("Quitting program")
        root.destroy()

    def rotate_selected_clockwise(event):

        item = canvas.find_withtag("selected")
        print(f"item = {item}")
        if item:
            for mon in monitors:
                if mon.canvas_id == item[0]:
                    mon.rotate_clockwise()
                    update_monitor_display(mon)
                    break

    def rotate_selected_anticlockwise(event=None):
        item = canvas.find_withtag("selected")
        print(f"item = {item}")
        if item:
            for mon in monitors:
                if mon.canvas_id == item[0]:
                    mon.rotate_anticlockwise()
                    update_monitor_display(mon)
                    break

    def change_scale(event=None):
        item = canvas.find_withtag("selected")
        print(f"item = {item}")
        if item:
            for mon in monitors:
                if mon.canvas_id == item[0]:
                    new_scale = simpledialog.askfloat(
                        "Scale Factor",
                        f"Enter scale factor for {mon.name} (current: {mon.scale}):",
                        initialvalue=mon.scale,
                        minvalue=0.5,
                        maxvalue=3.0,
                    )
                    if new_scale:
                        mon.set_scale(new_scale)
                        update_monitor_display(mon)
                    break

    def increase_scale(event=None):
        item = canvas.find_withtag("selected")
        print(f"item = {item}")
        if item:
            for mon in monitors:
                if mon.canvas_id == item[0]:
                    mon.scale = min(3.0, mon.scale + 0.1)
                    update_monitor_display(mon)
                    break

    def decrease_scale(event=None):
        item = canvas.find_withtag("selected")
        print(f"item = {item}")
        if item:
            for mon in monitors:
                if mon.canvas_id == item[0]:
                    mon.scale = max(0.5, mon.scale - 0.1)
                    update_monitor_display(mon)
                    break

    def update_monitor_display(monitor):
        """Update the visual representation of a monitor after rotation or scale change."""
        # Remove old items
        canvas.delete(monitor.canvas_id)
        canvas.delete(monitor.text_id)

        # Get current position and calculate new display
        x1, y1, x2, y2 = get_monitor_canvas_coords(monitor)

        # Create new rectangle
        monitor.canvas_id = canvas.create_rectangle(x1, y1, x2, y2, fill=monitor.color, outline="white", width=2, tags="monitor")

        # Create new text
        monitor.text_id = canvas.create_text(
            (x1 + x2) / 2,
            (y1 + y2) / 2,
            text=f"{monitor.name}\n{monitor.get_rotation()}°\n{monitor.scale:.1f}x",
            fill="black",
            font=("Arial", 10, "bold"),
            tags="monitor_text",
        )

        update_bounding_box()

    def get_monitor_canvas_coords(monitor):
        """Calculate canvas coordinates for a monitor."""
        x, y = monitor.position
        w, h = monitor.resolution

        # Adjust position with margin and centering offsets
        adj_x = x + max_width + monitor_offset_x
        adj_y = y + max_height + monitor_offset_y

        # Scale and offset to fit and center in canvas
        scaled_x = scale * adj_x + canvas_pos_x
        scaled_y = scale * adj_y + canvas_pos_y
        scaled_w = scale * w
        scaled_h = scale * h

        return scaled_x, scaled_y, scaled_x + scaled_w, scaled_y + scaled_h

    root.bind("<Escape>", quit_program)
    root.bind("h", toggle_horizontal)
    root.bind("v", toggle_vertical)
    root.bind("r", rotate_selected_clockwise)
    root.bind("R", rotate_selected_anticlockwise)  # Shift+R
    root.bind("s", change_scale)
    root.bind("<plus>", increase_scale)
    root.bind("<minus>", decrease_scale)

    drag_data = {"x": 0, "y": 0, "item": None, "monitor": None}

    def on_ready():
        print("Calling on ready")
        nonlocal scale, canvas_pos_x, canvas_pos_y, monitor_offset_x, monitor_offset_y

        window_width = root.winfo_width()
        window_height = root.winfo_height()

        scale_x = window_width / virtual_width
        scale_y = window_height / virtual_height
        scale = min(scale_x, scale_y)

        # Calculate canvas position (top-left) to center the scaled virtual canvas in window
        center_canvas_width = virtual_width * scale
        center_canvas_height = virtual_height * scale
        canvas_pos_x, canvas_pos_y = calculate_canvas_position(window_width, window_height, center_canvas_width, center_canvas_height)

        # Draw background
        canvas.create_rectangle(
            canvas_pos_x,
            canvas_pos_y,
            canvas_pos_x + center_canvas_width,
            canvas_pos_y + center_canvas_height,
            fill="lightgray",
            outline="black",
            width=2,
        )

        monitor_offset_x = calculate_monitor_offset(monitors)
        min_y = min(mon.position[1] for mon in monitors)
        max_y = max(mon.position[1] + mon.resolution[1] for mon in monitors)

        monitor_total_height = max_y - min_y
        monitor_offset_y = (virtual_height - monitor_total_height) / 2 - max_height

        # Draw all monitors
        for mon in monitors:
            x1, y1, x2, y2 = get_monitor_canvas_coords(mon)

            rect = canvas.create_rectangle(x1, y1, x2, y2, fill=mon.color, outline="white", width=2, tags="monitor")
            all_mon_rects[mon] = rect

            text = canvas.create_text(
                (x1 + x2) / 2,
                (y1 + y2) / 2,
                text=f"{mon.name}\n{mon.get_rotation()}°\n{mon.scale:.1f}x",
                fill="black",
                font=("Arial", 10, "bold"),
                tags="monitor_text",
            )
            mon.canvas_id = rect
            mon.text_id = text

        update_bounding_box()
        canvas.bind("<ButtonPress-1>", on_start_drag)
        canvas.bind("<B1-Motion>", on_drag)
        canvas.bind("<ButtonRelease-1>", on_end_drag)

    canvas = tk.Canvas(root, bg="white")
    canvas.pack(fill="both", expand=True)

    # Initialize these as nonlocal variables
    scale = 1.0
    canvas_pos_x = 0
    canvas_pos_y = 0
    monitor_offset_x = 0
    monitor_offset_y = 0
    all_mon_rects = {}
    bounding_rect_id = None

    def update_bounding_box():
        nonlocal bounding_rect_id
        scaled_xs = []
        scaled_ys = []
        for mon in monitors:
            coords = canvas.coords(mon.canvas_id)
            x1, y1, x2, y2 = coords
            scaled_xs.extend([x1, x2])
            scaled_ys.extend([y1, y2])

        if not scaled_xs:
            return

        left_corner = np.array([min(scaled_xs), min(scaled_ys)])
        right_bottom_corner = np.array([max(scaled_xs), max(scaled_ys)])

        if bounding_rect_id:
            canvas.coords(bounding_rect_id, left_corner[0], left_corner[1], right_bottom_corner[0], right_bottom_corner[1])
        else:
            bounding_rect_id = canvas.create_rectangle(
                left_corner[0], left_corner[1], right_bottom_corner[0], right_bottom_corner[1], outline="blue", fill="", width=2
            )

    def on_start_drag(event):
        widget = event.widget
        item = widget.find_closest(event.x, event.y)[0]
        print(f"item = {item}")

        # Clear previous selection
        canvas.itemconfig("selected", outline="white")
        canvas.dtag("all", "selected")

        for mon in monitors:
            if mon.canvas_id == item:
                drag_data["item"] = item
                drag_data["monitor"] = mon
                drag_data["x"] = event.x
                drag_data["y"] = event.y
                # Mark as selected
                canvas.itemconfig(item, outline="yellow", width=3)
                canvas.addtag("selected", "withtag", item)
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
        other_points = []
        for mon, rect_id in all_mon_rects.items():
            if mon == exclude_monitor:
                continue
            coords = canvas.coords(rect_id)
            other_points.append(get_key_points(coords))
        return np.array(other_points) if other_points else np.array([]).reshape(0, 9, 2)

    def find_closest_alignment(dragged_keypoints: np.ndarray, others_tensor: np.ndarray) -> tuple:
        if others_tensor.size == 0:
            return np.array([0.0, 0.0]), (-1, -1, -1, float("inf"))

        min_dist = float("inf")
        best_delta = np.array([0.0, 0.0])
        best_info = (-1, -1, -1, min_dist)

        for i, drag_pt in enumerate(dragged_keypoints):
            for j, mon_keypoints in enumerate(others_tensor):
                for k, other_pt in enumerate(mon_keypoints):
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
            dragged_keypoints = get_key_points(canvas.coords(mon.canvas_id))

            # 2. Get (N, 9, 2) keypoints of all *other* monitors
            others_tensor = get_other_monitors_keypoints_tensor(canvas, all_mon_rects, mon)

            # 3. Find best alignment and delta
            if others_tensor.size > 0:
                delta, (drag_idx, mon_idx, point_idx, dist) = find_closest_alignment(dragged_keypoints, others_tensor)
                print(f"Snapping dragged point {drag_idx} to monitor {mon_idx}'s point {point_idx} (dist = {dist:.2f})")

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

    root.after(WAYLAND_WINDOW_CREATION_TIME, on_ready)
    draw_instructions(canvas)
    root.mainloop()


def generate_hypr_monitor_config(monitors: List[Monitor]) -> str:
    """
    Generate Hyprland monitor config lines from a list of Monitor objects.
    Now includes scale and rotation.
    Output lines like:
    monitor=DP-1,2560x1440@60,0x0,1,transform,1
    """
    lines = []
    for mon in monitors:
        name = mon.name
        width, height = mon.get_effective_resolution()  # Use scaled resolution
        x, y = map(int, mon.position)
        refresh = int(round(mon.refresh_rate))
        transform = mon.transform
        scale = mon.scale

        # Format as required by Hyprland
        line = f"monitor={name},{width}x{height}@{refresh},{x}x{y},{scale},transform,{transform}"
        lines.append(line)
    return "\n".join(lines)


def apply_hypr_monitor_config(monitors: List[Monitor]) -> None:
    """
    Generate and execute hyprctl dispatch monitor commands to set monitor layout immediately.
    Now includes scale and rotation.
    """
    for mon in monitors:
        name = mon.name
        width, height = mon.get_effective_resolution()
        x, y = map(int, mon.position)
        refresh = int(round(mon.refresh_rate))
        transform = mon.transform
        scale = mon.scale

        cmd = ["hyprctl", "dispatch", "monitor", f"{name},{width}x{height}@{refresh},{x}x{y},{scale},transform,{transform}"]

        print(f"Executing: {' '.join(cmd)}")
        subprocess.run(cmd, check=True, env=env)


if __name__ == "__main__":
    print("\n\n====Start of program=====\n\n")
    monitors: List[Monitor] = create_monitors()
    draw_monitors(monitors)
    positions: dict[str, np.ndarray] = {}
    all_pos = []
    for m in monitors:
        positions[m.name] = m.position
        print(f"position[{m.name}] = {positions[m.name]}")
        all_pos.append(positions[m.name])

    assert MAIN_MONITOR in positions, "The main monitor should be in the positions"
    dp1_pos = positions[MAIN_MONITOR].copy()
    positions_tuple: Dict[str, Tuple[int, int]] = {}
    for m in monitors:
        m.position -= dp1_pos
        positions_tuple[m.name] = tuple(m.position.tolist())

    print("======")
    print(f"positions = \n{positions_tuple}\n")
    meta_code = generate_hypr_monitor_config(monitors)
    print("\nHyprland Configuration:")
    print(meta_code)

    APPLY_RIGHT_NOW = False
    if APPLY_RIGHT_NOW:
        print("\nApplying configuration...")
        apply_hypr_monitor_config(monitors)
