#!/bin/bash

# Toggle Redshift nightlight for X11

if pgrep -x "redshift" > /dev/null; then
    echo "Disabling Redshift..."
    pkill redshift
else
    echo "Enabling Redshift..."
    redshift -O 4500 &
fi
