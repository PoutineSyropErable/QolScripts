#!/bin/bash

# Get the currently focused workspace's output (screen)
focused_screen=$(i3-msg -t get_workspaces | jq -r '.[] | select(.focused==true).output')

# Check if jq is installed and output detected
if [ -z "$focused_screen" ]; then
    echo "Error: jq is not installed or no output detected."
    exit 1
fi

# Map i3 output names to xrandr screen names
screen_name=$(xrandr --query | grep -w "connected" | awk '{print $1}' | grep "$focused_screen")
echo $screen_name

# Check if xcalib is installed
if ! command -v xcalib > /dev/null; then
    echo "Error: xcalib is not installed."
    exit 1
fi

# Invert colors on the focused screen using xcalib
if [[ -f /tmp/xcalib_inverted ]]; then
    echo "Reverting screen colors..."
    xcalib -c
    rm /tmp/xcalib_inverted
else
    echo "Inverting colors on $screen_name..."
    xcalib -a -i
    touch /tmp/xcalib_inverted
fi

