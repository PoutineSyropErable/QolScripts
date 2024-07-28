#!/bin/bash

# Get screen resolutions
screen1=$(xrandr | grep 'eDP-1' | awk '{print $4}')  # Adjust 'eDP-1' to your main screen
screen2=$(xrandr | grep 'HDMI-1' | awk '{print $3}') # Adjust 'HDMI-1' to your second screen

# Calculate total width and height
total_width=$((screen1_width + screen2_width))
total_height=$((screen1_height > screen2_height ? screen1_height : screen2_height))

# Position a transparent window across both screens
xdotool search --onlyvisible --class '^trans' windowmove 0 0 windowsize $total_width $total_height

# Allow clicking and dragging to position screens

# Apply the configuration using xrandr or similar tool
xrandr --output HDMI-1 --auto --right-of eDP-1  # Adjust accordingly

