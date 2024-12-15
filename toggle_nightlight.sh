#!/bin/bash

if pgrep -x "gammastep" > /dev/null; then
  # gammastep -x
  pkill -9 gammastep &
  notify-send -t 1000 "Night Light" "Deactivated"
  exit 0
else
  gammastep -O 3500 &
  notify-send -t 1000 "Night Light" "Activated"
  exit 0
fi

