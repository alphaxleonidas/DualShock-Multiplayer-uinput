#!/usr/bin/env python3
import evdev
import uinput
import subprocess
import re
import threading
import time
from evdev import InputDevice, categorize, ecodes

try:
    import pyudev
    PYUDEV_AVAILABLE = True
except ImportError:
    PYUDEV_AVAILABLE = False
    print("⚠ pyudev not available. Hot-plugging will not work.")
    print("Install with: pip install pyudev")

import config


class ControllerHandler:
    def __init__(self, device, player_id):
        self.device = device
        self.player_id = player_id
        self.last_values = {}
        self.is_running = True
        self.button_state = {}
        self.axis_state = {}
        self.name = f"{config.controllerName} - Player {player_id}"

        self.ui = uinput.Device(self._get_events(), name=self.name)

        print(f"[Player {player_id}] Controller registered: {device.name}")
        print(f"[Player {player_id}] Virtual device: {self.name}")

    def _get_events(self):
        return (
            uinput.ABS_X + (-32768, 32767, 0, 0),
            uinput.ABS_Y + (-32768, 32767, 0, 0),
            uinput.ABS_RX + (-32768, 32767, 0, 0),
            uinput.ABS_RY + (-32768, 32767, 0, 0),
            uinput.ABS_Z + (-32768, 32767, 0, 0),
            uinput.ABS_RZ + (-32768, 32767, 0, 0),
            uinput.ABS_HAT0X + (-1, 1, 0, 0),
            uinput.ABS_HAT0Y + (-1, 1, 0, 0),

            uinput.BTN_A,
            uinput.BTN_B,
            uinput.BTN_X,
            uinput.BTN_Y,
            uinput.BTN_TL,
            uinput.BTN_TR,
            uinput.BTN_SELECT,
            uinput.BTN_START,
            uinput.BTN_THUMBL,
            uinput.BTN_THUMBR,
            uinput.BTN_MODE,
        )

    def _apply_deadzone(self, code, val):
        if code in (ecodes.ABS_X, ecodes.ABS_Y):
            return 0 if abs(val) < config.DEADZONE_L else val
        if code in (ecodes.ABS_RX, ecodes.ABS_RY, ecodes.ABS_Z, ecodes.ABS_RZ):
            return 0 if abs(val) < config.DEADZONE_R else val
        return val

    def handle_events(self):
        keymap = {
            'BTN_TRIGGER': uinput.BTN_A,
            'BTN_THUMB': uinput.BTN_B,
            'BTN_THUMB2': uinput.BTN_X,
            'BTN_TOP': uinput.BTN_Y,
            'BTN_TOP2': uinput.BTN_TL,
            'BTN_PINKIE': uinput.BTN_TR,
            'BTN_BASE': uinput.BTN_SELECT,
            'BTN_BASE2': uinput.BTN_START,
            'BTN_BASE3': uinput.BTN_THUMBL,
            'BTN_BASE4': uinput.BTN_THUMBR,
            'BTN_BASE5': uinput.BTN_MODE,
            'BTN_BASE6': uinput.BTN_MODE,

            'BTN_SOUTH': uinput.BTN_A,
            'BTN_EAST': uinput.BTN_B,
            'BTN_WEST': uinput.BTN_X,
            'BTN_NORTH': uinput.BTN_Y,
            'BTN_TL': uinput.BTN_TL,
            'BTN_TR': uinput.BTN_TR,
            'BTN_SELECT': uinput.BTN_SELECT,
            'BTN_START': uinput.BTN_START,
            'BTN_THUMBL': uinput.BTN_THUMBL,
            'BTN_THUMBR': uinput.BTN_THUMBR,
            'BTN_MODE': uinput.BTN_MODE,
        }

        abs_map = {
            ecodes.ABS_X: uinput.ABS_X,
            ecodes.ABS_Y: uinput.ABS_Y,
            ecodes.ABS_RX: uinput.ABS_RX,
            ecodes.ABS_RY: uinput.ABS_RY,
            ecodes.ABS_Z: uinput.ABS_Z,
            ecodes.ABS_RZ: uinput.ABS_RZ,
            ecodes.ABS_HAT0X: uinput.ABS_HAT0X,
            ecodes.ABS_HAT0Y: uinput.ABS_HAT0Y,
        }

        print(f"[Player {self.player_id}] Event handler started")

        try:
            for event in self.device.read_loop():
                if not self.is_running:
                    break

                if event.type == ecodes.EV_ABS:
                    code = event.code
                    val = self._apply_deadzone(code, event.value)

                    if code in abs_map:
                        if self.last_values.get(code) != val:
                            self.ui.emit(abs_map[code], val, syn=False)
                            self.last_values[code] = val
                        self.ui.syn()

                    elif config.DEBUG:
                        print(f"[Player {self.player_id}] [ABS] Unhandled: {code} = {event.value}")

                elif event.type == ecodes.EV_KEY:
                    keyevent = categorize(event)
                    code = keyevent.keycode
                    val = 1 if keyevent.keystate == keyevent.key_down else 0

                    if isinstance(code, (list, tuple)):
                        code = code[0]

                    if config.DEBUG:
                        print(f"[Player {self.player_id}] [KEY]: {code} = {val}")

                    if code in keymap:
                        mapped = keymap[code]
                        if self.last_values.get(code) != val:
                            self.ui.emit(mapped, val)
                            self.last_values[code] = val
                    else:
                        if config.DEBUG:
                            print(f"[Player {self.player_id}] [KEY] Unmapped: {code} = {val}")

        except OSError as e:
            print(f"[Player {self.player_id}] Device disconnected: {e}")
        except Exception as e:
            print(f"[Player {self.player_id}] Error: {e}")
        finally:
            print(f"[Player {self.player_id}] Handler stopped")
            self.is_running = False


