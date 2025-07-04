#!/bin/bash

# Configuration
STATE_FILE="$HOME/.cache/nightlight_state"  # State file to store the current stage
MAX_STAGES=5                                # Maximum number of stages before reset
NIGHTLIGHT_TEMP=5500                        # Nightlight temperature

# Function to enable nightlight
enable_nightlight() {
    echo "Applying Nightlight: Stage $1"
    redshift -O $NIGHTLIGHT_TEMP
    echo "$1" > "$STATE_FILE"  # Save the current stage
}

# Function to reset nightlight
disable_nightlight() {
    echo "Resetting Nightlight..."
    redshift -x
    echo "0" > "$STATE_FILE"  # Reset stage to 0
}

# Get current stage from the state file
if [[ -f "$STATE_FILE" ]]; then
    current_stage=$(cat "$STATE_FILE")
else
    current_stage=0
fi

# Determine the next stage
if [[ "$current_stage" -ge "$MAX_STAGES" ]]; then
    disable_nightlight
else
    next_stage=$((current_stage + 1))
    enable_nightlight "$next_stage"
fi
