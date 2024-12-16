#!/bin/bash

# Get the currently focused workspace's output (screen)
focused_screen=$(i3-msg -t get_workspaces | jq -r '.[] | select(.focused==true).output')

# Check if jq is installed
if [ -z "$focused_screen" ]; then
    echo "Error: jq is not installed or no output detected."
    exit 1
fi

# Run xrandr inversion on the focused screen
xrandr --output "$focused_screen" --gamma 1:-1:-1 --brightness 1