def is_generic_controller(device):
    try:
        caps = device.capabilities()
        return ecodes.EV_KEY in caps and ecodes.EV_ABS in caps
    except Exception:
        return False


def find_all_controllers():
    devices = []
    for path in evdev.list_devices():
        device = InputDevice(path)
        if config.DEBUG:
            print(f"Detected device: {device.name} ({device.path})")
        if is_generic_controller(device):
            devices.append(device)
            if config.DEBUG:
                print(f"[DEBUG] Added controller: {device.name}")
    return devices


class ControllerManager:
    def __init__(self):
        self.active_handlers = {}
        self.next_player_id = 1
        self.running = True
        self.monitor_thread = None

    def get_next_player_id(self):
        pid = self.next_player_id
        self.next_player_id += 1
        return pid

    def add_controller(self, device):
        if device.path in self.active_handlers:
            return

        player_id = self.get_next_player_id()
        print(f"\n➕ New controller detected!")
        print(f"Initializing as Player {player_id}: {device.name}\n")

        handler = ControllerHandler(device, player_id)
        thread = threading.Thread(target=handler.handle_events, daemon=False)
        thread.start()

        self.active_handlers[device.path] = {
            "handler": handler,
            "thread": thread,
            "player_id": player_id,
            "device": device,
        }

    def remove_controller(self, device_path):
        if device_path in self.active_handlers:
            info = self.active_handlers[device_path]
            pid = info["player_id"]
            handler = info["handler"]

            print(f"\n❌ Player {pid} controller disconnected\n")
            handler.is_running = False
            info["thread"].join(timeout=2)
            del self.active_handlers[device_path]

    def initial_scan(self):
        print("Searching for connected controllers...")
        devices = find_all_controllers()

        if config.MAX_CONTROLLERS and config.MAX_CONTROLLERS > 0:
            devices = devices[:config.MAX_CONTROLLERS]

        if devices:
            print(f"✓ Found {len(devices)} controller(s)\n")
            for device in devices:
                self.add_controller(device)
        else:
            print("No controllers found at startup.")

    def start_monitoring(self):
        if not PYUDEV_AVAILABLE:
            print("⚠ Hot-plugging not available (pyudev not installed)")
            return
        self.monitor_thread = threading.Thread(target=self._monitor_devices, daemon=True)
        self.monitor_thread.start()

    def _monitor_devices(self):
        try:
            context = pyudev.Context()
            monitor = pyudev.Monitor.from_netlink(context)
            monitor.filter_by("input")

            print("✓ Hot-plug monitoring enabled")

            for device in iter(monitor.poll, None):
                if not self.running:
                    break

                if device.action == "add":
                    time.sleep(0.5)
                    for path in evdev.list_devices():
                        input_dev = InputDevice(path)
                        if is_generic_controller(input_dev) and path not in self.active_handlers:
                            if config.MAX_CONTROLLERS == 0 or len(self.active_handlers) < config.MAX_CONTROLLERS:
                                self.add_controller(input_dev)
                                break

                elif device.action == "remove":
                    disconnected = []
                    for path in list(self.active_handlers.keys()):
                        try:
                            InputDevice(path)
                        except Exception:
                            disconnected.append(path)

                    for path in disconnected:
                        self.remove_controller(path)

        except Exception as e:
            print(f"Monitor error: {e}")

    def shutdown(self):
        self.running = False
        for path in list(self.active_handlers.keys()):
            self.remove_controller(path)
        print("All controllers stopped")


def main():
    manager = ControllerManager()

    print("=" * 60)
    print("Universal Controller Handler")
    print("=" * 60)

    manager.initial_scan()
    manager.start_monitoring()

    print()
    print("=" * 60)
    print(f"✓ {len(manager.active_handlers)} controller(s) active")
    print("Waiting for controller input...")
    print("Press Ctrl+C to stop all controllers")
    print("=" * 60)
    print()

    try:
        while manager.running:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n" + "=" * 60)
        print("Shutting down all players...")
        print("=" * 60)
        manager.shutdown()


if __name__ == "__main__":
    main()
