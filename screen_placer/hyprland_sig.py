import os


def find_hyprland_signature():
    runtime_dir = os.environ.get("XDG_RUNTIME_DIR")
    if not runtime_dir:
        raise EnvironmentError("XDG_RUNTIME_DIR is not set")

    hypr_dir = os.path.join(runtime_dir, "hypr")
    if not os.path.exists(hypr_dir):
        raise FileNotFoundError(f"No hypr directory found at {hypr_dir}")

    # List directories inside $XDG_RUNTIME_DIR/hypr/
    candidates = [d for d in os.listdir(hypr_dir) if os.path.isdir(os.path.join(hypr_dir, d))]
    if not candidates:
        raise FileNotFoundError(f"No Hyprland instance signatures found in {hypr_dir}")

    # Option 1: Pick the most recent directory (by modification time)
    candidates = sorted(
        candidates,
        key=lambda d: os.path.getmtime(os.path.join(hypr_dir, d)),
        reverse=True,
    )

    # Return the newest signature folder name
    return candidates[0]


# Usage:
signature = find_hyprland_signature()
print("Detected Hyprland instance signature:", signature)

signature = find_hyprland_signature()
env = os.environ.copy()
env["HYPRLAND_INSTANCE_SIGNATURE"] = signature
