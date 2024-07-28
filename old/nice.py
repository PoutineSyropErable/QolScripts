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
eDP_box_height = 400

# Calculate scale factor for eDP-1
scale_factor = eDP_box_height / edp1_height

# Calculate eDP-1 box width maintaining aspect ratio
eDP_box_width = int(edp1_width * scale_factor)

# Calculate HDMI-1 box dimensions based on scale factor
HDMI_box_width = int(hdmi_width * scale_factor)
HDMI_box_height = int(hdmi_height * scale_factor)

# Create a Tkinter window
window = tk.Tk()
window.title("Screen Positioning")

# Place eDP-1 square at the center
eDP_frame = tk.Frame(window, width=eDP_box_width, height=eDP_box_height, bg="blue")
eDP_frame.grid(row=0, column=0, padx=20, pady=20)  # Adjust padding as needed

# Place HDMI-1 square
HDMI_frame = tk.Frame(window, width=HDMI_box_width, height=HDMI_box_height, bg="green")
HDMI_frame.grid(row=0, column=1, padx=20, pady=20)  # Adjust padding as needed

# Labels for eDP-1 and HDMI-1
eDP_label = tk.Label(eDP_frame, text="eDP-1 (Laptop Screen)", fg="white", bg="blue")
eDP_label.place(relx=0.5, rely=0.5, anchor="center")

HDMI_label = tk.Label(HDMI_frame, text="HDMI-1 (Connected Second Screen)", fg="white", bg="green")
HDMI_label.place(relx=0.5, rely=0.5, anchor="center")

# Start the Tkinter event loop
window.mainloop()
