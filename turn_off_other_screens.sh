xrandr --output HDMI-1 --off 
xrandr --output DP-1 --off
xrandr --output eDP-1 --primary --auto

~/.config/polybar.old/polylaunch &

~/QolScripts/touchscreen_fix.sh


$HOME/QolScripts/set_lock_screen.sh
