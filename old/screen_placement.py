import pyautogui

def main():
    print("Move your mouse to the location where you want to place the second screen.")
    print("Press Ctrl+C to capture the current mouse position.")
    
    try:
        while True:
            x, y = pyautogui.position()
            print(f"Current mouse position: X={x}, Y={y}", end='\r')
            pyautogui.sleep(0.1)  # Adjust sleep time as needed
    except KeyboardInterrupt:
        print("\nMouse position captured.")
        print(f"Final mouse position: X={x}, Y={y}")
        # You can use x and y coordinates for further processing or screen placement logic

if __name__ == "__main__":
    main()

