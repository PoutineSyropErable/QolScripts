# Check for wl-clipboard
if command -v wl-copy &>/dev/null; then
	echo "wl-clipboard is installed."
else
	echo "wl-clipboard is not installed."
fi

# Check for grim
if command -v grim &>/dev/null; then
	echo "grim is installed."
else
	echo "grim is not installed."
fi

# Check for swaymsg (only if using Sway)
if command -v swaymsg &>/dev/null; then
	echo "swaymsg is installed."
else
	echo "swaymsg is not installed."
fi
