Make it easier for yourself and just do this command if you have 3 screen, just do
kcmshell6 kcm_kscreen




This is scripts to connect to multiple window and keep the touchscreen and stylus working as you do so. It goes well with i3 keybinds

touchscreen-fix.sh is for mapping the touchscreen to the correct screens



Screen_input.py: Testing the prompt windows

Screen_placer.py: The master script. If you give no argument, It will open a prompt asking for the name of the display you want to use
You must input {main_screen_name}, {other_screen_name}
the space is optional (Pretty sure). Don't put a space at the start. Correctly write the name. 

Otherwise, you can use `python screen_placer.py <main_screen> <other_screen>`





As of now, it only supports adding one screen at a time. You can move the other screen, the main_screen is fixed. 

If you want to add multiple screens, You'll need to multiple usage.

I wanted it done quick, so I used lots of chatgpt to learn the syntax. However, The script works. 

Eventually, I will rewrite it manually in object oriented style, allowing multiple movable windows. 
Getting the corners sticking to work will be an annoying problem due to how the coordinates are encoded but what do you know. 

This is mostly done for myself. As using kde system settings is annoying everyime i connect a mouse. Also, I have a touchscreen and stylus and I need it mapped to the correct screen. So, This script does that for me. 

I probably won't work on it in a while as it's good enough and I wrote this in my free time. 
