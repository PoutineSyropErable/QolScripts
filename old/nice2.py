import tkinter as tk
import subprocess

def run_bash_command(command):
    result = subprocess.run(command, shell=True, check=True, stdout=subprocess.PIPE)
    return result.stdout.decode("utf-8").strip()

# Get dimensions for eDP-1
edp1_dimensions = run_bash_command("xrandr | grep 'eDP-1' | awk '{print $4}'").split("+")[0]

# Get dimensions for HDMI-1
hdmi1_dimensions = run_bash_command("xrandr | grep 'HDMI-1' | awk '{print $3}'").split("+")[0]

# Split dimensions into width and height for eDP-1
edp1_width, edp1_height = map(int, edp1_dimensions.split("x"))

# Split dimensions into width and height for HDMI-1
hdmi1_width, hdmi1_height = map(int, hdmi1_dimensions.split("x"))

print(f"eDP-1 dimensions: {edp1_width}x{edp1_height}")
print(f"HDMI-1 dimensions: {hdmi1_width}x{hdmi1_height}")

# Create a simple GUI to move squares
class ScreenPositioner(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Screen Positioner")
        
        self.canvas = tk.Canvas(self, width=800, height=600, bg="white")
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        # Create eDP-1 square (not movable)
        self.edp1_square = self.canvas.create_rectangle(50, 50, 50 + edp1_width, 50 + edp1_height, fill="green", tags="edp1")
        self.canvas.create_text(50 + edp1_width//2, 50 + edp1_height//2, text="eDP-1 (Laptop Screen)", fill="white", font=("Arial", 10, "bold"))
        
        # Create HDMI-1 square (movable)
        self.hdmi1_square = self.canvas.create_rectangle(300, 50, 300 + 100, 50 + 100, fill="red", tags="hdmi1")
        self.canvas.create_text(300 + 100//2, 50 + 100//2, text="HDMI-1 (Connected Second Screen)", fill="white", font=("Arial", 10, "bold"))
        
        self.hdmi1_offset_x = 0
        self.hdmi1_offset_y = 0
        
        # Bind events for moving hdmi1_square
        self.canvas.tag_bind("hdmi1", "<ButtonPress-1>", self.on_square_press)
        self.canvas.tag_bind("hdmi1", "<B1-Motion>", self.on_square_move)
        
    def on_square_press(self, event):
        self.hdmi1_offset_x = event.x
        self.hdmi1_offset_y = event.y
        
    def on_square_move(self, event):
        dx = event.x - self.hdmi1_offset_x
        dy = event.y - self.hdmi1_offset_y
        self.canvas.move("hdmi1", dx, dy)
        self.hdmi1_offset_x = event.x
        self.hdmi1_offset_y = event.y

app = ScreenPositioner()
app.mainloop()
