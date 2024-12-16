#!/bin/bash
# Reset all connected screens to default gamma and brightness

for output in $(xrandr --query | grep " connected" | awk '{print $1}'); do
    xrandr --output "$output" --gamma 1:1:1 --brightness 1
done
