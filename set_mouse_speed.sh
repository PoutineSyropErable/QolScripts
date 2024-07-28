#!/bin/bash

notify-send -u low -t 2000 "Mouse speed changed to $1"

# --------- example: "xinput list" --------------------------------------------
#⎡ Virtual core pointer                    	id=2	[master pointer  (3)]
#⎜   ↳ Virtual core XTEST pointer              	id=4	[slave  pointer  (2)]
#⎜   ↳ Wacom HID 52C6 Pen stylus               	id=16	[slave  pointer  (2)]
#⎜   ↳ Wacom HID 52C6 Finger touch             	id=17	[slave  pointer  (2)]
#⎜   ↳ ELAN06FA:00 04F3:31AD Mouse             	id=18	[slave  pointer  (2)]
#⎜   ↳ ELAN06FA:00 04F3:31AD Touchpad          	id=19	[slave  pointer  (2)]
#⎜   ↳ Wacom HID 52C6 Pen eraser               	id=23	[slave  pointer  (2)]
#⎜   ↳ Razer Razer BlackWidow Elite Keyboard   	id=8	[slave  pointer  (2)]
#⎜   ↳ Razer Razer BlackWidow Elite            	id=11	[slave  pointer  (2)]
#⎜   ↳ HP, Inc HyperX Pulsefire Haste Consumer Control	id=14	    [slave  pointer  (2)]
#⎜   ↳ HP, Inc HyperX Pulsefire Haste          	id=22	[slave  pointer  (2)]
#⎣ Virtual core keyboard                   	id=3	[master keyboard (2)]
#    ↳ Virtual core XTEST keyboard             	id=5	[slave  keyboard (3)]
#    ↳ Video Bus                               	id=6	[slave  keyboard (3)]
#    ↳ Power Button                            	id=7	[slave  keyboard (3)]
#    ↳ Ideapad extra buttons                   	id=15	[slave  keyboard (3)]
#    ↳ AT Translated Set 2 keyboard            	id=20	[slave  keyboard (3)]
#    ↳ Razer Razer BlackWidow Elite Keyboard   	id=9	[slave  keyboard (3)]
#    ↳ Razer Razer BlackWidow Elite            	id=10	[slave  keyboard (3)]
#    ↳ HP, Inc HyperX Pulsefire Haste System Control	id=12	    [slave  keyboard (3)]
#    ↳ HP, Inc HyperX Pulsefire Haste          	id=13	[slave  keyboard (3)]
#    ↳ HP, Inc HyperX Pulsefire Haste Consumer Control	id=21	    [slave  keyboard (3)]





# Mouse speed (adjust the value to your preference)
MOUSE_SPEED=$1
MOUSE_NAME2="HP, Inc HyperX Pulsefire Haste"
MOUSE_NAME="Compx 2.4G Receiver Mouse"


# Get the device ID for HP HyperX Pulsefire Haste under the virtual core pointer category
DEVICE_ID=$(xinput list | grep -i "$MOUSE_NAME" | grep -i 'pointer' | grep -vi "Consumer" |  grep -Eo 'id=[0-9]+' | grep -Eo '[0-9]+' | head -1)
DEVICE_NAME=$(xinput list --name-only $DEVICE_ID)


# Check if the device ID was found
if [ -z "$DEVICE_ID" ]; then
	echo " mouse not found or no pointer device found."
	exit 1
fi

echo $(xinput list)
notify-send -u normal -t 5000  "\n\nThe device name is: ($DEVICE_NAME) | The device ID is: ($DEVICE_ID)\n"
echo "It's speed will be set to '$MOUSE_SPEED' and modify the cordinate matrix"


# Evaluate $2+x: Evaluate to nothing if $2 is unset, and x if empty
# and something concat x if exit. 
if [ -z ${2+x} ]; then
	notify-send -u normal -t 4000 "exiting"
	read -p "Do you want to change it? (y/n): " confirm
	if  [[ $confirm != [yY] ]]; then
		echo "Ok, wrong id, exiting"
		exit 2
	fi
fi

# Set the Coordinate Transformation Matrix using the found device ID
xinput set-prop "$DEVICE_ID" "Coordinate Transformation Matrix" $MOUSE_SPEED 0 0  0 $MOUSE_SPEED 0  0 0 1

notify-send -u critical -t 5000 "Mouse speed set to $MOUSE_SPEED for device ID $DEVICE_ID"

