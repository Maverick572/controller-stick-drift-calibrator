import pygame
import vgamepad as vg
import time

# ───────────────────────────── Initialization ───────────────────────────── #
pygame.init()
pygame.joystick.init()

js = pygame.joystick.Joystick(0)
js.init()

pad = vg.VX360Gamepad()

print(f"Using joystick: {js.get_name()}")
print(f"Axes: {js.get_numaxes()}, Buttons: {js.get_numbuttons()}, Hats: {js.get_numhats()}")
print("Press Ctrl+C to quit.\n")

# ───────────────────────────── Calibration ───────────────────────────── #
calibration = {
    2: (-0.32, 1.0),  # Example: right-stick X damaged
}

def calibrate(value, axis_index):
    """Piecewise calibration: keeps center (0) centered, maps -0.32→-1 and 1→1."""
    if axis_index in calibration:
        old_min, old_max = calibration[axis_index]
        # Ensure within expected range
        value = max(min(value, old_max), old_min)

        # Split into two halves to keep 0 stable
        if value < 0:
            # Map [-0.32, 0] → [-1, 0]
            return (value - old_min) / (0 - old_min) * (0 - (-1)) + (-1)
        else:
            # Map [0, 1] → [0, 1] (unchanged)
            return value
    return value

def to_short(val):
    """Converts -1..1 to signed short for XInput"""
    return int(val * 32767)

# ───────────────────────────── Mapping Configuration ───────────────────────────── #
BTN = vg.XUSB_BUTTON

def map_inputs():
    """
    Central mapping function.
    Each virtual button (B0–B16) is assigned to a physical input.
    You can remap these freely as needed.
    """
    return {
        "axes": {
            "left_x": 0,    # Axis index for left stick X
            "left_y": 1,    # Axis index for left stick Y
            "right_x": 2,   # Axis index for right stick X
            "right_y": 3,   # Axis index for right stick Y
            "lt": 4,        # Left trigger
            "rt": 5         # Right trigger
        },
        "dpad_hat": 0,      # Usually Hat 0
        "buttons": {
            # Map physical button index → virtual button (B0–B16)
            0: BTN.XUSB_GAMEPAD_A,             # B0
            1: BTN.XUSB_GAMEPAD_B,             # B1
            2: BTN.XUSB_GAMEPAD_X,             # B2
            3: BTN.XUSB_GAMEPAD_Y,             # B3
            4: BTN.XUSB_GAMEPAD_LEFT_SHOULDER, # B6 = LB
            5: BTN.XUSB_GAMEPAD_RIGHT_SHOULDER,# B7 = RB
            6: BTN.XUSB_GAMEPAD_BACK,          # B4
            7: BTN.XUSB_GAMEPAD_START,         # B5
            8: BTN.XUSB_GAMEPAD_LEFT_THUMB,    # B8 = L3
            9: BTN.XUSB_GAMEPAD_RIGHT_THUMB,   # B9 = R3
            10: BTN.XUSB_GAMEPAD_GUIDE,        # B10 = Xbox / Home
            # Add more if your controller has more buttons (up to B16)
        }
    }

# Load current mapping
mapping = map_inputs()

# ───────────────────────────── Input Update Functions ───────────────────────────── #
def update_sticks():
    lx = calibrate(js.get_axis(mapping["axes"]["left_x"]), mapping["axes"]["left_x"])
    ly = -calibrate(js.get_axis(mapping["axes"]["left_y"]), mapping["axes"]["left_y"])
    rx = calibrate(js.get_axis(mapping["axes"]["right_x"]), mapping["axes"]["right_x"])
    ry = -calibrate(js.get_axis(mapping["axes"]["right_y"]), mapping["axes"]["right_y"])

    pad.left_joystick(to_short(lx), to_short(ly))
    pad.right_joystick(to_short(rx), to_short(ry))

def update_triggers():
    lt_idx = mapping["axes"]["lt"]
    rt_idx = mapping["axes"]["rt"]

    lt = int((js.get_axis(lt_idx) + 1) * 127)
    rt = int((js.get_axis(rt_idx) + 1) * 127)

    pad.left_trigger(lt)
    pad.right_trigger(rt)

def update_dpad():
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

def update_buttons():
    for physical_btn, virtual_btn in mapping["buttons"].items():
        if js.get_button(physical_btn):
            pad.press_button(virtual_btn)
        else:
            pad.release_button(virtual_btn)

# ───────────────────────────── Main Loop ───────────────────────────── #
try:
    while True:
        pygame.event.pump()

        update_sticks()
        update_triggers()
        update_dpad()
        update_buttons()

        pad.update()
        time.sleep(0.01)

except KeyboardInterrupt:
    print("\nStopped.")
    pygame.quit()
