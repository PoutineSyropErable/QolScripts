import tkinter as tk
from tkinter import simpledialog
import subprocess

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

def get_screens():
    # Get screen names
    screen_names = list_available_screen_names()

    print("screen names:", screen_names)
    # Create a Tkinter window
    window = tk.Tk()
    window.title("Select Main and Other Screens")

    # Prompt for screen selection
    prompt = f"Available screens: {', '.join(screen_names)}\n\nEnter: '{Main Screen}, {Other Screen}'"
    user_input = simpledialog.askstring("Screen Selection", prompt)

    # Split user input into main_screen and other_screen
    if user_input:
        main_screen, other_screen = user_input.split(',')
        main_screen = main_screen.strip()
        other_screen = other_screen.strip()

        # Print selected screens
        print(f"Main Screen: {main_screen}")
        print(f"Other Screen: {other_screen}")

        # Here you can store these variables or use them further in your script
        # For demonstration, let's print them
        print("Variables saved:")
        print(f"main_screen = '{main_screen}'")
        print(f"other_screen = '{other_screen}'")

    # Start the Tkinter event loop
    window.mainloop()

if __name__ == "__main__":
    get_screens()
