from evdev import InputDevice

# add user to the input group to gain access to /dev/input/
# sudo usermod -a -G input <user>
keyboard_dev_dir = f"/dev/input/by-path/platform-i8042-serio-0-event-kbd"
keyboard_dev = InputDevice(keyboard_dev_dir) # your keyboard device
while(True):
    active_LEDs = [v[0] for v in keyboard_dev.leds(verbose=True)]
    if 'LED_NUML' in active_LEDs:
        print("numlock on")
    else:
        print("numlock off")