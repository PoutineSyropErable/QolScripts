#!/usr/bin/env python3
"""
wdisplays_to_hyprland.py
Run wdisplays, then output the resulting monitor configuration as Hyprland config lines.
Includes transform/rotation support and optional backup when changes are made.
"""

import json
import subprocess
import sys
from pathlib import Path
from datetime import datetime
import shutil
from typing import List, Dict, Any, Optional, Tuple


class WDisplaysToHyprland:
    def __init__(self) -> None:
        self.original_state: Optional[List[Dict[str, Any]]] = None
        self.new_state: Optional[List[Dict[str, Any]]] = None
        self.config_file: Path = Path.home() / ".config/hypr/hyprland.conf"
        self.backup_dir: Path = Path.home() / ".config/hypr/backups"

    def run_hyprctl(self) -> List[Dict[str, Any]]:
        """Run hyprctl command and return parsed JSON."""
        try:
            result: subprocess.CompletedProcess = subprocess.run(["hyprctl", "monitors", "-j"], capture_output=True, text=True, check=True)
            return json.loads(result.stdout)
        except subprocess.CalledProcessError as e:
            print(f"❌ Error running hyprctl: {e}")
            sys.exit(1)
        except json.JSONDecodeError as e:
            print(f"❌ Error parsing hyprctl output: {e}")
            sys.exit(1)

    def get_monitor_config(self, monitors_data: List[Dict[str, Any]]) -> List[str]:
        """Convert monitors data to Hyprland config lines with scale before transform."""
        config_lines: List[str] = []
        for monitor in monitors_data:
            # Extract monitor parameters
            name: str = monitor["name"]
            width: int = monitor["width"]
            height: int = monitor["height"]
            refresh: int = monitor["refreshRate"]
            pos_x: int = monitor["x"]
            pos_y: int = monitor["y"]

            # Optional values with defaults
            scale: float = monitor.get("scale", 1.0)
            transform: int = monitor.get("transform", 0)

            # Base config
            base_config: str = f"monitor={name},{width}x{height}@{refresh},{pos_x}x{pos_y}"

            # Always include scale, then transform if needed
            if transform != 0:
                line: str = f"{base_config},{scale},transform,{transform}"
            else:
                line: str = f"{base_config},{scale}"

            config_lines.append(line)

        return config_lines

    def print_monitor_summary(self, monitors_data: List[Dict[str, Any]], title: str) -> None:
        """Print a readable summary of monitor configuration including transform and scale."""
        print(f"\n📊 {title}")
        print("-" * 70)
        for monitor in monitors_data:
            transform: int = monitor.get("transform", 0)
            scale: float = monitor.get("scale", 1.0)

            transform_names: Dict[int, str] = {
                0: "normal",
                1: "90°",
                2: "180°",
                3: "270°",
                4: "flipped",
                5: "flipped-90°",
                6: "flipped-180°",
                7: "flipped-270°",
            }
            transform_str: str = transform_names.get(transform, f"transform_{transform}")

            scale_str: str = f"scale {scale}" if scale != 1.0 else "scale 1"

            print(
                f"  {monitor['name']}: {monitor['width']}x{monitor['height']}@{monitor['refreshRate']}Hz at ({monitor['x']}, {monitor['y']}) [{transform_str}, {scale_str}]"
            )
        print()

    def has_changes(self) -> bool:
        """Check if monitor configuration has changed."""
        if not self.original_state or not self.new_state:
            return False

        def normalize_monitors(monitors: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
            normalized: List[Dict[str, Any]] = []
            for mon in monitors:
                # Keep only the fields that matter for configuration
                normalized.append(
                    {
                        "name": mon["name"],
                        "width": mon["width"],
                        "height": mon["height"],
                        "x": mon["x"],
                        "y": mon["y"],
                        "refreshRate": mon["refreshRate"],
                        "transform": mon.get("transform", 0),
                        "scale": mon.get("scale", 1.0),
                    }
                )
            return sorted(normalized, key=lambda x: x["name"])

        orig_norm: List[Dict[str, Any]] = normalize_monitors(self.original_state)
        new_norm: List[Dict[str, Any]] = normalize_monitors(self.new_state)

        return orig_norm != new_norm

    def backup_config(self) -> Optional[Path]:
        """Create a backup of the current config file."""
        if not self.config_file.exists():
            print(f"⚠️  Config file not found: {self.config_file}")
            return None

        self.backup_dir.mkdir(parents=True, exist_ok=True)
        timestamp: str = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file: Path = self.backup_dir / f"hyprland.conf.backup.{timestamp}"

        try:
            shutil.copy2(self.config_file, backup_file)
            print(f"📂 Backup created: {backup_file}")
            return backup_file
        except Exception as e:
            print(f"❌ Error creating backup: {e}")
            return None

    def apply_config(self, config_lines: List[str]) -> bool:
        """Apply the new configuration to the config file."""
        try:
            # Read current config
            with open(self.config_file, "r") as f:
                current_config: str = f.read()

            # Remove old monitor lines
            lines: List[str] = current_config.split("\n")
            new_lines: List[str] = [line for line in lines if not line.strip().startswith("monitor=")]

            # Add new monitor lines
            new_lines.extend(config_lines)

            # Write new config
            with open(self.config_file, "w") as f:
                f.write("\n".join(new_lines))

            print(f"✅ Configuration applied to: {self.config_file}")
            return True

        except Exception as e:
            print(f"❌ Error applying configuration: {e}")
            return False

    def run_wdisplays(self) -> None:
        """Run wdisplays and wait for it to close."""
        print("🚀 Starting wdisplays...")
        print("💡 Make your display configuration changes in wdisplays:")
        print("   • Drag monitors to position them")
        print("   • Adjust resolution and refresh rate as needed")
        print("   • Set rotation/transform in wdisplays")
        print("   • Set scale in wdisplays")
        print("   • Close wdisplays when finished\n")

        try:
            # Check if wdisplays is available
            subprocess.run(["which", "wdisplays"], check=True, capture_output=True)
        except subprocess.CalledProcessError:
            print("❌ wdisplays not found. Please install it first:")
            print("   Ubuntu/Debian: sudo apt install wdisplays")
            print("   Fedora: sudo dnf install wdisplays")
            print("   Arch: yay -S wdisplays or pacman -S wdisplays")
            sys.exit(1)

        process: Optional[subprocess.Popen] = None
        try:
            process = subprocess.Popen(["wdisplays"])
            process.wait()
        except KeyboardInterrupt:
            print("\n⏹️  Interrupted by user.")
            if process and process.poll() is None:
                process.terminate()
            sys.exit(1)
        except Exception as e:
            print(f"❌ Error running wdisplays: {e}")
            sys.exit(1)

    def main(self) -> None:
        """Main execution flow."""
        print("=" * 60)
        print("🖥️  wdisplays to Hyprland Config Converter")
        print("=" * 60)

        # Get original state
        self.original_state = self.run_hyprctl()
        self.print_monitor_summary(self.original_state, "Current Monitor Configuration")

        # Run wdisplays
        self.run_wdisplays()

        # Get new state
        self.new_state = self.run_hyprctl()
        self.print_monitor_summary(self.new_state, "New Monitor Configuration")

        # Check for changes
        if not self.has_changes():
            print("ℹ️  No changes detected in monitor configuration.")
            sys.exit(0)

        # Generate and display config lines
        config_lines: List[str] = self.get_monitor_config(self.new_state)

        print("✅ Hyprland Config Lines (copy and paste into your config):")
        print("=" * 60)
        for line in config_lines:
            print(line)
        print("=" * 60)

        # Ask if user wants to apply the configuration
        print("\n💡 Configuration changes detected!")
        response: str = input("Apply this configuration to hyprland.conf? (y/N): ").strip().lower()

        if response in ("y", "yes"):
            # Create backup before applying changes
            backup_file: Optional[Path] = self.backup_config()

            if self.apply_config(config_lines):
                print("\n🎉 Configuration applied successfully!")
                print("   Run: hyprctl reload  # to apply changes immediately")
                if backup_file:
                    print(f"   Backup saved to: {backup_file}")
            else:
                print("\n❌ Failed to apply configuration.")
        else:
            print("\n📋 Configuration ready to manually copy into your hyprland.conf")
            print("   Add the lines above to your config file, then run: hyprctl reload")


def main() -> None:
    """Entry point."""
    converter: WDisplaysToHyprland = WDisplaysToHyprland()
    converter.main()


if __name__ == "__main__":
    main()
