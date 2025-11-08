import pygame
import vgamepad as vg
import time
import threading
import gc
import importlib
import os
import sys

# ───────────────────────────── Globals ───────────────────────────── #
running = False
thread = None
pad = None
calibration = {
    0: (-1.0, 1.0),  # Left Stick X
    1: (-1.0, 1.0),  # Left Stick Y
    2: (-1.0, 1.0),  # Right Stick X
    3: (-1.0, 1.0),  # Right Stick Y
}
joystick_name = None

# ───────────────────────────── Calibration ───────────────────────────── #
def calibrate(value, axis_index):
    """Maps joystick input so that 0→0, old_min→-1, old_max→1."""
    if axis_index in calibration:
        old_min, old_max = calibration[axis_index]
        value = max(min(value, old_max), old_min)

        # Negative side
        if value < 0:
            if old_min == 0:
                return 0.0
            return (value - 0.0) / (old_min - 0.0) * -1.0
        # Positive side
        elif value > 0:
            if old_max == 0:
                return 0.0
            return (value - 0.0) / (old_max - 0.0)
        else:
            return 0.0
    return value


def to_short(val):
    """Converts -1..1 to signed short for XInput"""
    return int(val * 32767)


# ───────────────────────────── Input Mapping ───────────────────────────── #
BTN = vg.XUSB_BUTTON
mapping = {
    "axes": {"left_x": 0, "left_y": 1, "right_x": 2, "right_y": 3, "lt": 4, "rt": 5},
    "dpad_hat": 0,
    "buttons": {
        0: BTN.XUSB_GAMEPAD_A,
        1: BTN.XUSB_GAMEPAD_B,
        2: BTN.XUSB_GAMEPAD_X,
        3: BTN.XUSB_GAMEPAD_Y,
        4: BTN.XUSB_GAMEPAD_LEFT_SHOULDER,
        5: BTN.XUSB_GAMEPAD_RIGHT_SHOULDER,
        6: BTN.XUSB_GAMEPAD_BACK,
        7: BTN.XUSB_GAMEPAD_START,
        8: BTN.XUSB_GAMEPAD_LEFT_THUMB,
        9: BTN.XUSB_GAMEPAD_RIGHT_THUMB,
        10: BTN.XUSB_GAMEPAD_GUIDE,
    },
}


# ───────────────────────────── Core Mapping Loop ───────────────────────────── #
def mapping_loop(js):
    global running, pad
    print("🟢 Mapping loop started.")
    try:
        while running:
            pygame.event.pump()

            # Sticks
            lx = calibrate(js.get_axis(mapping["axes"]["left_x"]), 0)
            ly = -calibrate(js.get_axis(mapping["axes"]["left_y"]), 1)
            rx = calibrate(js.get_axis(mapping["axes"]["right_x"]), 2)
            ry = -calibrate(js.get_axis(mapping["axes"]["right_y"]), 3)

            pad.left_joystick(to_short(lx), to_short(ly))
            pad.right_joystick(to_short(rx), to_short(ry))

            # Triggers
            lt = int((js.get_axis(mapping["axes"]["lt"]) + 1) * 127)
            rt = int((js.get_axis(mapping["axes"]["rt"]) + 1) * 127)
            pad.left_trigger(lt)
            pad.right_trigger(rt)

            # D-pad
            if js.get_numhats() > 0:
                hat_x, hat_y = js.get_hat(mapping["dpad_hat"])
                pad.release_button(BTN.XUSB_GAMEPAD_DPAD_UP)
                pad.release_button(BTN.XUSB_GAMEPAD_DPAD_DOWN)
                pad.release_button(BTN.XUSB_GAMEPAD_DPAD_LEFT)
                pad.release_button(BTN.XUSB_GAMEPAD_DPAD_RIGHT)
                if hat_y == 1:
                    pad.press_button(BTN.XUSB_GAMEPAD_DPAD_UP)
                elif hat_y == -1:
                    pad.press_button(BTN.XUSB_GAMEPAD_DPAD_DOWN)
                if hat_x == 1:
                    pad.press_button(BTN.XUSB_GAMEPAD_DPAD_RIGHT)
                elif hat_x == -1:
                    pad.press_button(BTN.XUSB_GAMEPAD_DPAD_LEFT)

            # Buttons
            for physical_btn, virtual_btn in mapping["buttons"].items():
                if js.get_button(physical_btn):
                    pad.press_button(virtual_btn)
                else:
                    pad.release_button(virtual_btn)

            pad.update()
            time.sleep(0.01)
    except Exception as e:
        print(f"⚠️ Mapping loop error: {e}")
    finally:
        # Ensure pad is neutralized
        if pad:
            try:
                pad.reset()
                pad.update()
            except Exception:
                pass
        try:
            pygame.quit()
        except Exception:
            pass
        print("🟡 Mapping loop stopped and joystick reset.")


