import tkinter as tk
from tkinter import messagebox
from tkinter import simpledialog

import subprocess,os, sys, argparse
import numpy as np
import time

def echo_to_file(message, log_file="~/QolScripts/screen_placer.log"):
    # Expand the user's home directory
    log_file = os.path.expanduser(log_file)

    # Append the message to the log file
    with open(log_file, "a") as file:
        file.write(message + "\n")

def launch_script(script_path):
    # Expand the user's home directory in case '~' is used
    script_path = os.path.expanduser(script_path)
    
    # Launch the script in the background
    process = subprocess.Popen(["bash", script_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE, start_new_session=True)

# Function to run bash commands and return output
def run_bash_command(command): 
    echo_to_file("Executing command: {}".format(command))
    print(f"Executing command: {command}")
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    echo_to_file("The command worked")
    return result.stdout.strip()


def main(main_screen, other_screen):
    echo_to_file("\n\n-----------------------------------------------------------------------------------------\n")

    # Use xrandr to connect other_screen
    run_bash_command("xrandr --output eDP-1 --pos")
    run_bash_command(f"xrandr --output {other_screen} --auto --right-of {main_screen}")

    # Get screen dimensions using xrandr and awk
    main_dimensions = run_bash_command(f"xrandr | grep -P '\\b{main_screen}\\b' | grep -P -o '[0-9]+x[0-9]+(?=\\+)'")
    other_dimensions = run_bash_command(f"xrandr | grep -P '\\b{other_screen}\\b' | grep -P -o '[0-9]+x[0-9]+(?=\\+)'")
    

    print(f"\nmain screen dimensions: {main_dimensions}")
    print(f"other screen dimensions: {other_dimensions}\n")

    # Extract width and height for main_screen and other_screen
    main_width, main_height = map(int, main_dimensions.split("+")[0].split("x"))
    other_width, other_height = map(int, other_dimensions.split("+")[0].split("x"))

    # Fixed height for the main_screen square in the GUI
    main_box_height = 200

    # Calculate scale factor for main_screen
    scale_factor = main_box_height / main_height

    # Calculate main_screen box width maintaining aspect ratio
    main_box_width = int(main_width * scale_factor)

    # Calculate other_screen box dimensions based on scale factor
    other_box_width = int(other_width * scale_factor)
    other_box_height = int(other_height * scale_factor)

    # Print dimensions for testing purposes
    echo_to_file(f"{main_screen} (width, height): ({main_width}, {main_height})")
    echo_to_file(f"{main_screen} Box (Width, Height): ({main_box_width}, {main_box_height})")
    echo_to_file(f"{other_screen} (width, height): ({other_width}, {other_height})")
    echo_to_file(f"{other_screen} Box (Width, Height): ({other_box_width}, {other_box_height})")
    print(f"{main_screen} (width, height): ({main_width}, {main_height})")
    print(f"{main_screen} Box (Width, Height): ({main_box_width}, {main_box_height})")
    print(f"{other_screen} (width, height): ({other_width}, {other_height})")
    print(f"{other_screen} Box (Width, Height): ({other_box_width}, {other_box_height})")

    # Create a Tkinter window
    window = tk.Tk()
    window.title("Screen Positioning")

    # Center main_screen box on the canvas
    canvas_width  = (main_box_width  + other_box_width  + 40) * 2  # Doubling the canvas width
    canvas_height = (main_box_height + other_box_height + 40) * 2  # Doubling the canvas height
    canvas = tk.Canvas(window, width=canvas_width, height=canvas_height)
    canvas.pack()

    # Draw a black rectangle around the canvas
    canvas.create_rectangle(5, 5, canvas_width - 5, canvas_height - 5, outline="black", width=2)

    # Initial positions for main_screen box
    main_x = (canvas_width - main_box_width) // 2
    main_y = (canvas_height - main_box_height) // 2

    # Instruction message
    canvas.create_text(canvas_width // 2, 20, text="Drag the mouse on other_screen and press Enter when it's correct. Windows+ ; to kill", fill="black")

    # Draw main_screen box
    main_frame = canvas.create_rectangle(main_x, main_y, main_x + main_box_width, main_y + main_box_height, fill="blue")
    main_label = canvas.create_text(main_x + main_box_width // 2, main_y + main_box_height // 2, text=f"{main_screen} (Currently Connected Screen)", fill="white")

    # Initial positions for other_screen box (attached to the right of main_screen)
    other_x = main_x + main_box_width
    other_y = main_y

    # Draw other_screen box
    other_frame = canvas.create_rectangle(other_x, other_y, other_x + other_box_width, other_y + other_box_height, fill="green")
    other_label = canvas.create_text(other_x + other_box_width // 2, other_y + other_box_height // 2, text=f"{other_screen} (New screen you are connecting)", fill="white")

    # Function to move the other_screen box
    def move_other(event):
        new_x = event.x - other_box_width // 2
        new_y = event.y - other_box_height // 2

        # Ensure other_screen touches one of main_screen's sides
        if new_x < main_x - other_box_width:  # Left side
            new_x = main_x - other_box_width
        elif new_x > main_x + main_box_width:  # Right side
            new_x = main_x + main_box_width
        elif new_y < main_y - other_box_height:  # Top side
            new_y = main_y - other_box_height
        elif new_y > main_y + main_box_height:  # Bottom side
            new_y = main_y + main_box_height

        # Update positions
        canvas.coords(other_frame, new_x, new_y, new_x + other_box_width, new_y + other_box_height)
        canvas.coords(other_label, new_x + other_box_width // 2, new_y + other_box_height // 2)

    # Bind mouse motion to the move_other function
    canvas.tag_bind(other_frame, "<B1-Motion>", move_other)
    canvas.tag_bind(other_label, "<B1-Motion>", move_other)

    # Function to handle Enter key press
    def on_enter(event):
        result = messagebox.askyesno("Confirmation", "Do you want to set the screens to the current location?")
        if result:
            # Get the current position of other_screen
            other_coords = canvas.coords(other_frame)
            other_x = int((other_coords[0] - main_x) / scale_factor)
            other_y = int((other_coords[1] - main_y) / scale_factor)

            points = np.array([
                [0, -1080],
                [1920, 0],
                [-1920, 0],
                [-1920, 120],
                [0, 1200]
            ])

            other_pos = np.array([other_x, other_y])

            print(f"Start {other_screen} position: ({other_x}, {other_y})")
            echo_to_file(f"Start {other_screen} position: ({other_x}, {other_y})")

            # Calculate L1 norms
            l1_norms = np.sum(np.abs(points - np.array([other_x, other_y])), axis=1)

            # Find minimum L1 norm
            min_l1_norm = np.min(l1_norms)
            print(f"min L1_norm: {min_l1_norm}")

            # Epsilon value
            eps = 60

            # Check if the minimum L1 norm is smaller than eps
            if min_l1_norm < eps:
                # Find the index of the closest point
                closest_index = np.argmin(l1_norms)

                # Snap other_x and other_y to the closest point
                other_x, other_y = points[closest_index]

                # Print the updated other_x and other_y
                print(f"Updated {other_screen} position: ({other_x}, {other_y})")
                echo_to_file(f"Updated {other_screen} position: ({other_x}, {other_y})")

            command = f"notify-send -u normal -t 5000 'Updated {other_screen} position: ({other_x}, {other_y})' &"
            run_bash_command(command)

            # Use xrandr to move other_screen
            run_bash_command("xrandr --output eDP-1 --primary --auto")
            run_bash_command(f"xrandr --output {other_screen} --auto --right-of {main_screen}")
            
            command2 = f"xrandr --output {other_screen} --pos {other_x}x{other_y}"
            run_bash_command(command2)

            # Fix the touchscreen
            command3 = f"/home/francois/QolScripts/touchscreen_fix.sh"
            run_bash_command(command3)
            
            run_bash_command(f"xrandr --output eDP-1 --primary --auto")

            time.sleep(1)
            # Add polybar
            launch_script(f"~/.config/polybar.old/polylaunch")

    # Bind Enter key press to the on_enter function
    window.bind("<Return>", on_enter)

    # Start the Tkinter event loop
    window.mainloop()
    return "END OF MAIN"


#----------------------------------------------------------------------------------------------------------------------------


def parse_screen_names():
    parser = argparse.ArgumentParser(description="Screen name parser")
    parser.add_argument("main_screen", type=str, help="Name of the main screen")
    parser.add_argument("other_screen", type=str, help="Name of the other screen")
    
    args = parser.parse_args()
    return args.main_screen, args.other_screen



def list_available_screen_names():
    # Use xrandr to get connected screens
    xrandr_output = subprocess.check_output(['xrandr']).decode('utf-8')

    # Extract screen names
    screen_names = []
    lines = xrandr_output.splitlines()
    for line in lines:
        if ' connected' in line:
            screen_name = line.split()[0]
            screen_names.append(screen_name)
    
    return screen_names


def get_screens_from_user():
    # Get screen names
    screen_names = list_available_screen_names()

    # Prompt for screen selection using a simple dialog
    prompt = f"Available screens: {', '.join(screen_names)}\n\nEnter: 'Main Screen, Other Screen'"
    user_input = simpledialog.askstring("Screen Selection", prompt)

    # Split user input into main_screen and other_screen
    if user_input:
        main_screen, other_screen = user_input.split(',')
        main_screen = main_screen.strip()
        other_screen = other_screen.strip()

        # Print selected screens
        print(f"Main Screen: {main_screen}")
        print(f"Other Screen: {other_screen}")

        return main_screen, other_screen











if __name__ == "__main__":

    if len(sys.argv) == 3:
        #main_screen, other_screen = sys.argv[1], sys.argv[2]
        #naive approach ^
    
        main_screen, other_screen = parse_screen_names()

    else:
        main_screen, other_screen = get_screens_from_user()
        

    # Call the main function with main_screen and other_screen
    main(main_screen, other_screen)
    

    print("End of the script")    







