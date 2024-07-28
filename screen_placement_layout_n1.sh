#!/bin/bash

xrandr --output eDP-1 --primary --mode 1920x1200 --rate 60
#xrandr --output eDP-1 --primary --mode 1920x1200 --rate 60 --pos 0x1260

#xrandr --output HDMI-1 --mode 1920x1080 --fbmm 531x299 --rate 75 --pos 0x180
xrandr --output HDMI-1 --mode 1920x1080 --rate 75 --above eDP-1

#xrandr --output DP-1 --mode 2560x1440 --fbmm 597x366 --rate 75 --pos 1920x0
xrandr --output DP-1 --mode 2560x1440 --rate 75 --right-of HDMI-1

# Restart dunst to adjust notification size
#killall dunst
#dunst &


/home/francois/QolScripts/touchscreen_fix.sh
