#!/bin/bash

# Set your mount point (usually `/`)
MOUNT_POINT="/"
THRESHOLD_GB=30

# Get available space in GiB
available=$(df --output=avail -BG "$MOUNT_POINT" | tail -n1 | tr -dc '0-9')

if ((available < THRESHOLD_GB)); then
	notify-send -u critical "Low Disk Space" "Only ${available}G left on ${MOUNT_POINT}"
fi
