#!/bin/bash

WINDOW_PROPERTIES_DIR="$HOME/QolScripts/WindowPositions"
mkdir -p "$WINDOW_PROPERTIES_DIR"


WINDOW_ID=$(i3-msg -t get_tree | jq '.. | select(.focused? == true) | .id')
FLOATING_STATUS=$(i3-msg -t get_tree | jq '.. | select(.focused? == true) | .floating')

echo "$WINDOW_ID: $FLOATING_STATUS"


WINDOW_PROPERTIES="$WINDOW_PROPERTIES_DIR/WINDOW_ID.json"


if [ "$FLOATING_STATUS" == "\"auto_on\"" ] || [ "$FLOATING_STATUS" == "\"user_on\"" ]; then
	i3-msg -t get_tree | jq ".. | select(.id==$WINDOW_ID) | .rect" > $WINDOW_PROPERTIES

fi
