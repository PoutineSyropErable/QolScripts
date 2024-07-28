import tkinter as tk
import subprocess

# Function to run bash commands and return output
def run_bash_command(command):
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    return result.stdout.strip()

# Get screen dimensions using xrandr and awk
edp1_dimensions = run_bash_command("xrandr | grep 'eDP-1' | awk '{print $4}'")
hdmi_dimensions = run_bash_command("xrandr | grep 'HDMI-1' | awk '{print $3}'")

# Extract width and height for eDP-1 and HDMI-1
edp1_width, edp1_height = map(int, edp1_dimensions.split("+")[0].split("x"))
hdmi_width, hdmi_height = map(int, hdmi_dimensions.split("+")[0].split("x"))

# Fixed height for the eDP-1 square in the GUI
eDP_box_height = 250

# Calculate scale factor for eDP-1
scale_factor = eDP_box_height / edp1_height

# Calculate eDP-1 box width maintaining aspect ratio
eDP_box_width = int(edp1_width * scale_factor)

# Calculate HDMI-1 box dimensions based on scale factor
HDMI_box_width = int(hdmi_width * scale_factor)
HDMI_box_height = int(hdmi_height * scale_factor)

# Print dimensions for testing purposes
print(f"eDP-1 (width, height): ({edp1_width}, {edp1_height})")
print(f"eDP-1 Box (Width, Height): ({eDP_box_width}, {eDP_box_height})")
print(f"HDMI-1 (width, height): ({hdmi_width}, {hdmi_height})")
print(f"HDMI-1 Box (Width, Height): ({HDMI_box_width}, {HDMI_box_height})")

# Create a Tkinter window
window = tk.Tk()
window.title("Screen Positioning")

# Center eDP-1 box on the canvas
canvas_width =  (eDP_box_width  + HDMI_box_width  + 40) * 2  # Doubling the canvas width
canvas_height = (eDP_box_height + HDMI_box_height + 40) * 2  # Doubling the canvas height
canvas = tk.Canvas(window, width=canvas_width, height=canvas_height)
canvas.pack()

# Draw a black rectangle around the canvas
canvas.create_rectangle(5, 5, canvas_width - 5, canvas_height - 5, outline="black", width=2)

# Initial positions for eDP-1 box
eDP_x = (canvas_width - eDP_box_width) // 2
eDP_y = (canvas_height - eDP_box_height) // 2

# Draw eDP-1 box
eDP_frame = canvas.create_rectangle(eDP_x, eDP_y, eDP_x + eDP_box_width, eDP_y + eDP_box_height, fill="blue")
eDP_label = canvas.create_text(eDP_x + eDP_box_width // 2, eDP_y + eDP_box_height // 2, text="eDP-1 (Laptop Screen)", fill="white")

# Initial positions for HDMI-1 box (attached to the right of eDP-1)
HDMI_x = eDP_x + eDP_box_width
HDMI_y = eDP_y

# Draw HDMI-1 box
HDMI_frame = canvas.create_rectangle(HDMI_x, HDMI_y, HDMI_x + HDMI_box_width, HDMI_y + HDMI_box_height, fill="green")
HDMI_label = canvas.create_text(HDMI_x + HDMI_box_width // 2, HDMI_y + HDMI_box_height // 2, text="HDMI-1 (Connected Second Screen)", fill="white")

# Function to move the HDMI-1 box
def move_hdmi(event):
    new_x = event.x - HDMI_box_width // 2
    new_y = event.y - HDMI_box_height // 2

    # Ensure HDMI-1 touches one of eDP-1's sides
    if new_x < eDP_x - HDMI_box_width:  # Left side
        new_x = eDP_x - HDMI_box_width
    elif new_x > eDP_x + eDP_box_width:  # Right side
        new_x = eDP_x + eDP_box_width
    elif new_y < eDP_y - HDMI_box_height:  # Top side
        new_y = eDP_y - HDMI_box_height
    elif new_y > eDP_y + eDP_box_height:  # Bottom side
        new_y = eDP_y + eDP_box_height

    # Update positions
    canvas.coords(HDMI_frame, new_x, new_y, new_x + HDMI_box_width, new_y + HDMI_box_height)
    canvas.coords(HDMI_label, new_x + HDMI_box_width // 2, new_y + HDMI_box_height // 2)

# Bind mouse motion to the move_hdmi function
canvas.tag_bind(HDMI_frame, "<B1-Motion>", move_hdmi)
canvas.tag_bind(HDMI_label, "<B1-Motion>", move_hdmi)

# Start the Tkinter event loop
window.mainloop()
