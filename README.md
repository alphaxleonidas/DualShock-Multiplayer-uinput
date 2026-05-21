# Disclaimer

Forked from [DualShock-uinput](https://github.com/sera-ina/DualShock-uinput)

The original repo was made by ChatGPT but this fork has been modified using Copilot. Sorry if it's messy. 

This fork has been modified for multicontroller support and hotplugging. 

# Description

I wanted a tool that works systemwide for any game so I don't always have to rely on SteamInput/Bottles/Lutris. Works wired and via Bluetooth. Works for PS4 and PS5 controller.

It in general reads the raw input from the PS controllers and sends it as a virtual controller in uinput (xinput), which I needed especially in older games which don't support DirectInput at all.

~~**It only works for one active controller!**~~

**It works with multiple active controllers. Tested on two.**



## Requirements
### packages
- python3
- python3-dev
- python3-venv
- python3-pyudev (for hotplug support)
### pip
- python_uinput
- evdev
### system
- bluetoothctl
  - if desired to be able to disconnect the controller via (PS + Start) combination
### dependency installation
- for an ubuntu based distro, use:
```
sudo apt update
sudo apt install python3-dev python3-venv python3-pyudev
```
note: rest of the dependencies are not needed in my testing. might have to use ```bluez``` instead of ```bluetoothctl```.

# Installation
Download the files manually or clone repo
```
cd ~
git clone https://github.com/alphaxleonidas/DualShock-Multiplayer-uinput.git
```

Once you installed python on your system, create a virtual enviroment (for example ".venv" in your home folder)
```
python3 -m venv ~/.venv
```
Update pip
```
~/.venv/bin/pip install --upgrade pip setuptools wheel
```
When it is done, install the dependencies manually or with the requirements.txt file
```
~/.venv/bin/pip install -r ~/DualShock-Multiplayer-uinput/requirements.txt
```
or 
```
~/.venv/bin/pip install evdev==1.9.2 python_uinput==1.0.1
```
Create udev rules file
```
sudo nano /etc/udev/rules.d/99-psinput.rules
```
and add
```
KERNEL=="uinput", MODE="0660", GROUP="input"
```
Add user to input group
```
sudo usermod -aG input $USER
```
Load uinput module
```
sudo modprobe uinput
```
Reload udev rules
```
sudo udevadm control --reload-rules
sudo udevadm trigger
```


# Usage

**Steps:**
- **Connect you PS4/PS5 controller first via USB or Bluetooth**, then run the script
```
~/.venv/bin/python ~/DualShock-Multiplayer-uinput/ds4input_multiplayerv2.py
```
as the script looks for the controller directly on start else the script will just stop with an error.

# Creating an App Entry

Instead of running the command, you can create a launch script which will appear in the App Menu.
```
nano ~/.local/share/applications/ds4input_multiplayerv2.desktop
```
Add this to the file: 
```
[Desktop Entry]
Version=1.0
Name=DualShock Multiplayer uinput
Comment=Run DualShock DS4 input script with Hot plugging support
Exec=/home/<username>/.venv/bin/python /home/<username>/DualShock-Multiplayer-uinput/ds4input_multiplayerv2.py
Type=Application
Icon=input-gaming
Terminal=false
Categories=Utility;Game;
Keywords=ds4;dualshock4;controller;dualsense;sense;
```
Replace ```<username>``` with your username, so the paths becomes correct. E.g. 

```Exec=/home/randomusername/.venv/bin/python /home/randomusername/DualShock-Multiplayer-uinput/ds4input_multiplayerv2.py```

Now make this desktop entry an executeable:
```
chmod +x ~/.local/share/applications/ds4input_multiplayerv2.desktop
```
Now logout and relogin into a new session. You will see ```DualShock Multiplayer uinput``` in the appmenu.
Now connect your DualShock or DualSense and run the ```DualShock Multiplayer uinput``` from the appmenu.

# Autostart on login

```
cp ~/.local/share/applications/ds4input_multiplayerv2.desktop ~/.config/autostart/
```

# Disconnect
To disconnect from bluetooth, use (PS + Start) 

# Additional Infos
- No vibration / force feedback
- The PS button is a separate button that you can map, for example in AntiMicroX
- In the config.py file you can change the deadzone of each stick, the name of the controller and if you want to be able to use the (PS + Start) combo to disconnect the controller.
- ```ds4input_multiplayerv2.py``` is for hotplugging support.

# Issues 
- ~~If the controller is disconnected while the script is running, reconnecting will not make it work. You will have to restart the script.~~  Fixed with ds4input_multiplayerv2.py .
- After first connecting, the system automatically registers up+forward input from the controller. Which resolves after moving the Left and Right Analogue Sticks. 
- Some games may require you to operate using the controller in the start screen of the game. It's a game issue.
- The Python script needs to be closed manually using System Monitor aka Task Manager if you choose to run it without a terminal. Otherwise, closing the terminal stops it.
- The kernel module needs to be signed each time you update your kernel.

# Signing the Module (Testing)


1. Create Signing Script


`sudo nano /usr/local/bin/sign-uinput.sh`

Paste this:


```
#!/bin/bash
KERNEL_VER=$(uname -r | sed 's/-generic//')
MODPATH="/lib/modules/$KERNEL_VER/kernel/drivers/input/misc/uinput.ko"

if [[ -f "$MODPATH" ]]; then
    cd /tmp
    sbctl sign -s "$MODPATH"
    echo "Signed $MODPATH"
else
    echo "uinput.ko not found at $MODPATH"
fi
```


`sudo chmod +x /usr/local/bin/sign-uinput.sh`

2. Create APT Hook


```
sudo mkdir -p /etc/apt/triggers.d
sudo nano /etc/apt/triggers.d/uinput-sign
```

Paste this:


```
#!/bin/bash
/usr/local/bin/sign-uinput.sh
```


```
sudo chmod +x /etc/apt/triggers.d/uinput-sign
```

3. Udev Rules + Groups

```
echo 'KERNEL=="uinput", MODE="0660", GROUP="input"' | sudo tee /etc/udev/rules.d/99-uinput.rules
```

 Add user to input group
```
sudo usermod -aG input $USER
```

 Load module
```
sudo modprobe uinput
```

 Reload rules

```
sudo udevadm control --reload-rules && sudo udevadm trigger
```

4. Test


```
sudo /usr/local/bin/sign-uinput.sh
lsmod | grep uinput
ls -l /dev/uinput
```


# Debugging

```
lsusb
```

```
cat /proc/bus/input/devices
```

```
sudo apt install joystick jstest-gtk
```

```
jstest /dev/input/js0
```

now press button and see the inputs given. Use this to change the parameters in the main .py file. 
