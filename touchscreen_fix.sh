#!/bin/bash

notify-send "Fixing touchscreen"

# Map finger touch to eDP-1
finger_touch_id=$(xinput | grep "Wacom HID 52C6 Finger touch" | grep -oP 'id=\K\d+')
notify-send "finger $finger_touch_id"
xinput map-to-output $finger_touch_id eDP-1

# Map stylus to eDP-1
stylus_id=$(xinput | grep "Wacom HID 52C6 Pen stylus" | grep -oP 'id=\K\d+')
xinput map-to-output $stylus_id eDP-1
notify-send "stylus $stylus_id"


eraser_id=$(xinput | grep "Wacom HID 52C6 Pen eraser" | grep -oP 'id=\K\d+')
xinput map-to-output $eraser_id eDP-1
notify-send "eraser $eraser_id"

$HOME/QolScripts/set_lock_screen.sh
