```
sudo sbctl create-keys
sudo sbctl enroll-keys
```


    modules

1. Install required packages
bash
```
sudo dnf install python3 python3-pip python3-pyudev sbctl zstd
```
2. Create the signing script
bash
```
sudo nano /usr/local/bin/sign-uinput.sh
```
Paste the content below (adapted for Fedora):
bash
```
#!/bin/bash
# Sign the uinput kernel module for Secure Boot on Fedora
# Called by kernel-install (with KERNEL_VERSION as $1) or manually.

KERNEL_VERSION="$1"
if [ -z "$KERNEL_VERSION" ]; then
    KERNEL_VERSION=$(uname -r)
fi

MODBASE="/lib/modules/${KERNEL_VERSION}/kernel/drivers/input/misc/uinput.ko"
MODPATH=""

if [ -f "${MODBASE}.zst" ]; then
    MODPATH="${MODBASE}.zst"
elif [ -f "${MODBASE}.xz" ]; then
    MODPATH="${MODBASE}.xz"
elif [ -f "${MODBASE}" ]; then
    MODPATH="${MODBASE}"
else
    echo "uinput module not found for kernel $KERNEL_VERSION"
    exit 0
fi

cd /tmp || exit

# Decompress
if [[ "$MODPATH" == *.zst ]]; then
    zstd -d "$MODPATH" -o uinput.ko
elif [[ "$MODPATH" == *.xz ]]; then
    xz -d "$MODPATH" -c > uinput.ko
else
    cp "$MODPATH" uinput.ko
fi

# Check if already signed
if sbctl verify uinput.ko | grep -q "signed"; then
    echo "uinput already signed for kernel $KERNEL_VERSION"
    rm -f uinput.ko
    exit 0
fi

# Sign
sbctl sign -s uinput.ko

# Recompress and copy back
if [[ "$MODPATH" == *.zst ]]; then
    zstd -19 uinput.ko -o uinput.ko.zst
    sudo cp uinput.ko.zst "$MODPATH"
elif [[ "$MODPATH" == *.xz ]]; then
    xz -9 uinput.ko -c > uinput.ko.xz
    sudo cp uinput.ko.xz "$MODPATH"
else
    sudo cp uinput.ko "$MODPATH"
fi

echo "Signed $MODPATH"
rm -f uinput.ko uinput.ko.zst uinput.ko.xz
```
Make it executable:
bash
```
sudo chmod +x /usr/local/bin/sign-uinput.sh
```
3. Create the post‑install hook (runs after every kernel update)
bash
```
sudo mkdir -p /etc/kernel/postinst.d
sudo nano /etc/kernel/postinst.d/99-sign-uinput.sh
```
Paste:
bash
```
#!/bin/bash
# kernel-install postinst hook – automatically signs uinput for the new kernel
/usr/local/bin/sign-uinput.sh "$1"
```
Make it executable:
bash
```
sudo chmod +x /etc/kernel/postinst.d/99-sign-uinput.sh
```
    Note: Fedora’s kernel-install runs all scripts in postinst.d with the kernel version as the first argument. This hook will fire on every kernel installation or upgrade.

4. Sign the module for your current running kernel
bash
```
sudo /usr/local/bin/sign-uinput.sh
```
5. Test that uinput loads correctly
bash
```
sudo modprobe uinput
lsmod | grep uinput
```
Check device node permissions:
bash
```
ls -l /dev/uinput
```
6. Update your system (equivalent of pacman -Syu)
bash
```
sudo dnf update
```
