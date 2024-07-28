#!/bin/bash

notify-send "Activating monitors"


#xrandr --output eDP-1 --primary --mode 1920x1200 --rate 60

#xrandr --output HDMI-1 --mode 1920x1080 --fbmm 531x299 --rate 75 --above eDP-1

#xrandr --output DP-1 --mode 2560x1440 --fbmm 597x366 --rate 75 --right-of HDMI-1

#sleep 1

kcmshell6 kcm_kscreen 

sleep 1

/home/francois/QolScripts/touchscreen_fix.sh

/home/francois/.config/polybar.old/polylaunch bar1
/home/francois/.config/polybar.old/polylaunch bar2

