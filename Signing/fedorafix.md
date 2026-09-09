Sometimes the module is not loaded and you have to decompress it manually.

```
xz -dc /usr/lib/modules/$(uname -r)/kernel/drivers/input/misc/uinput.ko.xz > /tmp/uinput.ko
sudo insmod /tmp/uinput.ko
```
