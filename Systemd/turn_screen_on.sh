#!/bin/bash

notify-send "turning screens on"

# Check for session type
if [ "$XDG_SESSION_TYPE" == "wayland" ]; then
	# Assuming Wayland with Hyprland
	hyprctl dispatch dpms on
elif [ "$XDG_SESSION_TYPE" == "x11" ]; then
	# Assuming X11
	xset dpms force on
else
	echo "Unknown session type: $XDG_SESSION_TYPE"
	exit 1
fi