# ───────────────────────────── Public API ───────────────────────────── #
def start_mapper(selected_name, calibration_dict):
    """Start mapping: binds joystick, creates virtual pad, spawns the mapping thread."""
    global running, pad, calibration, thread, joystick_name

    if running:
        print("⚠️ Mapper already running.")
        return

    gc.collect()
    time.sleep(0.2)

    joystick_name = selected_name
    calibration = calibration_dict

    # Re-init pygame and bind joystick (retrying)
    pygame.init()
    pygame.joystick.init()

    js = None
    for attempt in range(12):
        count = pygame.joystick.get_count()
        if count == 0:
            time.sleep(0.1)
            continue
        for i in range(count):
            name = pygame.joystick.Joystick(i).get_name()
            if name == joystick_name:
                js = pygame.joystick.Joystick(i)
                js.init()
                break
        if js:
            break
        time.sleep(0.1)

    if not js:
        raise RuntimeError(f"Joystick '{joystick_name}' not found after retries")

    print(f"🎮 Joystick '{joystick_name}' ready")

    # reload vgamepad module to ensure fresh ViGEm handle
    try:
        importlib.reload(vg)
    except Exception as e:
        print(f"Warning: vgamepad reload failed: {e}")
    gc.collect()
    time.sleep(0.15)

    pad = vg.VX360Gamepad()
    running = True
    thread = threading.Thread(target=mapping_loop, args=(js,), daemon=True)
    thread.start()
    print("✅ Mapper started successfully.")


def stop_mapper(force=False):
    """
    Stop mapping and exit the entire application.
    This will clean up the virtual joystick, pygame, and then terminate the process.
    """
    global running, pad, thread

    print("🛑 Stopping mapper (and exiting app)...")
    running = False

    # Wait briefly for the mapping thread to stop
    if thread and thread.is_alive():
        thread.join(timeout=0.5)

    # Try to cleanly release the virtual joystick
    try:
        if pad:
            pad.reset()
            pad.update()
            del pad
            pad = None
            print("💨 Virtual joystick destroyed.")
    except Exception as e:
        print(f"Error releasing virtual joystick: {e}")

    # Quit pygame
    try:
        pygame.quit()
    except Exception:
        pass

    # Final gc and small delay to flush handles
    gc.collect()
    time.sleep(0.2)

    print("👋 Exiting application now.")
    os._exit(0)


def refresh_devices():
    """Return list of connected joystick names."""
    pygame.init()
    pygame.joystick.init()
    return [pygame.joystick.Joystick(i).get_name() for i in range(pygame.joystick.get_count())]


# For manual testing:
if __name__ == "__main__":
    try:
        names = refresh_devices()
        if not names:
            print("No joystick found. Plug one in and rerun.")
            sys.exit(1)
        print("Found joysticks:", names)
        start_mapper(names[0], calibration)
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        stop_mapper(force=True)
