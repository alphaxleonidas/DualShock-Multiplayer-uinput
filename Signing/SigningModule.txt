```
sudo nano /usr/local/bin/sign-uinput.sh
```

```
#!/bin/bash
KERNEL_VER=$(pacman -Q linux-cachyos | cut -d' ' -f2 | sed 's/-cachyos//')
MODPATH="/lib/modules/${KERNEL_VER}-cachyos/kernel/drivers/input/misc/uinput.ko.zst"

if [[ -f "$MODPATH" ]]; then
    cd /tmp
    zstd -d "$MODPATH" -o uinput.ko
    sbctl sign -s uinput.ko
    zstd -19 uinput.ko -o uinput.ko.zst
    sudo cp uinput.ko.zst "$MODPATH"
    echo "Signed $MODPATH"
    rm uinput.ko uinput.ko.zst
fi
```

```
sudo chmod +x /usr/local/bin/sign-uinput.sh
```


```
sudo mkdir -p /etc/pacman.d/hooks
```

```
sudo nano /etc/pacman.d/hooks/90-uinput-sign.hook
```
```
[Trigger]
Operation = Install
Operation = Upgrade
Type = Package
Target = linux-cachyos
Target = linux-cachyos-headers

[Action]
Description = Signing uinput module for Secure Boot
When = PostTransaction
Exec = /usr/local/bin/sign-uinput.sh
```




```
sudo /usr/local/bin/sign-uinput.sh
```


Check if uinput loads
```
sudo modprobe uinput
```
```
lsmod | grep uinput
```


```
ls -l /dev/uinput
```


```
sudo pacman -Syu
```
