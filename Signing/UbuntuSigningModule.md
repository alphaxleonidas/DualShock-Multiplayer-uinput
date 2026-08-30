# Signing the Module (for Ubuntu based distros)


1. Create Signing Script


```
sudo nano /usr/local/bin/sign-uinput.sh
```

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


```
sudo chmod +x /usr/local/bin/sign-uinput.sh
```

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
