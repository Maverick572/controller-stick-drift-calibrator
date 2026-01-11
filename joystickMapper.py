import pygame
import vgamepad as vg
import time
import threading
import gc

# ───────────────────────────── Globals ───────────────────────────── #

_pad = None
_mapping_thread = None
_running = False
_js = None

# calibration format:
# axis_index: (old_min, old_center, old_max)
_calibration = {
    0: (-1.0, 0.0, 1.0),
    1: (-1.0, 0.0, 1.0),
    2: (-1.0, 0.0, 1.0),
    3: (-1.0, 0.0, 1.0),
}

# ───────────────────────────── Calibration ───────────────────────────── #

def _calibrate(value: float, axis: int) -> float:
    old_min, old_center, old_max = _calibration.get(axis, (-1.0, 0.0, 1.0))

    # clamp to calibrated range
    value = max(min(value, old_max), old_min)

    if value < old_center:
        denom = old_center - old_min
        return 0.0 if denom == 0 else (value - old_center) / denom

    if value > old_center:
        denom = old_max - old_center
        return 0.0 if denom == 0 else (value - old_center) / denom

    return 0.0


def _to_short(v: float) -> int:
    return int(max(-1.0, min(1.0, v)) * 32767)


# ───────────────────────────── Mapping Loop ───────────────────────────── #

BTN = vg.XUSB_BUTTON

_BUTTON_MAP = {
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
}


def _mapping_loop():
    """
    Background thread:
    physical joystick → virtual Xbox controller
    """
    global _running, _pad, _js

    clock = pygame.time.Clock()

    while _running:
        pygame.event.pump()

        # ───────── Sticks ───────── #
        lx = _calibrate(_js.get_axis(0), 0)
        ly = -_calibrate(_js.get_axis(1), 1)
        rx = _calibrate(_js.get_axis(2), 2)
        ry = -_calibrate(_js.get_axis(3), 3)

        _pad.left_joystick(_to_short(lx), _to_short(ly))
        _pad.right_joystick(_to_short(rx), _to_short(ry))

        # ───────── Triggers ───────── #
        if _js.get_numaxes() >= 6:
            lt = int((_js.get_axis(4) + 1.0) * 127.5)
            rt = int((_js.get_axis(5) + 1.0) * 127.5)
            _pad.left_trigger(max(0, min(255, lt)))
            _pad.right_trigger(max(0, min(255, rt)))

        # ───────── D-Pad ───────── #
        if _js.get_numhats() > 0:
            hx, hy = _js.get_hat(0)

            # clear all d-pad buttons first
            _pad.release_button(BTN.XUSB_GAMEPAD_DPAD_UP)
            _pad.release_button(BTN.XUSB_GAMEPAD_DPAD_DOWN)
            _pad.release_button(BTN.XUSB_GAMEPAD_DPAD_LEFT)
            _pad.release_button(BTN.XUSB_GAMEPAD_DPAD_RIGHT)

            if hy == 1:
                _pad.press_button(BTN.XUSB_GAMEPAD_DPAD_UP)
            elif hy == -1:
                _pad.press_button(BTN.XUSB_GAMEPAD_DPAD_DOWN)

            if hx == 1:
                _pad.press_button(BTN.XUSB_GAMEPAD_DPAD_RIGHT)
            elif hx == -1:
                _pad.press_button(BTN.XUSB_GAMEPAD_DPAD_LEFT)

        # ───────── Buttons ───────── #
        for idx, btn in _BUTTON_MAP.items():
            if idx < _js.get_numbuttons() and _js.get_button(idx):
                _pad.press_button(btn)
            else:
                _pad.release_button(btn)

        _pad.update()
        clock.tick(100)  # ~10ms loop, stable timing

    # cleanup when stopped
    _pad.reset()
    _pad.update()


# ───────────────────────────── Public API ───────────────────────────── #

def create_virtual_joystick():
    """
    Create virtual Xbox 360 controller ONCE.
    Slot handling is managed by UI.
    """
    global _pad

    if _pad:
        return

    gc.collect()
    time.sleep(0.15)  # allow HID stack to settle

    _pad = vg.VX360Gamepad()
    _pad.reset()
    _pad.update()

    print("🟢 Virtual joystick created.")


def destroy_virtual_joystick():
    """
    Destroy virtual controller cleanly.
    """
    global _pad

    if not _pad:
        return

    _pad.reset()
    _pad.update()
    _pad = None

    gc.collect()
    time.sleep(0.1)

    print("🟡 Virtual joystick destroyed.")


def start_mapping(physical_js, calibration_dict):
    """
    Start mapping physical joystick → virtual joystick.
    Virtual joystick MUST already exist.
    """
    global _running, _mapping_thread, _js, _calibration

    if _running:
        return

    if not _pad:
        raise RuntimeError("Virtual joystick not created")

    _js = physical_js
    _calibration = calibration_dict

    pygame.init()
    pygame.joystick.init()

    _running = True
    _mapping_thread = threading.Thread(
        target=_mapping_loop,
        daemon=True
    )
    _mapping_thread.start()

    print("✅ Mapping started.")


def stop_mapping():
    """
    Stop mapping but KEEP virtual joystick alive.
    """
    global _running, _mapping_thread

    if not _running:
        return

    _running = False

    if _mapping_thread:
        _mapping_thread.join(timeout=0.5)
        _mapping_thread = None

    print("🛑 Mapping stopped.")
