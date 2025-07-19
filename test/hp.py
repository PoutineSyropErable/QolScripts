import os

print("UID:", os.getuid())
print("XDG_RUNTIME_DIR:", os.environ.get("XDG_RUNTIME_DIR"))
print("DISPLAY:", os.environ.get("DISPLAY"))
