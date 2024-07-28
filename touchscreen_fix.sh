#!/bin/bash

notify-send "Fixing touchscreen"

# Map finger touch to eDP-1
finger_touch_id=$(xinput | grep "Wacom HID 52C6 Finger touch" | grep -oP 'id=\K\d+')
xinput map-to-output $finger_touch_id eDP-1

# Map stylus to eDP-1
stylus_id=$(xinput | grep "Wacom HID 52C6 Pen stylus" | grep -oP 'id=\K\d+')
xinput map-to-output $stylus_id eDP-1


$HOME/QolScripts/set_lockscreen.sh
