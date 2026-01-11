from joystickUI import UI
import sys
import os
import pygame


# ───────────────────────────── Resources ───────────────────────────── #

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


# ───────────────────────────── Pygame Init ───────────────────────────── #
# IMPORTANT:
# pygame + joystick MUST be initialized ONCE on Windows.
# Re-initializing causes devices to disappear.

pygame.init()
pygame.joystick.init()


# ───────────────────────────── Device Refresh ───────────────────────────── #

def refresh_devices():
    """
    Enumerate all joystick device names.
    pygame must already be initialized.
    """
    names = []

    # DO NOT re-init pygame here
    for i in range(pygame.joystick.get_count()):
        js = pygame.joystick.Joystick(i)
        names.append(js.get_name())

    return names


# ───────────────────────────── App Startup ───────────────────────────── #

ui = UI(on_refresh=refresh_devices)
ui.app.iconbitmap(resource_path("icon.ico"))
ui.run()
